//! Python bindings for cumple's audio repair core, imported as `cumple_dsp`.
//!
//! The core is the dependency `dsp` (the package cumple-dsp): the `#[pymodule]` below is named cumple_dsp,
//! which would shadow a dependency of that name.

use std::borrow::Cow;

use numpy::ndarray::Dimension;
use numpy::{
    Complex64, Element, PyArray1, PyArray2, PyArrayMethods, PyReadonlyArray, PyReadonlyArray1,
    PyReadonlyArray2, PyUntypedArrayMethods,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

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
    Ok(())
}
