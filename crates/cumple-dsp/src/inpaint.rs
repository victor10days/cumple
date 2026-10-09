// Ported from cathar (github.com/vbasky/cathar) crates/cathar/src/inpaint.rs at commit f2c2842f, MIT OR Apache-2.0, used under MIT; see crates/cumple-dsp/THIRD_PARTY.md.
//! Gap interpolation: rebuild a known missing span by autoregressive (Janssen, Godsill and Rayner)
//! interpolation.
//!
//! An AR model is estimated from the samples around the gap (Levinson-Durbin on the autocovariance of the
//! known samples only); the missing samples are then the ones that minimise the AR prediction error given
//! their fixed neighbours, a symmetric banded system solved by banded Cholesky. cathar repeats the estimate
//! and the solve `iterations` times. Everything here is f64, as upstream copies its f32 segment to f64.
//!
//! Changes from upstream, none of them to the arithmetic: the span is rebuilt in place in an f64 slice
//! rather than in a new f32 buffer (the caller casts, as upstream casts in and out); the slice need not be
//! the whole file, so `FileEnds` says which of its ends are the file's, and a gap whose context would reach
//! past an end that is not the file's is filled linearly instead (`Fill::Linear`); and `inpaint_auto` is
//! not ported.

/// AR model order for short gaps; the order grows with the gap up to 128.
pub const AR_ORDER: usize = 32;
/// Gaps longer than this (samples) are filled linearly: the dense solve would be too large.
pub const MAX_SOLVE: usize = 2048;

/// Whether each end of the slice handed to [`inpaint_gap`] is the file's own end.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct FileEnds {
    /// The slice begins at the file's first sample.
    pub left: bool,
    /// The slice ends at the file's last sample.
    pub right: bool,
}

/// How [`inpaint_gap`] filled a span.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Fill {
    /// Rebuilt by the AR solve.
    Ar,
    /// Filled by the straight line between its neighbours: the gap is longer than [`MAX_SOLVE`], or its
    /// context would reach past an end of the slice that is not the file's.
    Linear,
    /// Left as it was: the span is empty or does not lie inside the slice.
    Unchanged,
}

/// Samples of context the AR estimate reads on each side of a gap of `len` samples (inpaint.rs 37 to 40).
fn context(len: usize) -> usize {
    // AR reach scales with model order, so grow the order with the gap (capped). Context must dominate the
    // gap so the AR estimate reflects the signal, not the hole; also keep a floor for tiny gaps.
    let p = len.clamp(AR_ORDER, 128);
    (len * 4).max(p * 8).max(1024)
}

/// Samples [`inpaint_gap`] reads on each side of a gap of `len` samples: its AR context, or one neighbour
/// for a gap it fills linearly because it is longer than [`MAX_SOLVE`].
pub fn reach(len: usize) -> usize {
    if len > MAX_SOLVE { 1 } else { context(len) }
}

/// Rebuild `signal[start..start + len]` in place by AR interpolation refined over `iterations` passes (cathar
/// passes 3; 0 runs one). `ends` says which ends of `signal` are the file's: the context is clipped at a
/// file end, as upstream clips it, and a gap whose context would reach past any other end is filled linearly.
/// An empty or out-of-range span leaves the slice unchanged.
pub fn inpaint_gap(
    signal: &mut [f64],
    start: usize,
    len: usize,
    iterations: u32,
    ends: FileEnds,
) -> Fill {
    let n = signal.len();
    if len == 0 || start >= n || start + len > n {
        return Fill::Unchanged;
    }

    // Linear pre-fill across the gap (also the fallback for very long gaps).
    let left = if start > 0 { signal[start - 1] } else { 0.0 };
    let right = if start + len < n {
        signal[start + len]
    } else {
        0.0
    };
    for (i, s) in signal[start..start + len].iter_mut().enumerate() {
        let t = (i + 1) as f64 / (len + 1) as f64;
        *s = left * (1.0 - t) + right * t;
    }
    if len > MAX_SOLVE {
        return Fill::Linear;
    }

    let p = len.clamp(AR_ORDER, 128);
    let ctx = context(len);
    // The context may be clipped only where the slice ends at the file's own end.
    if (start < ctx && !ends.left) || (start + len + ctx > n && !ends.right) {
        return Fill::Linear;
    }
    let w0 = start.saturating_sub(ctx);
    let w1 = (start + len + ctx).min(n);
    // Upstream copies out[w0..w1] to f64 and writes back only the gap; the solve writes nothing else, so
    // working in place on the f64 slice is the same arithmetic.
    let seg = &mut signal[w0..w1];
    let gstart = start - w0;

    for _ in 0..iterations.max(1) {
        // Estimate AR from the known samples only (the gap would bias it).
        let a = estimate_ar_known(seg, gstart, len, p);
        let b = coef_autocorr(&a, p);
        solve_gap(seg, gstart, len, &b, p);
    }
    Fill::Ar
}

/// AR coefficients `[1, a1, ..., ap]` (Levinson) estimated from the samples outside the gap
/// `[gstart, gstart + glen)`, so the hole does not bias the fit.
fn estimate_ar_known(seg: &[f64], gstart: usize, glen: usize, p: usize) -> Vec<f64> {
    let n = seg.len();
    let known = |i: usize| i < gstart || i >= gstart + glen;
    let mut r = vec![0.0f64; p + 1];
    for (lag, rl) in r.iter_mut().enumerate() {
        let mut s = 0.0;
        for i in lag..n {
            if known(i) && known(i - lag) {
                s += seg[i] * seg[i - lag];
            }
        }
        *rl = s;
    }
    if r[0] <= 0.0 {
        let mut a = vec![0.0; p + 1];
        a[0] = 1.0;
        return a;
    }
    r[0] *= 1.0 + 1e-6; // white-noise regularisation for stability
    levinson(&r, p)
}

/// Levinson-Durbin recursion: solve the Yule-Walker equations for AR order `p`.
fn levinson(r: &[f64], p: usize) -> Vec<f64> {
    let mut a = vec![0.0f64; p + 1];
    a[0] = 1.0;
    let mut e = r[0];
    for i in 1..=p {
        let mut acc = r[i];
        for j in 1..i {
            acc += a[j] * r[i - j];
        }
        if e.abs() < 1e-12 {
            break;
        }
        let k = -acc / e;
        let prev: Vec<f64> = a[1..i].to_vec();
        for j in 1..i {
            a[j] = prev[j - 1] + k * prev[i - 1 - j];
        }
        a[i] = k;
        e *= 1.0 - k * k;
        if e <= 0.0 {
            break;
        }
    }
    a
}

/// Autocorrelation of the coefficient vector: `b[j]` is the sum over k of `a[k] * a[k + j]`.
fn coef_autocorr(a: &[f64], p: usize) -> Vec<f64> {
    let mut b = vec![0.0f64; p + 1];
    for (j, bj) in b.iter_mut().enumerate() {
        let mut s = 0.0;
        for k in 0..=(p - j) {
            s += a[k] * a[k + j];
        }
        *bj = s;
    }
    b
}

/// Solve the banded normal equations for the missing samples in `seg`.
fn solve_gap(seg: &mut [f64], gstart: usize, len: usize, b: &[f64], p: usize) {
    let n = seg.len();
    let mut mat = vec![vec![0.0f64; len]; len];
    let mut rhs = vec![0.0f64; len];
    // A well-fitting AR model makes the Gram matrix near-singular (its filter has roots on the unit
    // circle); a small ridge on the diagonal keeps the solve well-conditioned without noticeably biasing
    // the reconstruction.
    let ridge = 1e-6 * b[0];
    for i in 0..len {
        let mi = (gstart + i) as isize;
        for (j, row) in mat.iter_mut().enumerate() {
            let d = i.abs_diff(j);
            if d <= p {
                row[i] = b[d];
            }
        }
        mat[i][i] += ridge;
        // Known-neighbour contributions move to the right-hand side.
        let mut s = 0.0;
        for d in -(p as isize)..=(p as isize) {
            let idx = mi + d;
            if idx < 0 || idx as usize >= n {
                continue;
            }
            let gi = idx - gstart as isize;
            if gi >= 0 && (gi as usize) < len {
                continue; // unknown, so it stays in the matrix
            }
            s += b[d.unsigned_abs()] * seg[idx as usize];
        }
        rhs[i] = -s;
    }
    let x = solve_spd_banded(&mut mat, &rhs, p);
    for (i, xi) in x.iter().enumerate() {
        seg[gstart + i] = *xi;
    }
}

/// Banded symmetric positive-definite solve via Cholesky (half-bandwidth `p`).
// Textbook index-based linear algebra: the `[i][k]` and `[k][i]` (row against column) access pattern does
// not map cleanly onto iterators, so the range loops stay, as upstream keeps them.
#[allow(clippy::needless_range_loop)]
fn solve_spd_banded(mat: &mut [Vec<f64>], rhs: &[f64], p: usize) -> Vec<f64> {
    let n = rhs.len();
    // Lower Cholesky in place, restricted to the band.
    for i in 0..n {
        for j in i.saturating_sub(p)..=i {
            let klo = i.saturating_sub(p).max(j.saturating_sub(p));
            let mut sum = mat[i][j];
            for k in klo..j {
                sum -= mat[i][k] * mat[j][k];
            }
            if i == j {
                mat[i][i] = sum.max(1e-12).sqrt();
            } else {
                mat[i][j] = sum / mat[j][j];
            }
        }
    }
    // Forward solve L y = rhs.
    let mut y = vec![0.0f64; n];
    for i in 0..n {
        let mut s = rhs[i];
        for k in i.saturating_sub(p)..i {
            s -= mat[i][k] * y[k];
        }
        y[i] = s / mat[i][i];
    }
    // Back solve L^T x = y.
    let mut x = vec![0.0f64; n];
    for i in (0..n).rev() {
        let khi = (i + p).min(n - 1);
        let mut s = y[i];
        for k in (i + 1)..=khi {
            s -= mat[k][i] * x[k];
        }
        x[i] = s / mat[i][i];
    }
    x
}

#[cfg(test)]
mod tests {
    use super::*;

    const WHOLE: FileEnds = FileEnds {
        left: true,
        right: true,
    };

    fn sine(n: usize, amplitude: f64) -> Vec<f64> {
        (0..n)
            .map(|i| amplitude * (2.0 * std::f64::consts::PI * 440.0 * i as f64 / 48_000.0).sin())
            .collect()
    }

    fn max_error(a: &[f64], b: &[f64]) -> f64 {
        a.iter()
            .zip(b)
            .map(|(x, y)| (x - y).abs())
            .fold(0.0, f64::max)
    }

    /// What the linear pre-fill leaves in `[start, start + len)`.
    fn linear(x: &[f64], start: usize, len: usize) -> Vec<f64> {
        let (left, right) = (x[start - 1], x[start + len]);
        (0..len)
            .map(|i| {
                let t = (i + 1) as f64 / (len + 1) as f64;
                left * (1.0 - t) + right * t
            })
            .collect()
    }

    #[test]
    fn a_200_sample_gap_in_a_sine_is_rebuilt_within_a_hundredth() {
        // A faithful line-by-line port leaves about 6.4e-3 here (1.3e-3 at amplitude 0.1), so the bound is 1e-2.
        let truth = sine(12_000, 0.5);
        let (start, len) = (6_000, 200);
        let mut x = truth.clone();
        x[start..start + len].fill(0.0);
        assert_eq!(inpaint_gap(&mut x, start, len, 3, WHOLE), Fill::Ar);
        let err = max_error(&x[start..start + len], &truth[start..start + len]);
        assert!(err < 1e-2, "largest error in the gap {err:e}");
        assert_eq!(x[..start], truth[..start], "samples before the gap moved");
        assert_eq!(
            x[start + len..],
            truth[start + len..],
            "samples after the gap moved"
        );
    }

    #[test]
    fn a_gap_near_the_file_start_clips_its_context_and_solves_ar() {
        let truth = sine(8_000, 0.5);
        let (start, len) = (50, 100);
        let mut x = truth.clone();
        x[start..start + len].fill(0.0);
        assert_eq!(inpaint_gap(&mut x, start, len, 3, WHOLE), Fill::Ar);
        // With 50 known samples on the left the AR fill is about 0.07 off; the straight line is far worse.
        let err = max_error(&x[start..start + len], &truth[start..start + len]);
        let line = linear(&truth, start, len);
        let line_err = max_error(&line, &truth[start..start + len]);
        assert!(
            err < 0.1 && line_err > 5.0 * err,
            "AR {err:e}, straight line {line_err:e}"
        );
    }

    #[test]
    fn a_gap_near_a_chunk_edge_that_is_not_the_files_falls_back_to_linear() {
        let truth = sine(8_000, 0.5);
        let (start, len) = (50, 100);
        let mut x = truth.clone();
        let ends = FileEnds {
            left: false,
            right: true,
        };
        assert_eq!(inpaint_gap(&mut x, start, len, 3, ends), Fill::Linear);
        assert_eq!(x[start..start + len], linear(&truth, start, len)[..]);
        // The same at the right end: the gap ends 50 samples before a chunk edge.
        let mut x = truth.clone();
        let start = 8_000 - 150;
        let ends = FileEnds {
            left: true,
            right: false,
        };
        assert_eq!(inpaint_gap(&mut x, start, len, 3, ends), Fill::Linear);
        assert_eq!(x[start..start + len], linear(&truth, start, len)[..]);
    }

    #[test]
    fn a_gap_longer_than_max_solve_is_filled_linearly() {
        let truth = sine(20_000, 0.5);
        let (start, len) = (8_000, MAX_SOLVE + 1);
        let mut x = truth.clone();
        assert_eq!(inpaint_gap(&mut x, start, len, 3, WHOLE), Fill::Linear);
        assert_eq!(x[start..start + len], linear(&truth, start, len)[..]);
        assert_eq!(reach(len), 1);
        assert_eq!(reach(MAX_SOLVE), 4 * MAX_SOLVE);
        assert_eq!(reach(17), 1024);
    }

    #[test]
    fn an_empty_or_out_of_range_span_leaves_the_buffer_unchanged() {
        let truth = sine(1_000, 0.5);
        for (start, len) in [(500, 0), (1_000, 1), (2_000, 5), (990, 11), (0, 1_001)] {
            let mut x = truth.clone();
            assert_eq!(
                inpaint_gap(&mut x, start, len, 3, WHOLE),
                Fill::Unchanged,
                "start {start}, len {len}"
            );
            assert_eq!(x, truth, "start {start}, len {len}");
        }
    }
}
