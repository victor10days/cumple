# Third-party notices

cumple-dsp and its Python bindings (cumple-dsp-py, the distribution `cumple-dsp`) are MIT, as cumple is.
This file carries the notices of code ported into them and of libraries a built wheel links.

## cathar

The repair modules are ported from cathar (https://github.com/vbasky/cathar), licensed MIT OR Apache-2.0
and used here under MIT. Source commit: f2c2842f89084589d069e5a8a0b61311aa70d928.

Ported functions, each in a file whose first line names its source file and commit:

- `src/declick.rs`, from `crates/cathar/src/restore.rs`: `declick_with_method` (lines 116 to 169, the
  detector loop and the fill branches, split into `Declick::detect` and `Declick::fill`), `local_rms` (171 to
  194, with its running sum in `RunningRms`), `cubic_interpolate` (196 to 213) and the `DeclickMethod` enum.
- `src/inpaint.rs`, from `crates/cathar/src/inpaint.rs`: `inpaint_gap`, `estimate_ar_known`, `levinson`,
  `coef_autocorr`, `solve_gap` and `solve_spd_banded`, with the constants `AR_ORDER` and `MAX_SOLVE`.
  `inpaint_auto` is not ported.

`Window::HannSymmetric` in `src/stft.rs` computes the same formula as cathar's `hann_window`
(`crates/cathar/src/util.rs`) so the ports can be tested against it; it is not copied code.

```
MIT License

Copyright (c) The cathar Authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## rust-numpy

The bindings link the `numpy` crate (https://github.com/PyO3/rust-numpy), licensed BSD-2-Clause.

```
BSD 2-Clause License

Copyright (c) 2017, Toshiki Teramura
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Other Rust dependencies

Every other Rust dependency (rustfft, realfft, num-complex, num-traits, pyo3, ndarray and what they pull
in) is MIT or Apache-2.0, except two used only while building: unicode-ident (through syn) is also under
Unicode-3.0, and target-lexicon (through pyo3-build-config) is Apache-2.0 WITH LLVM-exception.
`cargo deny check licenses` (`deny.toml` at the repository root) holds the tree to that list.
