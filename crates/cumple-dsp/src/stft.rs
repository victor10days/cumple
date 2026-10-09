//! A streaming short-time Fourier transform and its inverse, f64 throughout.
//!
//! Frames are one-sided spectra of `n_fft / 2 + 1` bins, unnormalised (scipy's `ShortTimeFFT` with
//! `scale_to=None` and `phase_shift=None` gives the same numbers). Frame `j` covers samples `j * hop` to
//! `j * hop + n_fft - 1`; there is no padding, so the first frame starts at sample 0 and the last is the last
//! that fits.

use std::f64::consts::PI;
use std::sync::Arc;

use num_complex::Complex;
use realfft::{ComplexToReal, RealFftPlanner, RealToComplex};

/// The analysis and synthesis window.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Window {
    /// 0.5 - 0.5 cos(2 pi i / n): scipy's `hann(n, sym=False)`, the window for overlap-add.
    HannPeriodic,
    /// 0.5 - 0.5 cos(2 pi i / (n - 1)): cathar's `hann_window` (`util.rs`), for the ports' tests.
    HannSymmetric,
}

impl Window {
    /// The `n` coefficients of this window; a window of one sample is `[1.0]`.
    pub fn coefficients(self, n: usize) -> Vec<f64> {
        if n <= 1 {
            return vec![1.0; n];
        }
        let period = match self {
            Window::HannPeriodic => n as f64,
            Window::HannSymmetric => (n - 1) as f64,
        };
        (0..n)
            .map(|i| 0.5 - 0.5 * (2.0 * PI * (i as f64 / period)).cos())
            .collect()
    }
}

/// One-sided STFT on `realfft`. The transforms, the window and every scratch buffer are made once in
/// [`Stft::new`]; `analyze` and `synthesize` allocate nothing.
pub struct Stft {
    n_fft: usize,
    hop: usize,
    window: Vec<f64>,
    /// The window-squared overlap sum where every frame that could cover a sample exists, by the sample's
    /// index modulo `hop`. Constant for the periodic Hann at hop n_fft / 4.
    overlap: Vec<f64>,
    forward: Arc<dyn RealToComplex<f64>>,
    inverse: Arc<dyn ComplexToReal<f64>>,
    frame: Vec<f64>,
    spectrum: Vec<Complex<f64>>,
    scratch: Vec<Complex<f64>>,
}

impl Stft {
    /// Plans a transform of `n_fft` samples (at least 2) every `hop` samples (1 to `n_fft`).
    pub fn new(n_fft: usize, hop: usize, window: Window) -> Stft {
        assert!(n_fft >= 2, "n_fft must be at least 2, got {n_fft}");
        assert!(
            (1..=n_fft).contains(&hop),
            "hop must be between 1 and n_fft ({n_fft}), got {hop}"
        );
        let mut planner = RealFftPlanner::<f64>::new();
        let forward = planner.plan_fft_forward(n_fft);
        let inverse = planner.plan_fft_inverse(n_fft);
        let window = window.coefficients(n_fft);
        let mut overlap = vec![0.0; hop];
        for (i, w) in window.iter().enumerate() {
            overlap[i % hop] += w * w;
        }
        let scratch =
            vec![Complex::new(0.0, 0.0); forward.get_scratch_len().max(inverse.get_scratch_len())];
        Stft {
            n_fft,
            hop,
            window,
            overlap,
            frame: vec![0.0; n_fft],
            spectrum: forward.make_output_vec(),
            scratch,
            forward,
            inverse,
        }
    }

    pub fn n_fft(&self) -> usize {
        self.n_fft
    }

    pub fn hop(&self) -> usize {
        self.hop
    }

    /// Bins per frame: `n_fft / 2 + 1`.
    pub fn bins(&self) -> usize {
        self.n_fft / 2 + 1
    }

    /// Frames in a signal of `len` samples: 0 when it is shorter than `n_fft`.
    pub fn n_frames(&self, len: usize) -> usize {
        if len < self.n_fft {
            0
        } else {
            (len - self.n_fft) / self.hop + 1
        }
    }

    /// Writes the windowed spectrum of every frame of `x` into `out`, row major: frame by frame, each
    /// `bins()` long. `out` holds exactly `n_frames(x.len()) * bins()` values.
    pub fn analyze(&mut self, x: &[f64], out: &mut [Complex<f64>]) {
        let bins = self.bins();
        assert_eq!(
            out.len(),
            self.n_frames(x.len()) * bins,
            "out must hold n_frames(x.len()) * bins() values"
        );
        for (j, spectrum) in out.chunks_exact_mut(bins).enumerate() {
            let start = j * self.hop;
            for ((f, s), w) in self
                .frame
                .iter_mut()
                .zip(&x[start..start + self.n_fft])
                .zip(&self.window)
            {
                *f = s * w;
            }
            self.forward
                .process_with_scratch(&mut self.frame, spectrum, &mut self.scratch)
                .expect("the buffers were sized for this transform in new");
        }
    }

    /// Overlap-adds the frames of `spec` (row major, `bins()` per frame) into `out`, windowing each again and
    /// dividing by the window-squared overlap sum. Where frames are missing (the edges) the divisor is the
    /// partial sum of the frames that exist; a sample whose sum is zero (no frame reaches it, or every
    /// window that does is zero there) is 0. Frames that start past the end of `out` are ignored and the
    /// rest are cut at its end.
    pub fn synthesize(&mut self, spec: &[Complex<f64>], out: &mut [f64]) {
        let bins = self.bins();
        assert_eq!(
            spec.len() % bins,
            0,
            "spec must hold whole frames of bins() values"
        );
        let frames = spec.len() / bins;
        let scale = 1.0 / self.n_fft as f64;
        out.fill(0.0);
        for (j, spectrum) in spec.chunks_exact(bins).enumerate() {
            let start = j * self.hop;
            if start >= out.len() {
                break;
            }
            self.spectrum.copy_from_slice(spectrum);
            // The spectrum of a real signal has no imaginary part at DC, nor at Nyquist for an even n_fft.
            self.spectrum[0].im = 0.0;
            if self.n_fft.is_multiple_of(2) {
                self.spectrum[bins - 1].im = 0.0;
            }
            self.inverse
                .process_with_scratch(&mut self.spectrum, &mut self.frame, &mut self.scratch)
                .expect("the buffers were sized for this transform in new");
            let end = (start + self.n_fft).min(out.len());
            for ((o, f), w) in out[start..end]
                .iter_mut()
                .zip(&self.frame)
                .zip(&self.window)
            {
                *o += f * scale * w;
            }
        }
        for (t, o) in out.iter_mut().enumerate() {
            let sum = self.overlap_sum(t, frames);
            *o = if sum > 0.0 { *o / sum } else { 0.0 };
        }
    }

    /// The window-squared sum of the frames, among `frames`, that cover sample `t`.
    fn overlap_sum(&self, t: usize, frames: usize) -> f64 {
        if frames == 0 {
            return 0.0;
        }
        // Frame j covers t when j * hop <= t < j * hop + n_fft.
        let last = t / self.hop;
        if t + self.hop >= self.n_fft && last < frames {
            return self.overlap[t % self.hop];
        }
        let lo = if t + 1 > self.n_fft {
            (t + 1 - self.n_fft).div_ceil(self.hop)
        } else {
            0
        };
        let hi = last.min(frames - 1);
        (lo..=hi)
            .map(|j| {
                let w = self.window[t - j * self.hop];
                w * w
            })
            .sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const FS: f64 = 48_000.0;

    fn sine(len: usize, hz: f64) -> Vec<f64> {
        (0..len)
            .map(|i| (2.0 * PI * hz * i as f64 / FS).sin())
            .collect()
    }

    fn noise(len: usize, seed: u64) -> Vec<f64> {
        // A 64-bit linear congruential generator: enough to make the test signal broadband and repeatable.
        let mut state = seed;
        (0..len)
            .map(|_| {
                state = state
                    .wrapping_mul(6_364_136_223_846_793_005)
                    .wrapping_add(1_442_695_040_888_963_407);
                (state >> 11) as f64 / (1u64 << 53) as f64 - 0.5
            })
            .collect()
    }

    #[test]
    fn a_440_hz_sine_peaks_at_bin_9_in_every_frame() {
        let (n_fft, hop) = (1024, 256);
        let x = sine(4096, 440.0);
        let mut stft = Stft::new(n_fft, hop, Window::HannPeriodic);
        let frames = stft.n_frames(x.len());
        assert_eq!(frames, (4096 - 1024) / 256 + 1);
        let bins = stft.bins();
        let mut spec = vec![Complex::new(0.0, 0.0); frames * bins];
        stft.analyze(&x, &mut spec);
        let expected = (440.0 / FS * n_fft as f64).round() as usize;
        assert_eq!(expected, 9);
        for (j, frame) in spec.chunks_exact(bins).enumerate() {
            let peak = (0..bins)
                .max_by(|&a, &b| frame[a].norm().total_cmp(&frame[b].norm()))
                .unwrap();
            assert_eq!(peak, expected, "frame {j} peaks at bin {peak}");
        }
    }

    #[test]
    fn analysis_then_synthesis_reconstructs_away_from_the_edges() {
        let (n_fft, hop) = (1024, 256);
        let len = 48_000;
        let x: Vec<f64> = sine(len, 440.0)
            .iter()
            .zip(noise(len, 7))
            .map(|(s, n)| 0.5 * s + n)
            .collect();
        let mut stft = Stft::new(n_fft, hop, Window::HannPeriodic);
        let frames = stft.n_frames(len);
        let mut spec = vec![Complex::new(0.0, 0.0); frames * stft.bins()];
        stft.analyze(&x, &mut spec);
        let mut y = vec![f64::NAN; len];
        stft.synthesize(&spec, &mut y);
        let worst = (n_fft..len - n_fft)
            .map(|i| (y[i] - x[i]).abs())
            .fold(0.0, f64::max);
        assert!(worst < 1e-10, "largest reconstruction error {worst:e}");
        assert!(
            y.iter().all(|v| v.is_finite()),
            "the edges must never divide by zero"
        );
    }

    #[test]
    fn the_edges_divide_by_the_partial_overlap_sum() {
        let (n_fft, hop) = (1024, 256);
        let len = 48_100; // the last frame ends at 47,872, so the tail past it has no frame
        let x = noise(len, 3);
        let mut stft = Stft::new(n_fft, hop, Window::HannPeriodic);
        let frames = stft.n_frames(len);
        let covered = (frames - 1) * hop + n_fft;
        assert!(covered < len);
        let mut spec = vec![Complex::new(0.0, 0.0); frames * stft.bins()];
        stft.analyze(&x, &mut spec);
        let mut y = vec![f64::NAN; len];
        stft.synthesize(&spec, &mut y);
        assert_eq!(
            y[0], 0.0,
            "the periodic window is zero at sample 0, so nothing reaches it"
        );
        let edges = (1..n_fft).chain(covered - n_fft..covered);
        let worst = edges.map(|i| (y[i] - x[i]).abs()).fold(0.0, f64::max);
        assert!(
            worst < 1e-9,
            "largest error where only some frames reach: {worst:e}"
        );
        assert!(
            y[covered..].iter().all(|&v| v == 0.0),
            "no frame reaches the tail"
        );
    }

    #[test]
    fn a_signal_shorter_than_n_fft_has_no_frames_and_synthesizes_to_zeros() {
        let mut stft = Stft::new(1024, 256, Window::HannPeriodic);
        assert_eq!(stft.n_frames(0), 0);
        assert_eq!(stft.n_frames(1023), 0);
        assert_eq!(stft.n_frames(1024), 1);
        stft.analyze(&sine(1023, 440.0), &mut []);
        let mut y = vec![1.0; 1023];
        stft.synthesize(&[], &mut y);
        assert!(y.iter().all(|&v| v == 0.0));
    }

    #[test]
    fn hann_symmetric_is_cathars_hann_window() {
        let w = Window::HannSymmetric.coefficients(1024);
        assert_eq!(w.len(), 1024);
        for i in [0usize, 511, 512, 1023] {
            let cathar = 0.5 - 0.5 * (2.0 * PI * i as f64 / 1023.0).cos();
            assert!(
                (w[i] - cathar).abs() < 1e-15,
                "w[{i}] = {} against {cathar}",
                w[i]
            );
        }
        assert_eq!(w[0], 0.0);
        assert!(w[1023].abs() < 1e-15);
        assert!(
            (w[511] - w[512]).abs() < 1e-15,
            "the symmetric window is symmetric about 511.5"
        );
        // cathar computes the same expression in f32 (util.rs lines 5 to 13); the two agree to f32 precision.
        let n = 1024f32 - 1.0;
        for i in [0usize, 511, 512, 1023] {
            let cathar_f32 = 0.5 - 0.5 * (2.0 * std::f32::consts::PI * (i as f32 / n)).cos();
            assert!(
                (w[i] - f64::from(cathar_f32)).abs() < 1e-6,
                "w[{i}] against cathar's f32 {cathar_f32}"
            );
        }
    }
}
