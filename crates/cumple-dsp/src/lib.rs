//! cumple's audio repair core: a streaming STFT and the contract every repair module implements.
//!
//! Pure Rust and f64 at every public boundary. The Python bindings live in `crates/cumple-dsp-py`.

pub mod module;
pub mod stft;

pub use module::{Chunker, Edge, Event, Module, Report, process_whole};
pub use num_complex::Complex;
pub use stft::{Stft, Window};

/// This crate's version, which the bindings report as `cumple_dsp.core_version()` and receipts record.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
