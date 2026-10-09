// Ported from cathar (github.com/vbasky/cathar) crates/cathar/src/declip.rs and crates/cathar/src/util.rs at commit f2c2842f, MIT OR Apache-2.0, used under MIT; see crates/cumple-dsp/THIRD_PARTY.md.
//! De-clip: rebuild samples flattened by hard clipping.
//!
//! The port of cathar's `declip_with_method` with its A-SPADE path (`declip_spade`, `frame_starts`,
//! `cola_divisor`, `hard_threshold_k`, `project_gamma`) and its cubic path (`declip_cubic`, `cubic_fill`), from
//! declip.rs 57 to 272, and of `hann_window` (util.rs 5 to 13), generic over the sample type. At `f32` it does
//! cathar's arithmetic in cathar's order: the window is computed in f32 with f32 `cos` and f32 pi, the FFTs come
//! from `FftPlanner::<f32>` on the pinned rustfft, and every sum runs in upstream's sequence. At `f64` the same
//! steps run in f64, which is the build cumple ships.
//!
//! A sample is clipped when its magnitude is at or above `threshold`. A-SPADE (Kitic, Bertin and Gribonval)
//! works on a Gabor frame: a symmetric Hann window of `L = 1024` samples (divided by `L - 1`) at a hop of 256,
//! with one more frame set flush with the end of the signal when its length is off the hop grid, each frame a
//! full complex 1,024-point FFT scaled by `1/sqrt(L)`. Each iteration keeps the `k` largest of every frame's
//! 1,024 complex bins, every bin tied at the cutoff included, synthesises, and projects onto the clipping
//! consistent set: an unclipped sample comes back unchanged, and a clipped one stays at or beyond the threshold
//! on its own side. `k` starts at 1 and grows by `RELAX_BY = 2` every iteration, for at most `MAX_ITER = 100`;
//! the loop stops early once the residual, summed over every bin of every frame, is at most `eps`, 1e-3 times
//! the signal's norm. The cubic method redraws each clipped run and 4 samples of shoulder on each side as a
//! cubic Hermite curve, so it moves unclipped samples and rebuilds no peak.
//!
//! The module keeps its own frame rather than the shared [`crate::stft::Stft`]. The shared one is one-sided
//! with a periodic window, and that variant of A-SPADE moves rebuilt samples by up to 0.11 and ΔSDR by up to
//! 1.3 dB on the fixture (the plan's skeptics measured it in 03b and 03c): it is another algorithm.
//!
//! As a [`Module`], A-SPADE runs over each call's whole input. The left context is the module's own earlier
//! output, whose rebuilt samples stay at or beyond the threshold, so a call sees the same clipped set as the
//! raw file. Its sparsity schedule and its stopping rule cover the call's input rather than the file, so a
//! chunked run differs from one call over the whole file; that difference is the chunking cost, measured and
//! reported. The cubic method in blocks of any size gives exactly what one call gives, as long as each run and
//! its shoulders fit in `CONTEXT_FRAMES`: between calls it keeps the place the run scan reached and the rebuilt
//! samples past the centre, which reach every later centre they fall in, and a call takes every run that starts
//! before the end of its centre plus a shoulder, so no curve reaches back into a centre already returned.

use std::ops::Range;
use std::sync::Arc;

use num_complex::Complex;
use num_traits::{Float, FloatConst};
use rustfft::{Fft, FftNum, FftPlanner};

use crate::declick::{cubic_interpolate, from_f64, from_usize, to_f64};
use crate::module::{Edge, Event, Module, ParamError, Report};

/// Samples of context on each side of a block: four A-SPADE frames.
pub const CONTEXT_FRAMES: usize = 4_096;
/// The lowest threshold the module takes, as a linear sample value; the highest is 1.0.
pub const MIN_THRESHOLD: f64 = 1e-4;
/// A-SPADE's frame length and hop.
const L: usize = 1024;
const HOP: usize = 256;
/// The bins each frame keeps, `k`, grow by this many every iteration, from 1.
const RELAX_BY: usize = 2;
const MAX_ITER: usize = 100;
/// The cubic method's shoulder: the samples redrawn on each side of a clipped run.
const SHOULDER: usize = 4;

/// How a clipped run is rebuilt. Detection is the same for both: every sample at or above the threshold.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum DeclipMethod {
    /// A-SPADE sparse reconstruction over a Gabor frame, cathar's default.
    #[default]
    Spade,
    /// A cubic Hermite curve across each clipped run and its shoulders, cathar's legacy fill.
    Cubic,
}

/// cathar's `hann_window` in `F`: symmetric, `0.5 - 0.5 cos(2 pi i / (size - 1))`, every step in `F` in
/// util.rs's order, with `F`'s own `cos` and pi. At f32 this is not the f64 window cast down, which differs in
/// the last bits.
fn hann_window<F: Float + FloatConst>(size: usize) -> Vec<F> {
    let n = from_usize::<F>(size) - F::one();
    let (half, two) = (from_f64::<F>(0.5), from_f64::<F>(2.0));
    (0..size)
        .map(|i| {
            let x = from_usize::<F>(i) / n;
            half - half * (two * F::PI() * x).cos()
        })
        .collect()
}

/// Project one sample onto the clipping consistent set: an unclipped observation comes back unchanged, and a
/// clipped one keeps the candidate only at or beyond the threshold on the observation's side.
fn project_gamma<F: Float>(cand: F, obs: F, threshold: F) -> F {
    if obs.abs() < threshold {
        obs
    } else if obs >= threshold {
        cand.max(threshold)
    } else {
        cand.min(-threshold)
    }
}

/// Frames every `hop` samples, and one more flush with the end when `n - l` is off the grid; none when `n < l`.
fn frame_starts(n: usize, l: usize, hop: usize, starts: &mut Vec<usize>) {
    starts.clear();
    if n < l {
        return;
    }
    starts.extend((0..=n - l).step_by(hop));
    if *starts.last().expect("a signal of l samples holds a frame") != n - l {
        starts.push(n - l);
    }
}

/// The overlap sum of the squared window at each of `n` samples, floored at 1e-3.
fn cola_divisor<F: Float>(n: usize, starts: &[usize], win: &[F], cola: &mut Vec<F>) {
    cola.clear();
    cola.resize(n, F::zero());
    for &s in starts {
        for (c, &w) in cola[s..s + win.len()].iter_mut().zip(win) {
            *c = *c + w * w;
        }
    }
    let floor = from_f64::<F>(1e-3);
    for c in cola.iter_mut() {
        *c = c.max(floor);
    }
}

/// Keep the `k` largest-magnitude bins of `c` and zero the rest. Every bin tied with the `k`-th largest
/// survives, so more than `k` can. The `k`-th largest squared magnitude is found by selection rather than by
/// upstream's full sort, which gives the same value; `total_cmp` orders these values, never negative and never
/// -0.0, as upstream's `partial_cmp` does, without panicking on a NaN. `mags` and `sorted` are scratch.
fn hard_threshold_k<F: Float>(
    c: &mut [Complex<F>],
    k: usize,
    mags: &mut Vec<F>,
    sorted: &mut Vec<F>,
) {
    if k >= c.len() {
        return;
    }
    mags.clear();
    mags.extend(c.iter().map(|v| v.norm_sqr()));
    sorted.clear();
    sorted.extend_from_slice(mags);
    let (_, cutoff, _) = sorted.select_nth_unstable_by(k.saturating_sub(1), |a, b| {
        b.to_f64()
            .expect("a float converts to f64")
            .total_cmp(&a.to_f64().expect("a float converts to f64"))
    });
    let cutoff = *cutoff;
    for (cj, &m) in c.iter_mut().zip(mags.iter()) {
        if m < cutoff {
            *cj = Complex::new(F::zero(), F::zero());
        }
    }
}

/// A-SPADE's transforms and buffers, planned and sized once, then reused by every call.
#[derive(Clone)]
struct Spade<F: FftNum> {
    win: Vec<F>,
    scale: F,
    fft: Arc<dyn Fft<F>>,
    ifft: Arc<dyn Fft<F>>,
    scratch: Vec<Complex<F>>,
    buf: Vec<Complex<F>>,
    /// Every frame's thresholded spectrum, frame after frame.
    z: Vec<Complex<F>>,
    /// The dual variable, laid out as `z`.
    u: Vec<Complex<F>>,
    /// The overlap-added synthesis.
    y: Vec<F>,
    cola: Vec<F>,
    starts: Vec<usize>,
    mags: Vec<F>,
    sorted: Vec<F>,
}

impl<F: Float + FloatConst + FftNum> Spade<F> {
    fn new() -> Self {
        let mut planner = FftPlanner::<F>::new();
        let fft = planner.plan_fft_forward(L);
        let ifft = planner.plan_fft_inverse(L);
        let zero = Complex::new(F::zero(), F::zero());
        let scratch_len = fft
            .get_inplace_scratch_len()
            .max(ifft.get_inplace_scratch_len());
        Spade {
            win: hann_window(L),
            scale: F::one() / from_usize::<F>(L).sqrt(),
            fft,
            ifft,
            scratch: vec![zero; scratch_len],
            buf: vec![zero; L],
            z: Vec::new(),
            u: Vec::new(),
            y: Vec::new(),
            cola: Vec::new(),
            starts: Vec::new(),
            mags: Vec::with_capacity(L),
            sorted: Vec::with_capacity(L),
        }
    }

    /// cathar's `declip_spade` of `signal` into `x`, which has its length; returns the iterations run and the
    /// frames in the layout. A signal shorter than one frame is copied unchanged, with neither.
    fn run(&mut self, signal: &[F], threshold: F, x: &mut [F]) -> (usize, usize) {
        let n = signal.len();
        x.copy_from_slice(signal);
        if n < L {
            return (0, 0);
        }
        let Spade {
            win,
            scale,
            fft,
            ifft,
            scratch,
            buf,
            z,
            u,
            y,
            cola,
            starts,
            mags,
            sorted,
        } = self;
        let scale = *scale;
        frame_starts(n, L, HOP, starts);
        let nf = starts.len();
        cola_divisor(n, starts, win, cola);
        let zero = Complex::new(F::zero(), F::zero());
        z.clear();
        z.resize(nf * L, zero);
        u.clear();
        u.resize(nf * L, zero);
        y.clear();
        y.resize(n, F::zero());

        // Upstream's `signal.iter().map(|v| v * v).sum::<f32>().sqrt()`: one running sum from the first sample.
        let mut energy = F::zero();
        for &v in signal {
            energy = energy + v * v;
        }
        let eps = from_f64::<F>(1e-3) * energy.sqrt().max(from_f64(1e-9));

        let mut k = 1usize;
        let mut iterations = 0;
        for _ in 0..MAX_ITER {
            iterations += 1;
            // z = hard_threshold_k(A x + u) and y = A*(z - u) overlap-added, one frame at a time. Upstream
            // analyses every frame before it synthesises any; the analysis reads only x and the synthesis
            // writes only y, so every value, and y's sums in frame order, come out the same.
            y.fill(F::zero());
            for ((&s, zm), um) in starts
                .iter()
                .zip(z.chunks_exact_mut(L))
                .zip(u.chunks_exact(L))
            {
                for ((zv, &xv), &w) in zm.iter_mut().zip(&x[s..s + L]).zip(win.iter()) {
                    *zv = Complex::new(xv * w * scale, F::zero());
                }
                fft.process_with_scratch(zm, scratch);
                for (zv, &uv) in zm.iter_mut().zip(um) {
                    *zv = *zv + uv;
                }
                hard_threshold_k(zm, k, mags, sorted);
                for ((b, zv), uv) in buf.iter_mut().zip(zm.iter()).zip(um) {
                    *b = zv - uv;
                }
                ifft.process_with_scratch(buf, scratch);
                for ((yv, b), &w) in y[s..s + L].iter_mut().zip(buf.iter()).zip(win.iter()) {
                    *yv = *yv + w * scale * b.re;
                }
            }
            for ((xv, (&yv, &c)), &obs) in x.iter_mut().zip(y.iter().zip(cola.iter())).zip(signal) {
                *xv = project_gamma(yv / c, obs, threshold);
            }
            // The residual A x - z over every bin of every frame, in frame order, and the dual update.
            let mut resid = F::zero();
            for ((&s, zm), um) in starts
                .iter()
                .zip(z.chunks_exact(L))
                .zip(u.chunks_exact_mut(L))
            {
                for ((b, &xv), &w) in buf.iter_mut().zip(&x[s..s + L]).zip(win.iter()) {
                    *b = Complex::new(xv * w * scale, F::zero());
                }
                fft.process_with_scratch(buf, scratch);
                for ((av, zv), uv) in buf.iter().zip(zm).zip(um.iter_mut()) {
                    let d = av - zv;
                    resid = resid + d.norm_sqr();
                    *uv = *uv + d;
                }
            }
            if resid.sqrt() <= eps {
                break;
            }
            k += RELAX_BY;
            if k >= L {
                break;
            }
        }
        (iterations, nf)
    }
}

/// The De-clip module for one channel of one file.
///
/// Its report has one event of kind `clip` per clipped run, its first sample and its length in file samples,
/// and the counters `runs` (the number of events), `longest_run`, `peak_in` and `peak_out` (the largest
/// magnitude in and out), `iterations` (A-SPADE iterations, summed over calls) and `frames` (the frames those
/// calls' layouts held, a frame in two calls' inputs counted twice).
#[derive(Clone)]
pub struct Declip<F: FftNum> {
    threshold: F,
    method: DeclipMethod,
    /// File samples that earlier calls' centres covered.
    done: usize,
    /// A call with `Edge::last` has run.
    finished: bool,
    spade: Spade<F>,
    /// This call's input, in `F`. Its centre and right context are raw samples.
    signal: Vec<F>,
    /// This call's output, in `F`.
    work: Vec<F>,
    /// The cubic method: the next file sample the run scan tests.
    scan: usize,
    /// The cubic method: rebuilt samples past the last centre, for the centres after it.
    carry: Vec<F>,
    /// A clipped run still open at the end of the last centre: its first file sample and its length so far.
    open: Option<(usize, usize)>,
    events: Vec<Event>,
    longest_run: usize,
    peak_in: f64,
    peak_out: f64,
    iterations: usize,
    frames: usize,
}

impl<F: Float + FloatConst + FftNum> Declip<F> {
    /// A De-clip at `threshold`, a linear sample value from `MIN_THRESHOLD` to 1.0 (0.95 suits a file clipped
    /// at full scale; the harness passes each file's clip level), rebuilding the runs by `method`.
    pub fn new(threshold: f64, method: DeclipMethod) -> Result<Declip<F>, ParamError> {
        if !(MIN_THRESHOLD..=1.0).contains(&threshold) {
            return Err(ParamError(format!(
                "threshold must be a sample value from {MIN_THRESHOLD} to 1.0, got {threshold}"
            )));
        }
        Ok(Declip {
            threshold: from_f64(threshold),
            method,
            done: 0,
            finished: false,
            spade: Spade::new(),
            signal: Vec::new(),
            work: Vec::new(),
            scan: 0,
            carry: Vec::new(),
            open: None,
            events: Vec::new(),
            longest_run: 0,
            peak_in: 0.0,
            peak_out: 0.0,
            iterations: 0,
            frames: 0,
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

    /// cathar's `declip_cubic` (declip.rs 162 to 182) on `work`, from where the last call's scan stopped. The
    /// input starts at file sample `lo`, its centre at input index `left` and ends before file sample `c_end`.
    fn cubic(&mut self, lo: usize, left: usize, c_end: usize, last: bool) {
        let n_in = self.signal.len();
        let end_in = lo + n_in;
        let carried = self.carry.len().min(n_in - left);
        self.work[left..left + carried].copy_from_slice(&self.carry[..carried]);
        // Carried samples that run past this centre too go on to the next call with this call's own fills.
        let mut fill_end = c_end.max(lo + left + carried);
        let threshold = self.threshold;
        let mut i = self.scan;
        while i < end_in {
            // A run from here on starts past the centre by a shoulder or more, so its curve leaves the
            // centre alone: the next call's.
            if !last && i >= c_end + SHOULDER {
                break;
            }
            if self.signal[i - lo].abs() >= threshold {
                let start = i;
                while i < end_in && self.signal[i - lo].abs() >= threshold {
                    i += 1;
                }
                // Upstream clips the run and its shoulders to the file; a call clips them to its input, the
                // same clip in one call over the whole file. In blocks it bites only on a run as long as the
                // right context.
                let end = i.min(end_in - 1);
                let clip_start = start.saturating_sub(SHOULDER).max(lo);
                let clip_end = (end + SHOULDER).min(end_in - 1);
                if clip_end > clip_start + SHOULDER {
                    cubic_interpolate(&mut self.work, clip_start - lo, clip_end - lo);
                    fill_end = fill_end.max(clip_end);
                }
            }
            i += 1;
        }
        self.scan = i;
        self.carry.clear();
        if !last && fill_end > c_end {
            self.carry
                .extend_from_slice(&self.work[c_end - lo..fill_end - lo]);
        }
    }

    /// Count the clipped runs and the peaks in the centre; a run open at its end goes on into the next call.
    fn tally(
        &mut self,
        input: &[f64],
        output: &[f64],
        centre: Range<usize>,
        lo: usize,
        last: bool,
    ) {
        for i in centre {
            self.peak_in = self.peak_in.max(input[i].abs());
            self.peak_out = self.peak_out.max(output[i].abs());
            if self.signal[i].abs() >= self.threshold {
                self.open = Some(match self.open {
                    Some((start, len)) => (start, len + 1),
                    None => (lo + i, 1),
                });
            } else if let Some((start, len)) = self.open.take() {
                self.close(start, len);
            }
        }
        if last {
            if let Some((start, len)) = self.open.take() {
                self.close(start, len);
            }
        }
    }

    fn close(&mut self, start: usize, len: usize) {
        self.events.push(Event {
            kind: "clip",
            start,
            len,
        });
        self.longest_run = self.longest_run.max(len);
    }
}

impl<F: Float + FloatConst + FftNum> Module for Declip<F> {
    fn id(&self) -> &'static str {
        "declip"
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
        output[n_in..].copy_from_slice(&input[n_in..]);
        self.signal.clear();
        self.signal
            .extend(input[..n_in].iter().map(|&v| from_f64::<F>(v)));
        self.work.clear();
        self.work.extend_from_slice(&self.signal);
        match self.method {
            DeclipMethod::Spade => {
                // Upstream returns a signal with nothing at or above the threshold as it is.
                if self.signal.iter().any(|v| v.abs() >= self.threshold) {
                    let (iterations, frames) =
                        self.spade.run(&self.signal, self.threshold, &mut self.work);
                    self.iterations += iterations;
                    self.frames += frames;
                }
            }
            DeclipMethod::Cubic => self.cubic(lo, centre.start, lo + centre.end, edge.last),
        }
        for (o, w) in output[..n_in].iter_mut().zip(&self.work) {
            *o = to_f64(*w);
        }
        let covered = centre.len();
        self.tally(input, output, centre, lo, edge.last);
        self.done += covered;
        self.finished = edge.last;
    }

    fn flush(&mut self, _output: &mut [f64]) -> usize {
        0
    }

    fn report(&self) -> Report {
        Report {
            events: self.events.clone(),
            counters: vec![
                ("runs".to_string(), self.events.len() as f64),
                ("longest_run".to_string(), self.longest_run as f64),
                ("peak_in".to_string(), self.peak_in),
                ("peak_out".to_string(), self.peak_out),
                ("iterations".to_string(), self.iterations as f64),
                ("frames".to_string(), self.frames as f64),
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::module::{Chunker, process_whole};
    use crate::stft::Window;

    fn sine(n: usize, amplitude: f64, hz: f64, rate: f64) -> Vec<f64> {
        (0..n)
            .map(|i| amplitude * (2.0 * std::f64::consts::PI * hz * i as f64 / rate).sin())
            .collect()
    }

    /// `x` hard-clipped at `threshold`, every value rounded to float32 first, so both builds read it exactly.
    fn clip(x: &[f64], threshold: f64) -> Vec<f64> {
        x.iter()
            .map(|&v| (v as f32 as f64).clamp(-threshold, threshold))
            .collect()
    }

    fn declip<F: Float + FloatConst + FftNum>(threshold: f64, method: DeclipMethod) -> Declip<F> {
        Declip::new(threshold, method).expect("valid parameters")
    }

    fn whole<F: Float + FloatConst + FftNum>(m: &mut Declip<F>, x: &[f64]) -> Vec<f64> {
        let mut out = vec![0.0; x.len()];
        process_whole(m, x, &mut out);
        out
    }

    fn chunked<F: Float + FloatConst + FftNum>(
        m: &mut Declip<F>,
        x: &[f64],
        block: usize,
    ) -> Vec<f64> {
        let mut out = vec![0.0; x.len()];
        Chunker::new(block, CONTEXT_FRAMES).run(m, x, &mut out);
        out
    }

    fn counter(report: &Report, name: &str) -> f64 {
        report
            .counters
            .iter()
            .find(|(n, _)| n == name)
            .unwrap_or_else(|| panic!("no counter {name}"))
            .1
    }

    /// Start and length of every run of samples at or above `threshold`.
    fn runs(x: &[f64], threshold: f64) -> Vec<(usize, usize)> {
        let mut out = Vec::new();
        let mut i = 0;
        while i < x.len() {
            if x[i].abs() >= threshold {
                let start = i;
                while i < x.len() && x[i].abs() >= threshold {
                    i += 1;
                }
                out.push((start, i - start));
            }
            i += 1;
        }
        out
    }

    fn events(report: &Report) -> Vec<(usize, usize)> {
        report.events.iter().map(|e| (e.start, e.len)).collect()
    }

    #[test]
    fn the_f32_window_is_cathars_float32_arithmetic_bit_for_bit() {
        // numpy, every step in float32 and in util.rs's order: n = float32(1023), x = float32(i) / n, then
        // 0.5 - 0.5 * cos(float32(2) * float32(pi) * x). numpy's float32 cos and the platform's cosf differ in
        // the last bit at some indices (55 of the 1,024 on the Mac this was written on), so the pinned indices
        // are ones where numpy's float32 cos, a correctly rounded cosf and that Mac's cosf agree. Each also has
        // its exact cosine at least 0.116 ULP from an f32 rounding midpoint, so a cosf within glibc's
        // documented 0.56 ULP rounds it the same way on every runner. Indices 5, 10, 800 and 1022, at 0.006 to
        // 0.063 ULP from one, are left out.
        let want: [(usize, u32); 13] = [
            (0, 0x0000_0000),
            (2, 0x381e_4000),
            (3, 0x38b2_0000),
            (50, 0x3cbf_a130),
            (100, 0x3dbb_25a0),
            (300, 0x3f22_5c74),
            (600, 0x3f6d_8d3f),
            (700, 0x3f33_610c),
            (767, 0x3f00_3250),
            (900, 0x3e0b_48fc),
            (1000, 0x3ba3_3400),
            (1020, 0x38b2_0000),
            (1023, 0x0000_0000),
        ];
        let w = hann_window::<f32>(L);
        for (i, bits) in want {
            assert_eq!(
                w[i].to_bits(),
                bits,
                "index {i}: {} against {}",
                w[i],
                f32::from_bits(bits)
            );
        }
        // The obvious generic code, the window in f64 cast to f32, differs at every pinned index but the ends.
        let cast: Vec<f32> = Window::HannSymmetric
            .coefficients(L)
            .iter()
            .map(|&v| v as f32)
            .collect();
        for &(i, bits) in &want[1..want.len() - 1] {
            assert_ne!(cast[i].to_bits(), bits, "index {i}: the cast agrees here");
        }
        // In f64 it is the shared symmetric Hann, bit for bit.
        assert_eq!(hann_window::<f64>(L), Window::HannSymmetric.coefficients(L));
    }

    #[test]
    fn the_f32_constants_are_cathars_f32_literals() {
        // cathar writes these as f32 literals; from_f64 must not round them a second time.
        assert_eq!(from_f64::<f32>(1e-3), 1e-3f32);
        assert_eq!(from_f64::<f32>(1e-9), 1e-9f32);
        assert_eq!(Spade::<f32>::new().scale, 1.0 / (L as f32).sqrt());
    }

    #[test]
    fn frames_step_by_the_hop_and_a_flush_frame_ends_a_length_off_the_grid() {
        let mut starts = Vec::new();
        frame_starts(L - 1, L, HOP, &mut starts);
        assert!(starts.is_empty());
        frame_starts(L, L, HOP, &mut starts);
        assert_eq!(starts, [0]);
        frame_starts(L + 2 * HOP, L, HOP, &mut starts);
        assert_eq!(starts, [0, 256, 512]);
        frame_starts(L + 300, L, HOP, &mut starts);
        assert_eq!(starts, [0, 256, 300]);
    }

    #[test]
    fn hard_threshold_k_keeps_the_k_largest_bins_and_every_tie_at_the_cutoff() {
        // Squared magnitudes 25, 9, 9, 16, 1, 9, 0, 4: exact in f32, with three bins tied at 9.
        let c = |re: f32, im: f32| Complex::new(re, im);
        let spectrum = [
            c(3.0, 4.0),
            c(3.0, 0.0),
            c(0.0, -3.0),
            c(4.0, 0.0),
            c(1.0, 0.0),
            c(-3.0, 0.0),
            c(0.0, 0.0),
            c(0.0, 2.0),
        ];
        let (mut mags, mut sorted) = (Vec::new(), Vec::new());
        for (k, kept) in [
            (1, vec![0]),
            (2, vec![0, 3]),
            (3, vec![0, 1, 2, 3, 5]),
            (4, vec![0, 1, 2, 3, 5]),
            (5, vec![0, 1, 2, 3, 5]),
            (6, vec![0, 1, 2, 3, 5, 7]),
            (8, vec![0, 1, 2, 3, 4, 5, 6, 7]),
        ] {
            let mut z = spectrum;
            hard_threshold_k(&mut z, k, &mut mags, &mut sorted);
            for (j, (got, was)) in z.iter().zip(&spectrum).enumerate() {
                let want = if kept.contains(&j) { *was } else { c(0.0, 0.0) };
                assert_eq!(*got, want, "k {k}, bin {j}");
            }
        }
    }

    /// A 440 Hz sine at 0.5, clipped 4.1 dB under its peak, through one build: the peak comes back within
    /// 1 dB (read away from the ends, which fewer frames cover), and no unclipped sample moves.
    fn recovers_the_sine<F: Float + FloatConst + FftNum>(label: &str) {
        let threshold = 0.3125;
        let y = clip(&sine(4_096, 0.5, 440.0, 48_000.0), threshold);
        let clipped = runs(&y, threshold);
        assert!(clipped.len() > 10);
        let mut m = declip::<F>(threshold, DeclipMethod::Spade);
        let out = whole(&mut m, &y);
        let peak = out[L..out.len() - L]
            .iter()
            .fold(0.0f64, |a, v| a.max(v.abs()));
        let error = 20.0 * (peak / 0.5).log10();
        assert!(error.abs() < 1.0, "{label}: peak {peak}, {error:+.2} dB");
        for (i, (o, v)) in out.iter().zip(&y).enumerate() {
            if v.abs() < threshold {
                assert_eq!(o, v, "{label}: unclipped sample {i} moved");
            } else {
                assert!(
                    o.abs() >= threshold,
                    "{label}: clipped sample {i} fell inside"
                );
            }
        }
        let report = m.report();
        assert_eq!(events(&report), clipped, "{label}");
        assert!(counter(&report, "iterations") >= 1.0, "{label}");
        // (4096 - 1024) / 256 + 1 frames, on the hop grid, so no flush frame
        assert_eq!(counter(&report, "frames"), 13.0, "{label}");
    }

    #[test]
    fn a_clipped_440_hz_sine_at_half_scale_recovers_its_peak_within_1_db() {
        recovers_the_sine::<f64>("f64");
        recovers_the_sine::<f32>("f32");
    }

    #[test]
    fn a_signal_with_nothing_at_the_threshold_passes_through_untouched() {
        let x = sine(4_096, 0.5, 440.0, 48_000.0);
        for method in [DeclipMethod::Spade, DeclipMethod::Cubic] {
            let mut m = declip::<f64>(0.6, method);
            assert_eq!(whole(&mut m, &x), x, "{method:?}");
            let report = m.report();
            assert!(report.events.is_empty(), "{method:?}");
            assert_eq!(counter(&report, "iterations"), 0.0, "{method:?}");
            assert_eq!(counter(&report, "frames"), 0.0, "{method:?}");
        }
    }

    #[test]
    fn a_chunk_shorter_than_one_frame_passes_through_untouched() {
        let y = clip(&sine(L - 1, 0.5, 440.0, 48_000.0), 0.3125);
        let mut m = declip::<f64>(0.3125, DeclipMethod::Spade);
        assert_eq!(whole(&mut m, &y), y);
        let report = m.report();
        assert_eq!(events(&report), runs(&y, 0.3125));
        assert_eq!(counter(&report, "iterations"), 0.0);
        // The cubic fill has no frame, and cathar runs it at any length.
        let out = whole(&mut declip::<f64>(0.3125, DeclipMethod::Cubic), &y);
        assert_ne!(out, y);
    }

    #[test]
    fn the_cubic_fill_redraws_each_run_and_four_samples_of_shoulder_on_each_side() {
        // A ramp under 0.5 with a 3-sample plateau at 10 to 12: the curve runs from sample 6 to sample 17.
        let mut y: Vec<f64> = (0..40).map(|i| i as f64 * 0.01).collect();
        for v in &mut y[10..13] {
            *v = 0.5;
        }
        let mut m = declip::<f64>(0.5, DeclipMethod::Cubic);
        let out = whole(&mut m, &y);
        assert_eq!(out[..7], y[..7]);
        assert_eq!(out[17..], y[17..]);
        for (i, v) in out.iter().enumerate().take(17).skip(7) {
            assert!(0.06 < *v && *v < 0.17, "sample {i}: {v}");
        }
        assert_eq!(events(&m.report()), [(10, 3)]);
    }

    /// Chunked at `block`, both builds give what one call gives, report included.
    fn assert_cubic_blocks_match_one_call(x: &[f64], threshold: f64, block: usize, label: &str) {
        let mut a = declip::<f64>(threshold, DeclipMethod::Cubic);
        let mut b = declip::<f64>(threshold, DeclipMethod::Cubic);
        let one = whole(&mut a, x);
        assert_ne!(one, x, "{label}: nothing was filled");
        assert_eq!(chunked(&mut b, x, block), one, "{label}");
        assert_eq!(b.report(), a.report(), "{label}");
        let mut a = declip::<f32>(threshold, DeclipMethod::Cubic);
        let mut b = declip::<f32>(threshold, DeclipMethod::Cubic);
        let one = whole(&mut a, x);
        assert_eq!(chunked(&mut b, x, block), one, "f32, {label}");
        assert_eq!(b.report(), a.report(), "f32, {label}");
    }

    /// A 0.3 sine with plateaus at 0.5 written in: `(start, length, sign)` each.
    fn plateaus(n: usize, at: &[(usize, usize, f64)]) -> Vec<f64> {
        let mut x = sine(n, 0.3, 440.0, 48_000.0);
        for &(start, len, sign) in at {
            for v in &mut x[start..start + len] {
                *v = 0.5 * sign;
            }
        }
        x
    }

    #[test]
    fn the_cubic_fill_in_blocks_shorter_than_a_run_matches_one_call() {
        // A 40-sample run, then a 3-sample run whose left shoulder reaches into the first one's curve, at every
        // phase against blocks from 1 to 16. The file is one context plus 128 samples: blocks tile the first
        // 128, where the runs are, and the last call takes the rest.
        let n = CONTEXT_FRAMES + 128;
        for block in [1, 2, 3, 4, 5, 8, 13, 16] {
            for phase in 0..block {
                let x = plateaus(n, &[(20 + phase, 40, 1.0), (65 + phase, 3, -1.0)]);
                assert_cubic_blocks_match_one_call(
                    &x,
                    0.5,
                    block,
                    &format!("block {block}, phase {phase}"),
                );
            }
        }
    }

    #[test]
    fn cubic_runs_around_a_block_edge_are_filled_as_in_one_call() {
        // One run at the same offset from each of four 8,192-sample block edges, for offsets that put the run,
        // its shoulders or its curve across the edge.
        let block = 8_192;
        for offset in [-45, -12, -8, -6, -5, -4, -3, -1, 0, 1, 2, 3, 4, 5, 8, 30] {
            let at: Vec<(usize, usize, f64)> = (1..=4)
                .map(|e| {
                    (
                        ((e * block) as isize + offset) as usize,
                        9,
                        if e % 2 == 0 { 1.0 } else { -1.0 },
                    )
                })
                .collect();
            let x = plateaus(60_000, &at);
            assert_cubic_blocks_match_one_call(&x, 0.5, block, &format!("offset {offset}"));
        }
    }

    #[test]
    fn a_run_longer_than_a_block_is_reported_once_and_rebuilt_in_every_centre() {
        // A 50 Hz sine at 0.5 peaking at sample 80, clipped at 0.4375: runs of 155 samples, the first from
        // sample 3, chunked at 32 so it spans five centres. A-SPADE in blocks need not match one call, but its
        // report must, and every centre where one call rebuilds part of the run must hold rebuilt samples too
        // (near the file's start one call leaves the plateau). A tone this sparse converges in tens of
        // iterations, which keeps the debug build quick.
        let n = CONTEXT_FRAMES + 160;
        let phase =
            std::f64::consts::FRAC_PI_2 - 2.0 * std::f64::consts::PI * 50.0 * 80.0 / 48_000.0;
        let clean: Vec<f64> = (0..n)
            .map(|i| 0.5 * (2.0 * std::f64::consts::PI * 50.0 * i as f64 / 48_000.0 + phase).sin())
            .collect();
        let threshold = 0.4375;
        let y = clip(&clean, threshold);
        let clipped = runs(&y, threshold);
        assert_eq!(clipped[0], (3, 155));
        let mut a = declip::<f64>(threshold, DeclipMethod::Spade);
        let mut b = declip::<f64>(threshold, DeclipMethod::Spade);
        let one = whole(&mut a, &y);
        let out = chunked(&mut b, &y, 32);
        let (ra, rb) = (a.report(), b.report());
        assert_eq!(events(&rb), clipped);
        assert_eq!(rb.events, ra.events);
        for name in ["longest_run", "peak_in"] {
            assert_eq!(counter(&rb, name), counter(&ra, name), "{name}");
        }
        assert!(counter(&rb, "peak_out") > threshold);
        for (i, (o, v)) in out.iter().zip(&y).enumerate() {
            if v.abs() < threshold {
                assert_eq!(o, v, "unclipped sample {i} moved");
            } else {
                assert!(o.abs() >= threshold, "clipped sample {i} fell inside");
            }
        }
        let (start, len) = clipped[0];
        for centre in (0..start + len).step_by(32) {
            let inside = start.max(centre)..(start + len).min(centre + 32);
            if one[inside.clone()] != y[inside.clone()] {
                assert_ne!(out[inside.clone()], y[inside], "the centre at {centre}");
            }
        }
        let worst = one
            .iter()
            .zip(&out)
            .map(|(p, q)| (p - q).abs())
            .fold(0.0, f64::max);
        assert!(worst < 0.1, "chunked against one call: {worst}");
    }

    #[test]
    fn a_cubic_run_longer_than_the_context_is_cut_at_each_input_without_a_panic() {
        // A 6,000-sample plateau reaches past every input's end in blocks, where the curve is clipped to the
        // input. Chunked runs need not match one call here; nothing may panic, and the report still has one run.
        let x = plateaus(30_000, &[(10_000, 6_000, 1.0)]);
        for block in [1_000, 8_192] {
            let mut m = declip::<f64>(0.5, DeclipMethod::Cubic);
            let out = chunked(&mut m, &x, block);
            assert!(out.iter().all(|v| v.is_finite()), "block {block}");
            assert_eq!(events(&m.report()), [(10_000, 6_000)], "block {block}");
        }
    }

    #[test]
    fn the_constructor_refuses_a_threshold_outside_its_range() {
        for threshold in [0.0, 5e-5, -0.5, 1.0 + 1e-9, f64::NAN, f64::INFINITY] {
            let err = Declip::<f64>::new(threshold, DeclipMethod::Spade).err();
            assert!(
                err.is_some_and(|e| e.0.contains("threshold")),
                "{threshold}"
            );
        }
        for threshold in [MIN_THRESHOLD, 0.95, 1.0] {
            assert!(Declip::<f32>::new(threshold, DeclipMethod::Cubic).is_ok());
        }
    }
}
