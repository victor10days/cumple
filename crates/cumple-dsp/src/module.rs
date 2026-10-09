//! The module contract: what a repair module tells its caller, and how a caller feeds it a file in blocks.
//!
//! A caller processes one channel of a file in consecutive calls. Each call's input is a centre (the block
//! the caller keeps) with context on both sides:
//!
//! - the left context is the `context_frames()` samples before the centre, or every sample before it when
//!   the file starts sooner (then `Edge::first` is true). It is the module's own earlier output, so a
//!   module sees repaired audio behind it, as it would in one pass over the whole file;
//! - the right context is the `context_frames()` raw samples after the centre. When the file ends sooner
//!   the call takes the rest of the file as its centre instead, has no right context, and `Edge::last` is
//!   true; `Edge::padding` then counts samples after the file's end that are not signal;
//! - the centres tile the file in order, so `Edge::centre` locates a call's centre from the number of
//!   samples earlier centres covered. A module that reports positions in file samples counts them that way.
//!
//! A call's input is therefore never longer than the block plus twice `context_frames()`.

use std::ops::Range;

/// Where one call's input sits in the file.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Edge {
    /// The input begins at the file's first sample: the left context is cut short by the start of the file.
    pub first: bool,
    /// The file ends in this input: the centre runs to the file's last sample and no right context follows.
    pub last: bool,
    /// Samples at the end of the input that are not signal, after the file's last sample.
    pub padding: usize,
}

impl Edge {
    /// The centre of an input of `input_len` samples, for a module with `context` frames of context whose
    /// earlier calls' centres covered `done` samples of the file.
    pub fn centre(self, input_len: usize, context: usize, done: usize) -> Range<usize> {
        let left = context.min(done);
        let right = if self.last { 0 } else { context };
        assert!(
            left + right + self.padding <= input_len,
            "an input shorter than its context and padding"
        );
        left..input_len - self.padding - right
    }
}

/// One thing a module did, at a place in the file.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Event {
    /// What happened, such as a repaired click or a rebuilt clipped run; each module documents its kinds.
    pub kind: &'static str,
    /// The first sample the event covers, counted from the start of the file.
    pub start: usize,
    /// How many samples it covers.
    pub len: usize,
}

/// What a module did over everything it has processed, for the receipt.
#[derive(Clone, Debug, Default, PartialEq)]
pub struct Report {
    pub events: Vec<Event>,
    /// Named totals and extremes, such as a count of fallbacks or the longest run.
    pub counters: Vec<(String, f64)>,
}

/// Parameters a module refuses, with the reason, which the bindings raise as `ValueError`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ParamError(pub String);

impl std::fmt::Display for ParamError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for ParamError {}

/// A repair module. One instance processes one channel of one file.
///
/// A module sizes its buffers once, from `context_frames` and the longest input it is given;
/// `process` allocates nothing per sample.
pub trait Module: Send {
    /// A stable identifier, such as `declick`.
    fn id(&self) -> &'static str;
    /// The module's version, which receipts record beside its parameters.
    fn version(&self) -> &'static str;
    /// Samples of neighbouring audio the module needs on each side of a block to process it as if it had
    /// the whole file.
    fn context_frames(&self) -> usize;
    /// Samples by which the output lags the input; the caller compensates. 0 for every build-1 module.
    fn latency_frames(&self) -> usize;
    /// Process one call's input (left context, centre, right context, padding; see the module docs) and
    /// write every sample of `output`, which has the same length. The caller keeps the centre.
    fn process(&mut self, input: &[f64], output: &mut [f64], edge: Edge);
    /// Write out anything a latency-carrying module still holds and return how many samples it wrote.
    fn flush(&mut self, output: &mut [f64]) -> usize;
    /// What the module has done so far.
    fn report(&self) -> Report;
}

/// Runs a module over a whole signal held in memory, block by block, as a streaming caller would.
pub struct Chunker {
    block: usize,
    context: usize,
    input: Vec<f64>,
    output: Vec<f64>,
}

impl Chunker {
    /// Buffers for blocks of `block` samples with `context` frames on each side, allocated once here.
    pub fn new(block: usize, context: usize) -> Chunker {
        assert!(block > 0, "a block holds at least one sample");
        let cap = block + 2 * context;
        Chunker {
            block,
            context,
            input: Vec::with_capacity(cap),
            output: vec![0.0; cap],
        }
    }

    /// Process `x` into `out` through `module`, which must have this chunker's context and no latency.
    ///
    /// Blocks are `block` samples, except that a call whose right context the end of the file would cut
    /// short takes the rest of the file instead (so its centre is shorter than `block + context`). An empty
    /// signal makes no call.
    pub fn run<M: Module + ?Sized>(&mut self, module: &mut M, x: &[f64], out: &mut [f64]) {
        assert_eq!(x.len(), out.len(), "out must be as long as x");
        assert_eq!(
            module.context_frames(),
            self.context,
            "the chunker was built for another context"
        );
        assert_eq!(
            module.latency_frames(),
            0,
            "the chunker serves modules without latency"
        );
        let n = x.len();
        let mut start = 0;
        while start < n {
            let mut end = (start + self.block).min(n);
            if n - end < self.context {
                end = n;
            }
            let last = end == n;
            let lo = start.saturating_sub(self.context);
            let hi = if last { n } else { end + self.context };
            self.input.clear();
            self.input.extend_from_slice(&out[lo..start]);
            self.input.extend_from_slice(&x[start..hi]);
            let output = &mut self.output[..hi - lo];
            module.process(
                &self.input,
                output,
                Edge {
                    first: lo == 0,
                    last,
                    padding: 0,
                },
            );
            out[start..end].copy_from_slice(&output[start - lo..end - lo]);
            start = end;
        }
    }
}

/// Process a whole signal in one call, with both ends of the input at the ends of the file.
pub fn process_whole<M: Module + ?Sized>(module: &mut M, x: &[f64], out: &mut [f64]) {
    assert_eq!(x.len(), out.len(), "out must be as long as x");
    assert_eq!(
        module.latency_frames(),
        0,
        "process_whole serves modules without latency"
    );
    module.process(
        x,
        out,
        Edge {
            first: true,
            last: true,
            padding: 0,
        },
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Adds one to every sample and keeps a copy of every call, so a test can read what the chunker fed it.
    struct Probe {
        context: usize,
        calls: Vec<(Vec<f64>, Edge)>,
    }

    impl Probe {
        fn new(context: usize) -> Probe {
            Probe {
                context,
                calls: Vec::new(),
            }
        }
    }

    impl Module for Probe {
        fn id(&self) -> &'static str {
            "probe"
        }
        fn version(&self) -> &'static str {
            "0"
        }
        fn context_frames(&self) -> usize {
            self.context
        }
        fn latency_frames(&self) -> usize {
            0
        }
        fn process(&mut self, input: &[f64], output: &mut [f64], edge: Edge) {
            for (o, i) in output.iter_mut().zip(input) {
                *o = i + 1.0;
            }
            self.calls.push((input.to_vec(), edge));
        }
        fn flush(&mut self, _output: &mut [f64]) -> usize {
            0
        }
        fn report(&self) -> Report {
            Report::default()
        }
    }

    fn ramp(n: usize) -> Vec<f64> {
        (0..n).map(|i| i as f64 * 0.25 - 3.0).collect()
    }

    // (block, context, length): blocks shorter and longer than the context, a tail shorter than the
    // context (merged into the call before it), a file shorter than one block, and no context at all.
    const SHAPES: [(usize, usize, usize); 10] = [
        (8, 3, 50),
        (3, 8, 50),
        (8, 0, 50),
        (8, 3, 8),
        (8, 3, 7),
        (8, 3, 10),
        (8, 3, 11),
        (8, 3, 13),
        (1, 1, 5),
        (16_384, 4_096, 40_000),
    ];

    #[test]
    fn chunked_output_is_the_centres_of_every_call() {
        for (block, context, n) in SHAPES {
            let x = ramp(n);
            let mut probe = Probe::new(context);
            let mut out = vec![f64::NAN; n];
            Chunker::new(block, context).run(&mut probe, &x, &mut out);
            let expected: Vec<f64> = x.iter().map(|v| v + 1.0).collect();
            assert_eq!(
                out, expected,
                "block {block}, context {context}, length {n}"
            );
        }
    }

    #[test]
    fn each_call_gets_its_own_output_on_the_left_and_raw_audio_on_the_right() {
        for (block, context, n) in SHAPES {
            let x = ramp(n);
            let mut probe = Probe::new(context);
            let mut out = vec![0.0; n];
            Chunker::new(block, context).run(&mut probe, &x, &mut out);
            let shape = format!("block {block}, context {context}, length {n}");
            let mut done = 0;
            for (input, edge) in &probe.calls {
                assert!(
                    input.len() <= block + 2 * context,
                    "{shape}: an input of {} samples",
                    input.len()
                );
                let centre = edge.centre(input.len(), context, done);
                let left = centre.start;
                let start = done - left;
                let end = done + centre.len();
                assert_eq!(
                    edge.first,
                    start == 0,
                    "{shape}: first flag at sample {done}"
                );
                assert_eq!(edge.last, end == n, "{shape}: last flag at sample {done}");
                assert_eq!(edge.padding, 0);
                assert_eq!(
                    left,
                    context.min(done),
                    "{shape}: left context at sample {done}"
                );
                if !edge.last {
                    assert_eq!(
                        input.len() - centre.end,
                        context,
                        "{shape}: right context at sample {done}"
                    );
                    assert_eq!(centre.len(), block, "{shape}: centre at sample {done}");
                }
                let behind: Vec<f64> = x[start..done].iter().map(|v| v + 1.0).collect();
                assert_eq!(
                    input[..left],
                    behind[..],
                    "{shape}: left context is the module's own output"
                );
                assert_eq!(
                    input[left..],
                    x[done..done + input.len() - left],
                    "{shape}: centre and right are raw"
                );
                done = end;
            }
            assert_eq!(done, n, "{shape}: the centres tile the file");
        }
    }

    #[test]
    fn an_empty_signal_makes_no_call() {
        let mut probe = Probe::new(4);
        Chunker::new(8, 4).run(&mut probe, &[], &mut []);
        assert!(probe.calls.is_empty());
    }

    #[test]
    fn process_whole_makes_one_call_with_both_file_ends() {
        let x = ramp(1000);
        let mut probe = Probe::new(4096);
        let mut out = vec![0.0; 1000];
        process_whole(&mut probe, &x, &mut out);
        assert_eq!(probe.calls.len(), 1);
        let (input, edge) = &probe.calls[0];
        assert_eq!(
            *edge,
            Edge {
                first: true,
                last: true,
                padding: 0
            }
        );
        assert_eq!(input, &x);
        assert_eq!(edge.centre(input.len(), 4096, 0), 0..1000);
        assert_eq!(out, x.iter().map(|v| v + 1.0).collect::<Vec<_>>());
    }

    #[test]
    fn padding_is_left_out_of_the_centre() {
        let edge = Edge {
            first: false,
            last: true,
            padding: 5,
        };
        assert_eq!(edge.centre(3 + 10 + 5, 3, 100), 3..13);
        let edge = Edge {
            first: false,
            last: false,
            padding: 0,
        };
        assert_eq!(edge.centre(3 + 10 + 3, 3, 100), 3..13);
        let edge = Edge {
            first: true,
            last: false,
            padding: 0,
        };
        assert_eq!(edge.centre(2 + 10 + 3, 3, 2), 2..12);
    }

    #[test]
    #[should_panic(expected = "latency")]
    fn the_chunker_refuses_a_module_with_latency() {
        struct Late(Probe);
        impl Module for Late {
            fn id(&self) -> &'static str {
                "late"
            }
            fn version(&self) -> &'static str {
                "0"
            }
            fn context_frames(&self) -> usize {
                self.0.context
            }
            fn latency_frames(&self) -> usize {
                1
            }
            fn process(&mut self, input: &[f64], output: &mut [f64], edge: Edge) {
                self.0.process(input, output, edge)
            }
            fn flush(&mut self, _output: &mut [f64]) -> usize {
                0
            }
            fn report(&self) -> Report {
                Report::default()
            }
        }
        let mut late = Late(Probe::new(2));
        Chunker::new(4, 2).run(&mut late, &[0.0; 10], &mut [0.0; 10]);
    }
}
