//! cumple's audio repair core: a streaming STFT, the contract every repair module implements, and the
//! modules ported from cathar (De-click and the AR gap interpolator behind it).
//!
//! Pure Rust and f64 at every module boundary; a module generic over its sample type, such as
//! `Declick<f32>`, casts in and out inside. The Python bindings live in `crates/cumple-dsp-py`.

pub mod declick;
pub mod inpaint;
pub mod module;
pub mod stft;

pub use declick::{Declick, DeclickMethod};
pub use inpaint::{FileEnds, Fill, inpaint_gap};
pub use module::{Chunker, Edge, Event, Module, ParamError, Report, process_whole};
pub use num_complex::Complex;
pub use num_traits::Float;
pub use stft::{Stft, Window};

/// This crate's version, which the bindings report as `cumple_dsp.core_version()` and receipts record.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
