//! Python bindings for cumple's audio repair core, imported as `cumple_dsp`.
//!
//! The core is the dependency `dsp` (the package cumple-dsp): the `#[pymodule]` below is named cumple_dsp,
//! which would shadow a dependency of that name.

use std::borrow::Cow;

use dsp::Module;
use numpy::ndarray::Dimension;
use numpy::{
    Complex64, Element, PyArray1, PyArray2, PyArrayDyn, PyArrayMethods, PyReadonlyArray,
    PyReadonlyArray1, PyReadonlyArray2, PyReadonlyArrayDyn, PyUntypedArrayMethods,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

/// The array's elements in C order: a view when it already is, a copy otherwise.
fn c_order<'a, T: Element + Copy, D: Dimension>(a: &'a PyReadonlyArray<'_, T, D>) -> Cow<'a, [T]> {
    match a.as_slice() {
        Ok(s) if a.is_c_contiguous() => Cow::Borrowed(s),
        _ => Cow::Owned(a.as_array().iter().copied().collect()),
    }
}

/// One-sided short-time Fourier transform with a periodic Hann window.
///
/// `analyze(x)` returns complex128 of shape (frames, n_fft // 2 + 1); frame j covers samples
/// j * hop to j * hop + n_fft - 1, with no padding, so a signal shorter than n_fft has no frames.
/// `synthesize(spec, length)` overlap-adds the frames back into `length` samples, dividing by the
/// window-squared overlap sum; samples no frame covers are zero.
#[pyclass(module = "cumple_dsp", name = "Stft")]
struct Stft {
    inner: dsp::Stft,
}

#[pymethods]
impl Stft {
    #[new]
    #[pyo3(signature = (n_fft, hop, window = "hann"))]
    fn new(n_fft: usize, hop: usize, window: &str) -> PyResult<Self> {
        if n_fft < 2 {
            return Err(PyValueError::new_err(format!(
                "n_fft must be at least 2, got {n_fft}"
            )));
        }
        if hop == 0 || hop > n_fft {
            return Err(PyValueError::new_err(format!(
                "hop must be between 1 and n_fft ({n_fft}), got {hop}"
            )));
        }
        let window = match window {
            "hann" => dsp::Window::HannPeriodic,
            other => {
                return Err(PyValueError::new_err(format!(
                    "window must be \"hann\", got {other:?}"
                )));
            }
        };
        Ok(Stft {
            inner: dsp::Stft::new(n_fft, hop, window),
        })
    }

    #[getter]
    fn n_fft(&self) -> usize {
        self.inner.n_fft()
    }

    #[getter]
    fn hop(&self) -> usize {
        self.inner.hop()
    }

    /// The spectrum of every frame of `x` (float64, one dimension), as complex128 (frames, bins).
    fn analyze<'py>(
        &mut self,
        py: Python<'py>,
        x: PyReadonlyArray1<'py, f64>,
    ) -> Bound<'py, PyArray2<Complex64>> {
        let x = c_order(&x);
        let frames = self.inner.n_frames(x.len());
        let out = PyArray2::<Complex64>::zeros(py, [frames, self.inner.bins()], false);
        {
            let mut rw = out.readwrite();
            let spec = rw.as_slice_mut().expect("a new array is contiguous");
            let stft = &mut self.inner;
            py.detach(|| stft.analyze(&x, spec));
        }
        out
    }

    /// `length` samples overlap-added from `spec` (complex128, frames by n_fft // 2 + 1 bins).
    fn synthesize<'py>(
        &mut self,
        py: Python<'py>,
        spec: PyReadonlyArray2<'py, Complex64>,
        length: usize,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let bins = self.inner.bins();
        if spec.shape()[1] != bins {
            return Err(PyValueError::new_err(format!(
                "spec must have {bins} columns (n_fft // 2 + 1), got shape {:?}",
                spec.shape()
            )));
        }
        let spec = c_order(&spec);
        let out = PyArray1::<f64>::zeros(py, length, false);
        {
            let mut rw = out.readwrite();
            let y = rw.as_slice_mut().expect("a new array is contiguous");
            let stft = &mut self.inner;
            py.detach(|| stft.synthesize(&spec, y));
        }
        Ok(out)
    }
}

/// The frames and channels of a signal given as (frames,) or (frames, channels).
fn frames_and_channels(shape: &[usize]) -> PyResult<(usize, usize)> {
    match *shape {
        [frames] => Ok((frames, 1)),
        [frames, channels] if channels > 0 => Ok((frames, channels)),
        _ => Err(PyValueError::new_err(format!(
            "audio must be float64 of shape (frames,) or (frames, channels) with at least one channel, \
             got shape {shape:?}"
        ))),
    }
}

/// What the bindings need of a module beyond the trait: its class name, and how far its file has gone.
trait Tracked: Module + Clone {
    const NAME: &'static str;
    /// File samples done so far.
    fn done(&self) -> usize;
    /// Whether the module has had its last call.
    fn finished(&self) -> bool;
}

/// `Tracked` for each instantiation the bindings hold, through the type's own `done` and `finished`.
macro_rules! tracked {
    ($name:literal: $($t:ty),+) => {
        $(impl Tracked for $t {
            const NAME: &'static str = $name;
            fn done(&self) -> usize {
                <$t>::done(self)
            }
            fn finished(&self) -> bool {
                <$t>::finished(self)
            }
        })+
    };
}

tracked!("Declick": dsp::Declick<f32>, dsp::Declick<f64>);
tracked!("Declip": dsp::Declip<f32>, dsp::Declip<f64>);

/// One module instance per channel, at one precision, with the buffers that move each channel in and out.
struct Bank<M> {
    template: M,
    channels: Vec<M>,
    /// Audio has gone through the instances, so their number is fixed.
    started: bool,
    input: Vec<f64>,
    output: Vec<f64>,
}

impl<M: Tracked> Bank<M> {
    fn new(template: M) -> Self {
        Bank {
            template,
            channels: Vec::new(),
            started: false,
            input: Vec::new(),
            output: Vec::new(),
        }
    }

    /// File samples done so far and whether the file has finished; every channel moves in step.
    fn state(&self) -> (usize, bool) {
        self.channels
            .first()
            .map_or((0, false), |m| (m.done(), m.finished()))
    }

    /// Instances for `channels` channels: made on first use, fixed after that.
    fn ensure(&mut self, channels: usize) -> PyResult<()> {
        if !self.started {
            self.channels = vec![self.template.clone(); channels];
        } else if self.channels.len() != channels {
            return Err(PyValueError::new_err(format!(
                "this {} processes {} channels, got a block with {channels}",
                M::NAME,
                self.channels.len()
            )));
        }
        Ok(())
    }

    /// Run each channel of `x` (frames by channels, C order) through its own instance into `out`.
    fn run(&mut self, x: &[f64], out: &mut [f64], edge: dsp::Edge, whole: bool) {
        self.started = true;
        let n = self.channels.len();
        let frames = x.len() / n;
        for (c, m) in self.channels.iter_mut().enumerate() {
            self.input.clear();
            self.input.extend(x.iter().skip(c).step_by(n));
            self.output.resize(frames, 0.0);
            if whole {
                dsp::process_whole(m, &self.input, &mut self.output);
            } else {
                m.process(&self.input, &mut self.output, edge);
            }
            for (o, v) in out.iter_mut().skip(c).step_by(n).zip(&self.output) {
                *o = *v;
            }
        }
    }

    /// One call of the chunk protocol through every channel, checked against the protocol first so a wrong
    /// call raises ValueError instead of reaching the core's asserts.
    fn process<'py>(
        &mut self,
        py: Python<'py>,
        block: PyReadonlyArrayDyn<'py, f64>,
        edge: (bool, bool, usize),
    ) -> PyResult<Bound<'py, PyArrayDyn<f64>>> {
        let (frames, channels) = frames_and_channels(block.shape())?;
        let (first, last, padding) = edge;
        let context = self.template.context_frames();
        let (done, finished) = self.state();
        if finished {
            return Err(PyValueError::new_err(format!(
                "this {} has had its last block; one object processes one file",
                M::NAME
            )));
        }
        if first != (done <= context) {
            return Err(PyValueError::new_err(format!(
                "edge first must be {} after {done} samples: the left context reaches the start of the file \
                 only within the first context_frames ({context})",
                done <= context
            )));
        }
        let left = context.min(done);
        let right = if last { 0 } else { context };
        if frames < left + right + padding {
            return Err(PyValueError::new_err(format!(
                "after {done} samples a block needs {left} frames of left context, {right} of right context \
                 and {padding} of padding, at least {} frames; got {frames}",
                left + right + padding
            )));
        }
        self.ensure(channels)?;
        let x = c_order(&block);
        let out = PyArrayDyn::<f64>::zeros(py, block.shape().to_vec(), false);
        {
            let mut rw = out.readwrite();
            let y = rw.as_slice_mut().expect("a new array is contiguous");
            let edge = dsp::Edge {
                first,
                last,
                padding,
            };
            py.detach(|| self.run(&x, y, edge, false));
        }
        Ok(out)
    }

    /// One call over the whole of `x`, both ends the file's, on instances that have processed nothing.
    fn process_whole<'py>(
        &mut self,
        py: Python<'py>,
        x: PyReadonlyArrayDyn<'py, f64>,
    ) -> PyResult<Bound<'py, PyArrayDyn<f64>>> {
        let (_, channels) = frames_and_channels(x.shape())?;
        if self.started {
            return Err(PyValueError::new_err(format!(
                "process_whole runs over a whole file on a fresh {0}; this one has processed audio",
                M::NAME
            )));
        }
        self.ensure(channels)?;
        let input = c_order(&x);
        let out = PyArrayDyn::<f64>::zeros(py, x.shape().to_vec(), false);
        {
            let mut rw = out.readwrite();
            let y = rw.as_slice_mut().expect("a new array is contiguous");
            py.detach(|| self.run(&input, y, dsp::Edge::default(), true));
        }
        Ok(out)
    }

    /// Flush every channel (nothing, for a module without latency) and return the number of channels.
    fn flush(&mut self) -> usize {
        for m in &mut self.channels {
            m.flush(&mut []);
        }
        self.channels.len()
    }

    fn reports(&self) -> Vec<dsp::Report> {
        self.channels.iter().map(|m| m.report()).collect()
    }
}

/// A module's banks: the fidelity build at f32 or the shipped build at f64.
enum Banks<A, B> {
    F32(Bank<A>),
    F64(Bank<B>),
}

/// Runs `$body` with `$bank` bound to whichever precision's bank `$banks` holds.
macro_rules! with_bank {
    ($banks:expr, $bank:ident => $body:expr) => {
        match $banks {
            Banks::F32($bank) => $body,
            Banks::F64($bank) => $body,
        }
    };
}

/// `precision` as one of a module's two banks, each made from its own build of the module.
fn banks<A: Tracked, B: Tracked>(
    precision: &str,
    f32_build: impl FnOnce() -> Result<A, dsp::ParamError>,
    f64_build: impl FnOnce() -> Result<B, dsp::ParamError>,
) -> PyResult<Banks<A, B>> {
    let refuse = |e: dsp::ParamError| PyValueError::new_err(e.0);
    match precision {
        "f32" => Ok(Banks::F32(Bank::new(f32_build().map_err(refuse)?))),
        "f64" => Ok(Banks::F64(Bank::new(f64_build().map_err(refuse)?))),
        other => Err(PyValueError::new_err(format!(
            "precision must be \"f32\" or \"f64\", got {other:?}"
        ))),
    }
}

/// The positions, widths and channels of every channel's events, ordered by channel, then position.
fn events(reports: &[dsp::Report]) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    let (mut positions, mut widths, mut channels) = (Vec::new(), Vec::new(), Vec::new());
    for (c, r) in reports.iter().enumerate() {
        for e in &r.events {
            positions.push(e.start);
            widths.push(e.len);
            channels.push(c);
        }
    }
    (positions, widths, channels)
}

/// Every channel's value of the counter `name`.
fn counters<'a>(reports: &'a [dsp::Report], name: &'a str) -> impl Iterator<Item = f64> + 'a {
    reports.iter().flat_map(move |r| {
        r.counters
            .iter()
            .filter(move |(n, _)| n == name)
            .map(|(_, v)| *v)
    })
}

/// De-click, ported from cathar: impulse clicks found against a sliding local RMS and rebuilt by AR
/// interpolation.
///
/// `threshold` is in local-RMS multiples and must be below sqrt(window): the local RMS includes the sample
/// tested, so no ratio exceeds sqrt(window), and a lone non-zero sample in digital silence sits exactly on
/// it, so any threshold below fires on it. `window` is the detector window in samples (cathar's CLI fixes
/// 64), `method` "ar" or "cubic", `iterations` the AR refinement passes (cathar passes 3). `precision="f32"`
/// selects the fidelity build, which does cathar's float32 arithmetic in cathar's order; "f64" ships.
///
/// Audio is float64 of shape (frames,) or (frames, channels); each channel runs through its own instance.
/// `process(block, edge=(first, last, padding))` takes one call of the chunk protocol (crates/cumple-dsp,
/// module.rs): up to `context_frames` of this object's own earlier output, the block, then `context_frames`
/// raw samples, or the rest of the file when `last`. `process_whole(x)` is one call over a whole signal on a
/// fresh object. `report()` lists each span handed to a filler (its start and its length in file samples,
/// shoulders included, and its channel) and the counts of linear and context fallbacks.
#[pyclass(module = "cumple_dsp", name = "Declick")]
struct Declick {
    banks: Banks<dsp::Declick<f32>, dsp::Declick<f64>>,
}

#[pymethods]
impl Declick {
    #[new]
    #[pyo3(signature = (samplerate, threshold = 5.0, window = 64, method = "ar", iterations = 3, precision = "f64"))]
    fn new(
        samplerate: i64,
        threshold: f64,
        window: usize,
        method: &str,
        iterations: u32,
        precision: &str,
    ) -> PyResult<Self> {
        if samplerate <= 0 {
            return Err(PyValueError::new_err(format!(
                "samplerate must be positive, got {samplerate}"
            )));
        }
        let method = match method {
            "ar" => dsp::DeclickMethod::Ar,
            "cubic" => dsp::DeclickMethod::Cubic,
            other => {
                return Err(PyValueError::new_err(format!(
                    "method must be \"ar\" or \"cubic\", got {other:?}"
                )));
            }
        };
        let banks = banks(
            precision,
            || dsp::Declick::new(threshold, window, method, iterations),
            || dsp::Declick::new(threshold, window, method, iterations),
        )?;
        Ok(Declick { banks })
    }

    #[getter]
    fn context_frames(&self) -> usize {
        with_bank!(&self.banks, b => b.template.context_frames())
    }

    #[getter]
    fn latency_frames(&self) -> usize {
        with_bank!(&self.banks, b => b.template.latency_frames())
    }

    /// One call of the chunk protocol; returns every frame of `block` processed, the caller keeping the centre.
    #[pyo3(signature = (block, *, edge))]
    fn process<'py>(
        &mut self,
        py: Python<'py>,
        block: PyReadonlyArrayDyn<'py, f64>,
        edge: (bool, bool, usize),
    ) -> PyResult<Bound<'py, PyArrayDyn<f64>>> {
        with_bank!(&mut self.banks, bank => bank.process(py, block, edge))
    }

    /// One call over the whole of `x`, both ends the file's; the object must not have processed audio yet.
    fn process_whole<'py>(
        &mut self,
        py: Python<'py>,
        x: PyReadonlyArrayDyn<'py, f64>,
    ) -> PyResult<Bound<'py, PyArrayDyn<f64>>> {
        with_bank!(&mut self.banks, bank => bank.process_whole(py, x))
    }

    /// Nothing: De-click has no latency, so it holds no samples back. An empty (0, channels) array.
    fn flush<'py>(&mut self, py: Python<'py>) -> Bound<'py, PyArray2<f64>> {
        let channels = with_bank!(&mut self.banks, bank => bank.flush());
        PyArray2::<f64>::zeros(py, [0, channels], false)
    }

    /// What every channel has done: `clicks`, and for each span `positions`, `widths` and `channels`, ordered
    /// by channel, then position; `linear_fallbacks` and `context_fallbacks` summed over the channels.
    fn report<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let reports = with_bank!(&self.banks, bank => bank.reports());
        let (positions, widths, channels) = events(&reports);
        let linear: f64 = counters(&reports, "linear_fallbacks").sum();
        let context: f64 = counters(&reports, "context_fallbacks").sum();
        let d = PyDict::new(py);
        d.set_item("clicks", positions.len())?;
        d.set_item("positions", positions)?;
        d.set_item("widths", widths)?;
        d.set_item("channels", channels)?;
        d.set_item("linear_fallbacks", linear as u64)?;
        d.set_item("context_fallbacks", context as u64)?;
        Ok(d)
    }
}

/// De-clip, ported from cathar: samples at or above `threshold` rebuilt by A-SPADE or by a cubic curve.
///
/// `threshold` is a linear sample value from 1e-4 to 1.0: 0.95 suits a file clipped at full scale, and the
/// harness passes each file's clip level. `method` is "spade" (A-SPADE over a 1,024-sample Gabor frame,
/// cathar's default; every unclipped sample comes back unchanged) or "cubic" (a cubic Hermite curve across
/// each clipped run and 4 samples of shoulder on each side, which moves those shoulders and rebuilds no peak).
/// `precision="f32"` selects the fidelity build, which does cathar's float32 arithmetic in cathar's order;
/// "f64" ships.
///
/// Audio, `process`, `process_whole` and `flush` work as Declick's do. `report()` lists each clipped run (its
/// start and its length in file samples, and its channel) as `runs`, `positions`, `widths` and `channels`,
/// with `longest_run`, `peak_in` and `peak_out` (the largest magnitudes in and out) over the channels, and the
/// A-SPADE `iterations` and `frames` summed over calls and channels.
#[pyclass(module = "cumple_dsp", name = "Declip")]
struct Declip {
    banks: Banks<dsp::Declip<f32>, dsp::Declip<f64>>,
}

#[pymethods]
impl Declip {
    #[new]
    #[pyo3(signature = (samplerate, threshold = 0.95, method = "spade", precision = "f64"))]
    fn new(samplerate: i64, threshold: f64, method: &str, precision: &str) -> PyResult<Self> {
        if samplerate <= 0 {
            return Err(PyValueError::new_err(format!(
                "samplerate must be positive, got {samplerate}"
            )));
        }
        let method = match method {
            "spade" => dsp::DeclipMethod::Spade,
            "cubic" => dsp::DeclipMethod::Cubic,
            other => {
                return Err(PyValueError::new_err(format!(
                    "method must be \"spade\" or \"cubic\", got {other:?}"
                )));
            }
        };
        let banks = banks(
            precision,
            || dsp::Declip::new(threshold, method),
            || dsp::Declip::new(threshold, method),
        )?;
        Ok(Declip { banks })
    }

    #[getter]
    fn context_frames(&self) -> usize {
        with_bank!(&self.banks, b => b.template.context_frames())
    }

    #[getter]
    fn latency_frames(&self) -> usize {
        with_bank!(&self.banks, b => b.template.latency_frames())
    }

    /// One call of the chunk protocol; returns every frame of `block` processed, the caller keeping the centre.
    #[pyo3(signature = (block, *, edge))]
    fn process<'py>(
        &mut self,
        py: Python<'py>,
        block: PyReadonlyArrayDyn<'py, f64>,
        edge: (bool, bool, usize),
    ) -> PyResult<Bound<'py, PyArrayDyn<f64>>> {
        with_bank!(&mut self.banks, bank => bank.process(py, block, edge))
    }

    /// One call over the whole of `x`, both ends the file's; the object must not have processed audio yet.
    fn process_whole<'py>(
        &mut self,
        py: Python<'py>,
        x: PyReadonlyArrayDyn<'py, f64>,
    ) -> PyResult<Bound<'py, PyArrayDyn<f64>>> {
        with_bank!(&mut self.banks, bank => bank.process_whole(py, x))
    }

    /// Nothing: De-clip has no latency, so it holds no samples back. An empty (0, channels) array.
    fn flush<'py>(&mut self, py: Python<'py>) -> Bound<'py, PyArray2<f64>> {
        let channels = with_bank!(&mut self.banks, bank => bank.flush());
        PyArray2::<f64>::zeros(py, [0, channels], false)
    }

    /// What every channel has done: `runs`, and for each clipped run `positions`, `widths` and `channels`,
    /// ordered by channel, then position; `longest_run`, `peak_in` and `peak_out` over the channels;
    /// `iterations` and `frames` summed over them.
    fn report<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let reports = with_bank!(&self.banks, bank => bank.reports());
        let (positions, widths, channels) = events(&reports);
        let largest = |name| counters(&reports, name).fold(0.0, f64::max);
        let sum = |name| counters(&reports, name).sum::<f64>();
        let d = PyDict::new(py);
        d.set_item("runs", positions.len())?;
        d.set_item("positions", positions)?;
        d.set_item("widths", widths)?;
        d.set_item("channels", channels)?;
        d.set_item("longest_run", largest("longest_run") as u64)?;
        d.set_item("peak_in", largest("peak_in"))?;
        d.set_item("peak_out", largest("peak_out"))?;
        d.set_item("iterations", sum("iterations") as u64)?;
        d.set_item("frames", sum("frames") as u64)?;
        Ok(d)
    }
}

/// The version of the core crate (cumple-dsp) this module was built with.
#[pyfunction]
fn core_version() -> &'static str {
    dsp::VERSION
}

#[pymodule]
fn cumple_dsp(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(core_version, m)?)?;
    m.add_class::<Stft>()?;
    m.add_class::<Declick>()?;
    m.add_class::<Declip>()?;
    Ok(())
}
