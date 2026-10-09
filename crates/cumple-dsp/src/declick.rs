// Ported from cathar (github.com/vbasky/cathar) crates/cathar/src/restore.rs at commit f2c2842f, MIT OR Apache-2.0, used under MIT; see crates/cumple-dsp/THIRD_PARTY.md.
//! De-click: find impulse clicks against a sliding local RMS and rebuild each one's span.
//!
//! The port of cathar's `declick_with_method`, `local_rms` and `cubic_interpolate` (restore.rs 116 to 213),
//! generic over the sample type. At `f32` it does cathar's arithmetic in cathar's order: the local RMS is a
//! running f32 sum of squares that adds and subtracts in restore.rs's sequence, the detector compares in f32,
//! and each gap goes to [`crate::inpaint::inpaint_gap`] as an f64 copy whose rebuilt samples are cast back,
//! as upstream casts them. At `f64` the same steps run in f64, which is the build cumple ships.
//!
//! Detection uses the raw input and its local RMS; the gaps are filled one after another in the output, so
//! each fill sees the gaps before it already rebuilt. A sample is a click when its magnitude exceeds
//! `threshold` times its local RMS. The window for sample `i` covers samples `i - window/2 + 1` to
//! `i + window/2` and includes `i` itself, so no ratio exceeds `sqrt(window)`; a lone non-zero sample in
//! digital silence sits exactly on that bound and fires at any threshold below it.
//!
//! As a [`Module`] the port runs over a file in blocks and gives the same result as one call over the whole
//! file, as long as each click's run, its shoulders and the AR context fit inside `CONTEXT_FRAMES`. Between
//! calls it keeps the raw samples and their local RMS behind the centre, the running sum, the place the
//! detector reached, and the rebuilt samples of a gap that runs past the centre; a gap belongs to the call
//! whose centre holds its first sample.

use num_traits::Float;

use crate::inpaint::{self, FileEnds, Fill, MAX_SOLVE};
use crate::module::{Edge, Event, Module, ParamError, Report};

/// Samples of context on each side of a block: 8,192 of AR reach for the longest gap the solve takes, 2,048
/// of gap and 8 of shoulder, rounded up.
pub const CONTEXT_FRAMES: usize = 16_384;
/// The longest detector window: the local RMS of a centre sample must not reach past the context.
pub const MAX_WINDOW: usize = CONTEXT_FRAMES;

/// How a detected click's span is rebuilt. Detection is the same for both.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum DeclickMethod {
    /// Autoregressive (Janssen, Godsill and Rayner) interpolation through `inpaint_gap`, cathar's default.
    #[default]
    Ar,
    /// A cubic Hermite curve across the span, cathar's legacy fill.
    Cubic,
}

fn from_f64<F: Float>(x: f64) -> F {
    <F as num_traits::NumCast>::from(x).expect("an f64 converts to any float type")
}

fn from_usize<F: Float>(n: usize) -> F {
    <F as num_traits::NumCast>::from(n).expect("a count converts to any float type")
}

fn to_f64<F: Float>(x: F) -> f64 {
    x.to_f64().expect("any float type converts to f64")
}

/// cathar's running sum of squares behind the local RMS (restore.rs 171 to 194), one step at a time.
#[derive(Clone, Copy, Debug)]
struct RunningRms<F> {
    sum_sq: F,
    count: usize,
}

impl<F: Float> RunningRms<F> {
    fn new() -> Self {
        RunningRms {
            sum_sq: F::zero(),
            count: 0,
        }
    }

    fn enter(&mut self, s: F) {
        self.sum_sq = self.sum_sq + s * s;
        self.count += 1;
    }

    fn leave(&mut self, s: F) {
        self.sum_sq = self.sum_sq - s * s;
        self.count -= 1;
    }

    /// The RMS of the samples in the window, floored at 1e-10. A sum that has drifted below zero gives NaN,
    /// which `max` turns into the floor, as upstream's f32::max does.
    fn rms(&self) -> F {
        (self.sum_sq / from_usize::<F>(self.count))
            .sqrt()
            .max(from_f64(1e-10))
    }
}

/// cathar's local RMS of a whole signal: for sample `i`, the RMS of samples `i - window/2 + 1` to
/// `i + window/2`, clipped to the signal, from one running sum taken in upstream's order.
pub fn local_rms<F: Float>(signal: &[F], window: usize) -> Vec<F> {
    let n = signal.len();
    let half = window / 2;
    let mut rms = vec![F::zero(); n];
    let mut acc = RunningRms::new();
    for s in signal.iter().take(half.min(n)) {
        acc.enter(*s);
    }
    for (i, r) in rms.iter_mut().enumerate() {
        if i >= half {
            acc.leave(signal[i - half]);
        }
        if i + half < n {
            acc.enter(signal[i + half]);
        }
        *r = acc.rms();
    }
    rms
}

/// Redraw `signal[start + 1..end]` as a cubic Hermite curve from `signal[start]` to `signal[end]`; a span
/// shorter than 4 is left alone.
fn cubic_interpolate<F: Float>(signal: &mut [F], start: usize, end: usize) {
    if end - start < 4 {
        return;
    }
    let y0 = signal[start];
    let y1 = signal[end];
    let len = from_usize::<F>(end - start);
    let (one, two, three) = (F::one(), from_f64::<F>(2.0), from_f64::<F>(3.0));
    for (i, s) in signal
        .iter_mut()
        .enumerate()
        .skip(start + 1)
        .take(end - start - 1)
    {
        let t = from_usize::<F>(i - start) / len;
        let t2 = t * t;
        let t3 = t2 * t;
        *s = y0 * (one - three * t2 + two * t3) + y1 * (three * t2 - two * t3);
    }
}

/// Where one call's input sits in the file.
#[derive(Clone, Copy, Debug)]
struct Span {
    /// The file sample at `input[0]`.
    lo: usize,
    /// The input's signal samples, padding left out.
    n_in: usize,
    /// The left context's length: the centre's first index in the input.
    left: usize,
    /// The first file sample after the centre.
    c_end: usize,
    /// The file's length, when the file ends in this input.
    file_len: Option<usize>,
}

/// The De-click module for one channel of one file.
///
/// Its report has one event of kind `click` per span handed to a filler: its start and length in file
/// samples, shoulders included. Its counters are `clicks` (the number of events), `linear_fallbacks` (gaps
/// longer than `MAX_SOLVE`, filled linearly) and `context_fallbacks` (gaps whose AR context would have
/// reached past a block's context, filled linearly; a caller that follows the chunk protocol never causes
/// one).
#[derive(Clone, Debug)]
pub struct Declick<F> {
    threshold: F,
    window: usize,
    method: DeclickMethod,
    iterations: u32,
    /// File samples that earlier calls' centres covered.
    done: usize,
    /// A call with `Edge::last` has run.
    finished: bool,
    /// The next file sample the detector tests.
    scan: usize,
    /// The local RMS is known for file samples below this.
    rms_end: usize,
    acc: RunningRms<F>,
    /// The file sample at index 0 of `raw` and `rms`.
    base: usize,
    raw: Vec<F>,
    rms: Vec<F>,
    work: Vec<F>,
    /// Rebuilt samples of a gap that ran past the last centre, for the start of the next one.
    carry: Vec<F>,
    /// This call's gaps as (first, end) file samples, shoulders included.
    gaps: Vec<(usize, usize)>,
    scratch: Vec<f64>,
    events: Vec<Event>,
    linear_fallbacks: usize,
    context_fallbacks: usize,
}

impl<F: Float> Declick<F> {
    /// A De-click with `threshold` in local-RMS multiples (cumple's default 5), a detector window of `window`
    /// samples (64, which cathar's CLI fixes), the fill `method`, and `iterations` of the AR refinement
    /// (cathar passes 3). Refuses a threshold at or above `sqrt(window)`, which no sample can exceed.
    pub fn new(
        threshold: f64,
        window: usize,
        method: DeclickMethod,
        iterations: u32,
    ) -> Result<Declick<F>, ParamError> {
        if !(2..=MAX_WINDOW).contains(&window) {
            return Err(ParamError(format!(
                "window must be between 2 and {MAX_WINDOW} samples, got {window}"
            )));
        }
        if !threshold.is_finite() || threshold <= 0.0 {
            return Err(ParamError(format!(
                "threshold must be a positive number of local-RMS multiples, got {threshold}"
            )));
        }
        let bound = (window as f64).sqrt();
        if threshold >= bound {
            return Err(ParamError(format!(
                "threshold must be below sqrt(window) = {bound} for a window of {window} samples: the local RMS \
                 includes the sample tested, so no sample's ratio exceeds sqrt(window) and the detector would never \
                 fire; got {threshold}"
            )));
        }
        Ok(Declick {
            threshold: from_f64(threshold),
            window,
            method,
            iterations,
            done: 0,
            finished: false,
            scan: window / 2,
            rms_end: 0,
            acc: RunningRms::new(),
            base: 0,
            raw: Vec::new(),
            rms: Vec::new(),
            work: Vec::new(),
            carry: Vec::new(),
            gaps: Vec::new(),
            scratch: Vec::new(),
            events: Vec::new(),
            linear_fallbacks: 0,
            context_fallbacks: 0,
        })
    }

    /// File samples that earlier calls' centres covered.
    pub fn done(&self) -> usize {
        self.done
    }

    /// Whether a call with `Edge::last` has run, so the instance's file is finished.
    pub fn finished(&self) -> bool {
        self.finished
    }

    /// Keep the raw samples and the local RMS from `at.lo` on, then append this input's raw samples (its
    /// left context is earlier output, so the raw samples behind the centre come from the last call).
    fn keep_history(&mut self, input: &[f64], at: Span) {
        debug_assert!(
            self.base <= at.lo && at.lo <= self.rms_end && self.rms_end <= at.lo + at.n_in
        );
        let shift = at.lo - self.base;
        let keep_rms = self.rms_end - at.lo;
        self.raw.copy_within(shift..shift + at.left, 0);
        self.raw.truncate(at.left);
        self.raw
            .extend(input[at.left..at.n_in].iter().map(|&v| from_f64::<F>(v)));
        self.rms.copy_within(shift..shift + keep_rms, 0);
        self.rms.truncate(keep_rms);
        self.base = at.lo;
    }

    /// Carry the running sum on to every sample whose window this input holds: rms[i] needs raw samples up
    /// to i + half, so a call that does not end the file stops half a window before the end of its input.
    fn extend_rms(&mut self, at: Span) {
        let half = self.window / 2;
        let limit = (at.lo + at.n_in).saturating_sub(half).max(self.rms_end);
        let limit = at.file_len.unwrap_or(limit);
        if self.rms_end == 0 {
            // The file's first call: upstream starts the sum with the first half window.
            for s in self.raw.iter().take(half.min(at.n_in)) {
                self.acc.enter(*s);
            }
        }
        for i in self.rms_end..limit {
            if i >= half {
                self.acc.leave(self.raw[i - half - at.lo]);
            }
            if at.file_len.is_none_or(|n| i + half < n) {
                self.acc.enter(self.raw[i + half - at.lo]);
            }
            self.rms.push(self.acc.rms());
        }
        self.rms_end = limit;
    }

    /// Upstream's detector loop from where the last call left it, collecting into `gaps` every gap whose
    /// first sample lies before the end of the centre. Detection reads only the raw input and its local
    /// RMS, so collecting the gaps first and filling them after, in order, is upstream's order of operations.
    fn detect(&mut self, at: Span) {
        let half = self.window / 2;
        let (raw, rms, lo, threshold) = (&self.raw, &self.rms, at.lo, self.threshold);
        let flagged = |j: usize| raw[j - lo].abs() > threshold * rms[j - lo];
        // Upstream scans while i + half < n and grows a run while end + half < n; within one call the local
        // RMS is known below `bound`.
        let bound = (at.lo + at.n_in).saturating_sub(half);
        let pad = half.clamp(2, 8);
        let mut i = self.scan;
        // Whether the detector reached i from a sample it tested and passed, rather than by a jump.
        let mut stepped = false;
        while i < bound {
            // Past the centre plus a shoulder, after a sample that passed, every later gap starts in the
            // next centre: leave them to the next call.
            if at.file_len.is_none() && stepped && i >= at.c_end + pad {
                break;
            }
            if flagged(i) {
                // Grow a contiguous run so multi-sample pops become one gap, then pad a few reliable
                // shoulders for the interpolator.
                let mut start = i;
                while start > half.max(lo) && flagged(start - 1) {
                    start -= 1;
                }
                let mut end = i + 1;
                while end < bound && flagged(end) {
                    end += 1;
                }
                // Shoulder pad: leave known samples at the edges for the solver.
                let gap_start = start.saturating_sub(pad);
                let gap_end = at.file_len.map_or(end + pad, |n| (end + pad).min(n));
                if at.file_len.is_none() && gap_start >= at.c_end {
                    break; // the next call's gap
                }
                self.gaps.push((gap_start, gap_end));
                i = end.max(i + 1) + half.saturating_sub(1);
                stepped = false;
                continue;
            }
            i += 1;
            stepped = true;
        }
        self.scan = i;
    }

    /// Fill one gap in `work` as upstream does and say whether it was handed to a filler.
    fn fill(&mut self, gap_start: usize, gap_end: usize, at: Span, edge: Edge) -> bool {
        let gap_len = gap_end.saturating_sub(gap_start);
        let (s0, s1) = (gap_start - at.lo, gap_end - at.lo);
        if gap_len >= 2 && gap_start > 0 && at.file_len.is_none_or(|n| gap_end < n) {
            match self.method {
                DeclickMethod::Ar => self.fill_ar(s0, s1, at.n_in, edge),
                DeclickMethod::Cubic => cubic_interpolate(&mut self.work, s0, s1 - 1),
            }
            true
        } else if gap_end > gap_start + 2 {
            // Edge of file or tiny hole: cubic is safe and always available.
            let last = at
                .file_len
                .map_or(gap_end - 1, |n| (gap_end - 1).min(n - 1));
            cubic_interpolate(&mut self.work, s0, last - at.lo);
            true
        } else {
            false
        }
    }

    /// Rebuild `work[s0..s1]` through `inpaint_gap` on an f64 copy of the gap and its context, and cast the
    /// gap back, as upstream copies its f32 output to f64 and back.
    fn fill_ar(&mut self, s0: usize, s1: usize, n_in: usize, edge: Edge) {
        let len = s1 - s0;
        let reach = inpaint::reach(len);
        let (w0, w1) = (s0.saturating_sub(reach), (s1 + reach).min(n_in));
        self.scratch.clear();
        self.scratch
            .extend(self.work[w0..w1].iter().map(|&v| to_f64(v)));
        let ends = FileEnds {
            left: edge.first,
            right: edge.last,
        };
        let fill = inpaint::inpaint_gap(&mut self.scratch, s0 - w0, len, self.iterations, ends);
        for (w, v) in self.work[s0..s1]
            .iter_mut()
            .zip(&self.scratch[s0 - w0..s1 - w0])
        {
            *w = from_f64(*v);
        }
        match fill {
            Fill::Ar => {}
            Fill::Linear if len > MAX_SOLVE => self.linear_fallbacks += 1,
            Fill::Linear => self.context_fallbacks += 1,
            Fill::Unchanged => unreachable!("a gap inside the input"),
        }
    }
}

impl<F: Float + Send> Module for Declick<F> {
    fn id(&self) -> &'static str {
        "declick"
    }

    fn version(&self) -> &'static str {
        crate::VERSION
    }

    fn context_frames(&self) -> usize {
        CONTEXT_FRAMES
    }

    fn latency_frames(&self) -> usize {
        0
    }

    fn process(&mut self, input: &[f64], output: &mut [f64], edge: Edge) {
        assert_eq!(input.len(), output.len(), "output must be as long as input");
        assert!(
            !self.finished,
            "one instance processes one file, and this one has had its last call"
        );
        let centre = edge.centre(input.len(), CONTEXT_FRAMES, self.done);
        let n_in = input.len() - edge.padding;
        let lo = self.done - centre.start;
        let at = Span {
            lo,
            n_in,
            left: centre.start,
            c_end: lo + centre.end,
            file_len: edge.last.then_some(lo + n_in),
        };
        output[n_in..].copy_from_slice(&input[n_in..]);
        self.keep_history(input, at);
        self.extend_rms(at);

        // The output starts as the input (earlier output on the left), with the rebuilt samples the last
        // call left past its centre written back.
        self.work.clear();
        self.work
            .extend(input[..n_in].iter().map(|&v| from_f64::<F>(v)));
        let carried = self.carry.len().min(n_in - at.left);
        self.work[at.left..at.left + carried].copy_from_slice(&self.carry[..carried]);

        self.gaps.clear();
        // Upstream: a signal no longer than the window has no interior to scan.
        if at.file_len.is_none_or(|n| n > self.window) {
            self.detect(at);
        }
        let gaps = std::mem::take(&mut self.gaps);
        let mut fill_end = at.c_end;
        for &(gap_start, gap_end) in &gaps {
            if self.fill(gap_start, gap_end, at, edge) {
                self.events.push(Event {
                    kind: "click",
                    start: gap_start,
                    len: gap_end - gap_start,
                });
                fill_end = fill_end.max(gap_end);
            }
        }
        self.gaps = gaps;

        self.carry.clear();
        if !edge.last && fill_end > at.c_end {
            self.carry
                .extend_from_slice(&self.work[at.c_end - lo..fill_end - lo]);
        }
        for (o, w) in output[..n_in].iter_mut().zip(&self.work) {
            *o = to_f64(*w);
        }
        self.done += centre.len();
        self.finished = edge.last;
    }

    fn flush(&mut self, _output: &mut [f64]) -> usize {
        0
    }

    fn report(&self) -> Report {
        Report {
            events: self.events.clone(),
            counters: vec![
                ("clicks".to_string(), self.events.len() as f64),
                ("linear_fallbacks".to_string(), self.linear_fallbacks as f64),
                (
                    "context_fallbacks".to_string(),
                    self.context_fallbacks as f64,
                ),
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::module::{Chunker, process_whole};

    fn sine(n: usize, amplitude: f64, hz: f64, rate: f64) -> Vec<f64> {
        (0..n)
            .map(|i| amplitude * (2.0 * std::f64::consts::PI * hz * i as f64 / rate).sin())
            .collect()
    }

    fn declick<F: Float>(threshold: f64, window: usize) -> Declick<F> {
        Declick::new(threshold, window, DeclickMethod::Ar, 3).expect("valid parameters")
    }

    fn whole<F: Float + Send>(m: &mut Declick<F>, x: &[f64]) -> Vec<f64> {
        let mut out = vec![0.0; x.len()];
        process_whole(m, x, &mut out);
        out
    }

    fn chunked<F: Float + Send>(m: &mut Declick<F>, x: &[f64], block: usize) -> Vec<f64> {
        let mut out = vec![0.0; x.len()];
        Chunker::new(block, CONTEXT_FRAMES).run(m, x, &mut out);
        out
    }

    fn max_error(a: &[f64], b: &[f64]) -> f64 {
        a.iter()
            .zip(b)
            .map(|(x, y)| (x - y).abs())
            .fold(0.0, f64::max)
    }

    #[test]
    fn local_rms_matches_a_direct_computation() {
        let x = [0.5, -0.25, 1.0, 0.0, -0.75, 0.125, 0.3, -0.6, 0.9, -0.1];
        // numpy: for each i, sqrt(mean(x[max(i - 1, 0) : min(i + 2, n - 1) + 1] ** 2)), window 4.
        let want = [
            0.6614378277661477,
            0.57282196186948,
            0.6373774391990981,
            0.6281172263200556,
            0.4086945681067954,
            0.5069824947668312,
            0.5647178499038259,
            0.5634713834792322,
            0.6271629240742259,
            0.6403124237432849,
        ];
        let got = local_rms(&x, 4);
        for (i, (g, w)) in got.iter().zip(want).enumerate() {
            assert!((g - w).abs() <= 1e-14 * w, "sample {i}: {g} against {w}");
        }
    }

    #[test]
    fn local_rms_in_f32_keeps_cathars_running_sum_bit_for_bit() {
        // A loud burst, then 2,000 samples near 1e-5: the f32 running sum keeps the burst's rounding
        // error, which dwarfs the quiet samples' energy. The expected bits are a numpy float32 cumsum of the
        // interleaved terms in restore.rs's order (tests/repair_helpers.py, cathar_local_rms); an f64 sum
        // gives about 4.2e-6 at every quiet sample instead.
        let burst = (0..64).map(|k: usize| {
            let v = ((k % 5) as f32 + 3.0) * 0.125;
            if k.is_multiple_of(2) { v } else { -v }
        });
        let quiet = (0..2_000).map(|j: usize| ((j * 7919) % 2001) as f32 - 1000.0);
        let quiet = quiet.map(|v| v * 2f32.powi(-27));
        let y: Vec<f32> = burst.chain(quiet).collect();
        let got = local_rms(&y, 64);
        let want: [(usize, u32); 14] = [
            (0, 0x3f235bd3),
            (31, 0x3f25370b),
            (63, 0x3eec1a07),
            (64, 0x3ee8b04a),
            (95, 0x34b00000),
            (96, 0x2edbe6ff),
            (100, 0x2edbe6ff),
            (200, 0x35b22b18),
            (500, 0x2edbe6ff),
            (1000, 0x35aa3d25),
            (1500, 0x35dc6840),
            (2000, 0x3590c902),
            (2031, 0x2edbe6ff),
            (2063, 0x2edbe6ff),
        ];
        for (i, bits) in want {
            assert_eq!(
                got[i].to_bits(),
                bits,
                "sample {i}: {} against {}",
                got[i],
                f32::from_bits(bits)
            );
        }
        let exact = local_rms(&y.iter().map(|&v| v as f64).collect::<Vec<_>>(), 64);
        assert!(
            (got[1000] as f64 / exact[1000] - 1.0).abs() > 0.5,
            "the drift this test pins is real"
        );
    }

    #[test]
    fn a_single_sample_click_at_twenty_times_the_local_rms_is_found_at_threshold_5_and_refilled() {
        let clean = sine(48_000, 0.5, 440.0, 48_000.0);
        let k = 24_011;
        let mut y = clean.clone();
        y[k] += 20.0 * local_rms(&clean, 64)[k];
        // The click raises its own window's RMS, so its ratio is about 7.4: threshold 5 fires, 10 never would.
        let ratio = y[k].abs() / local_rms(&y, 64)[k];
        assert!(7.0 < ratio && ratio < 8.0, "ratio {ratio}");
        let mut m = declick::<f64>(5.0, 64);
        let out = whole(&mut m, &y);
        let report = m.report();
        assert_eq!(
            report.events,
            vec![Event {
                kind: "click",
                start: k - 8,
                len: 17
            }]
        );
        let err = max_error(&out, &clean);
        assert!(err < 1e-3, "largest error {err:e}");
    }

    #[test]
    fn a_clean_sine_passes_through_unchanged() {
        let x = sine(48_000, 0.5, 440.0, 48_000.0);
        let mut m = declick::<f64>(5.0, 64);
        assert_eq!(whole(&mut m, &x), x);
        assert!(m.report().events.is_empty());
        let x32: Vec<f64> = x.iter().map(|&v| v as f32 as f64).collect();
        let mut m = declick::<f32>(5.0, 64);
        assert_eq!(whole(&mut m, &x32), x32);
        assert!(m.report().events.is_empty());
    }

    #[test]
    fn a_1500_sample_gap_near_a_chunk_edge_is_filled_as_in_one_call() {
        // A DC step of 1,484 samples in a quiet sine at window 4096 and threshold 1.5: every sample of the
        // step has ratio about 1.66 and the sine at most sqrt(2), so the gap is the step plus 8 samples of
        // shoulder on each side, 1,500 in all. Its AR context of 6,000 samples reaches 4,000 past the edge.
        let block = 8_192;
        for gap_start in [2 * block + 2_000, 3 * block - 2_000 - 1_500] {
            let mut x = sine(60_000, 0.01, 440.0, 48_000.0);
            for v in &mut x[gap_start + 8..gap_start + 8 + 1_484] {
                *v += 0.5;
            }
            let mut a = declick::<f64>(1.5, 4096);
            let mut b = declick::<f64>(1.5, 4096);
            let one = whole(&mut a, &x);
            let blocks = chunked(&mut b, &x, block);
            let gap = Event {
                kind: "click",
                start: gap_start,
                len: 1_500,
            };
            assert_eq!(a.report().events, vec![gap.clone()]);
            assert_eq!(b.report(), a.report());
            let err = max_error(&blocks, &one);
            assert!(
                err <= 1e-9,
                "gap at {gap_start}: largest difference {err:e}"
            );
            assert!(
                max_error(
                    &one[gap_start..gap_start + 1_500],
                    &x[gap_start..gap_start + 1_500]
                ) > 0.4
            );
        }
    }

    #[test]
    fn clicks_around_a_block_edge_are_repaired_as_in_one_call() {
        // One single-sample click near each of four block edges, at the same offset from each, for offsets
        // that put the click, its shoulders or the detector's jump across the edge.
        let block = 8_192;
        let clean: Vec<f64> = sine(60_000, 0.3, 440.0, 48_000.0)
            .iter()
            .zip(sine(60_000, 0.2, 1_250.0, 48_000.0))
            .map(|(a, b)| a + b)
            .collect();
        for offset in [-40, -31, -12, -9, -8, -3, -1, 0, 1, 3, 7, 8, 9, 12, 30, 40] {
            let mut x = clean.clone();
            for edge in 1..=4 {
                let k = (edge * block) as isize + offset;
                x[k as usize] += 3.0;
            }
            let mut a = declick::<f64>(5.0, 64);
            let mut b = declick::<f64>(5.0, 64);
            let one = whole(&mut a, &x);
            assert_eq!(a.report().events.len(), 4, "offset {offset}");
            assert_eq!(chunked(&mut b, &x, block), one, "offset {offset}");
            assert_eq!(b.report(), a.report(), "offset {offset}");
            // The f32 build carries its running sum across calls, so its blocks agree with one call too.
            let x32: Vec<f64> = x.iter().map(|&v| v as f32 as f64).collect();
            let mut a = declick::<f32>(5.0, 64);
            let mut b = declick::<f32>(5.0, 64);
            let one = whole(&mut a, &x32);
            assert_eq!(chunked(&mut b, &x32, block), one, "f32, offset {offset}");
            assert_eq!(b.report(), a.report(), "f32, offset {offset}");
        }
    }

    #[test]
    fn the_cubic_method_finds_the_same_gaps_and_draws_the_curve_across_them() {
        let mut span = [0.0, 9.0, 9.0, 9.0, 1.0];
        cubic_interpolate(&mut span, 0, 4);
        assert_eq!(span, [0.0, 0.15625, 0.5, 0.84375, 1.0]); // 3t^2 - 2t^3 at t = 1/4, 1/2, 3/4
        let mut short = [0.0, 9.0, 9.0, 1.0];
        cubic_interpolate(&mut short, 0, 3);
        assert_eq!(
            short,
            [0.0, 9.0, 9.0, 1.0],
            "a span shorter than 4 is left alone"
        );

        let clean = sine(48_000, 0.5, 440.0, 48_000.0);
        let k = 24_011;
        let mut y = clean.clone();
        y[k] += 20.0 * local_rms(&clean, 64)[k];
        let mut ar = declick::<f64>(5.0, 64);
        let mut cubic = Declick::<f64>::new(5.0, 64, DeclickMethod::Cubic, 3).unwrap();
        whole(&mut ar, &y);
        let out = whole(&mut cubic, &y);
        assert_eq!(cubic.report(), ar.report());
        assert!((out[k] - clean[k]).abs() < 0.1, "the click is still there");
        assert_eq!(out[..k - 7], y[..k - 7]);
        assert_eq!(out[k + 8..], y[k + 8..]);
    }

    #[test]
    fn clicks_at_the_file_ends_take_the_cubic_branch_in_the_first_and_last_calls() {
        // At window 16 the shoulder is the whole half window, so a click on the first sample the detector
        // tests (8) has its gap start at 0, and one on the last (n - 9) has its gap end at n.
        let n = 40_000;
        let clean = sine(n, 0.1, 440.0, 48_000.0);
        let mut y = clean.clone();
        y[8] += 1.0;
        y[n - 9] += 1.0;
        let mut a = declick::<f64>(3.0, 16);
        let mut b = declick::<f64>(3.0, 16);
        let one = whole(&mut a, &y);
        let ends = vec![
            Event {
                kind: "click",
                start: 0,
                len: 17,
            },
            Event {
                kind: "click",
                start: n - 17,
                len: 17,
            },
        ];
        assert_eq!(a.report().events, ends);
        assert!((one[8] - clean[8]).abs() < 0.1 && (one[n - 9] - clean[n - 9]).abs() < 0.1);
        assert_eq!(chunked(&mut b, &y, 8_192), one);
        assert_eq!(b.report(), a.report());
    }

    #[test]
    fn the_constructor_refuses_what_the_detector_cannot_use() {
        let err = Declick::<f64>::new(8.0, 64, DeclickMethod::Ar, 3).unwrap_err();
        assert!(err.0.contains("sqrt(window) = 8"), "{err}");
        assert!(Declick::<f64>::new(7.99, 64, DeclickMethod::Ar, 3).is_ok());
        for threshold in [0.0, -1.0, f64::NAN, f64::INFINITY] {
            assert!(Declick::<f32>::new(threshold, 64, DeclickMethod::Ar, 3).is_err());
        }
        for window in [0, 1, MAX_WINDOW + 1] {
            assert!(Declick::<f64>::new(1.0, window, DeclickMethod::Ar, 3).is_err());
        }
    }
}
