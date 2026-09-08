"""Run cumple, libebur128, pyloudnorm, ffmpeg's ebur128 filter and loudcheck on the official EBU test signals.

Run: uv run python scripts/benchmark_meters.py > docs/BENCHMARK.md
Needs the EBU Loudness Test Set unpacked under ~/.cache/cumple (or CUMPLE_EBU_TEST_SET; see
tests/test_ebu_conformance.py), ffmpeg on PATH, the libebur128 shared library (brew install
libebur128, or CUMPLE_LIBEBUR128 pointing at it) and the dev dependency group (pyloudnorm,
loudcheck). The script stops when a tool is missing: the committed report always carries all five,
because the landing page's comparison table is checked against its summary lines.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import functools
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import date
from importlib.metadata import version as dist_version
from typing import NamedTuple

import numpy as np
import pyloudnorm
import soundfile as sf

from cumple import __version__
from cumple.meters.measure import measure

ROOT = os.path.join(
    os.environ.get("CUMPLE_EBU_TEST_SET", os.path.expanduser("~/.cache/cumple")), "ebu-loudness-test-set"
)
# (file, expected I, expected TP, expected LRA) from EBU Tech 3341 Table 1 and Tech 3342.
CASES = [
    ("seq-3341-1-16bit.wav", -23.0, None, None),
    ("seq-3341-2-16bit.wav", -33.0, None, None),
    ("seq-3341-3-16bit-v02.wav", -23.0, None, None),
    ("seq-3341-4-16bit-v02.wav", -23.0, None, None),
    ("seq-3341-5-16bit-v02.wav", -23.0, None, None),
    ("seq-3341-6-5channels-16bit.wav", -23.0, None, None),
    ("seq-3341-6-6channels-WAVEEX-16bit.wav", -23.0, None, None),
    ("seq-3341-7_seq-3342-5-24bit.wav", -23.0, None, 5.0),
    ("seq-3341-2011-8_seq-3342-6-24bit-v02.wav", -23.0, None, 15.0),
    ("seq-3341-15-24bit.wav.wav", None, -6.0, None),
    ("seq-3341-16-24bit.wav.wav", None, -6.0, None),
    ("seq-3341-17-24bit.wav.wav", None, -6.0, None),
    ("seq-3341-18-24bit.wav.wav", None, -6.0, None),
    ("seq-3341-19-24bit.wav.wav", None, 3.0, None),
    ("seq-3341-20-24bit.wav.wav", None, 0.0, None),
    ("seq-3341-21-24bit.wav.wav", None, 0.0, None),
    ("seq-3341-22-24bit.wav.wav", None, 0.0, None),
    ("seq-3341-23-24bit.wav.wav", None, 0.0, None),
    ("seq-3342-1-16bit.wav", None, None, 10.0),
    ("seq-3342-2-16bit.wav", None, None, 5.0),
    ("seq-3342-3-16bit.wav", None, None, 20.0),
    ("seq-3342-4-16bit.wav", None, None, 15.0),
]
TOOLS = ("cumple", "libebur128", "pyloudnorm", "ffmpeg ebur128", "loudcheck")

# ebur128.h v1.2.6: modes and channel roles.
EBUR128_MODE_M = 1 << 0
EBUR128_MODE_S = (1 << 1) | EBUR128_MODE_M
EBUR128_MODE_I = (1 << 2) | EBUR128_MODE_M
EBUR128_MODE_LRA = (1 << 3) | EBUR128_MODE_S
EBUR128_MODE_SAMPLE_PEAK = (1 << 4) | EBUR128_MODE_M
EBUR128_MODE_TRUE_PEAK = (1 << 5) | EBUR128_MODE_M | EBUR128_MODE_SAMPLE_PEAK
MODE = EBUR128_MODE_I | EBUR128_MODE_LRA | EBUR128_MODE_TRUE_PEAK
UNUSED, LEFT, RIGHT, CENTER, LEFT_SURROUND, RIGHT_SURROUND = 0, 1, 2, 3, 4, 5
# The library's own default map, set explicitly so the report says what was measured.
CHANNEL_MAP = {
    1: (LEFT,),
    2: (LEFT, RIGHT),
    5: (LEFT, RIGHT, CENTER, LEFT_SURROUND, RIGHT_SURROUND),
    6: (LEFT, RIGHT, CENTER, UNUSED, LEFT_SURROUND, RIGHT_SURROUND),
}


class Reading(NamedTuple):
    """One tool on one file: None where the tool has no such quantity, nan where it failed."""

    i: float | None
    tp: float | None
    lra: float | None


def find_case(name: str) -> str:
    """The file's path under ROOT, accepting the doubled and the single .wav spelling of v5.0."""
    twin = name.removesuffix(".wav") if name.endswith(".wav.wav") else name + ".wav"
    for candidate in (name, twin):
        hits = glob.glob(os.path.join(glob.escape(ROOT), "**", candidate), recursive=True)
        if hits:
            return hits[0]
    sys.exit(f"{name}: not found under {ROOT}; unpack the EBU Loudness Test Set v5.0 there")


def cumple_reading(path: str) -> Reading:
    m = measure(path)
    return Reading(m.loudness.integrated, m.peaks.true_peak_dbtp, m.loudness.lra)


def ffmpeg_reading(path: str) -> Reading:
    out = subprocess.run(
        ["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    ).stderr
    tail = out.split("Summary:")[-1]

    def grab(pattern: str) -> float:
        m = re.search(pattern, tail)
        return float(m.group(1)) if m else float("nan")

    return Reading(grab(r"I:\s+(-?[\d.]+) LUFS"), grab(r"Peak:\s+(-?[\d.]+) dBFS"), grab(r"LRA:\s+(-?[\d.]+) LU"))


def pyloudnorm_reading(path: str) -> Reading:
    """Integrated loudness and loudness range from pyloudnorm; it has no true peak.

    pyloudnorm takes at most five channels in L R C Ls Rs order, so a six-channel
    L R C LFE Ls Rs file has its LFE removed first (BS.1770 excludes it anyway).
    """
    data, rate = sf.read(path, always_2d=True, dtype="float64")
    if data.shape[1] == 6:
        data = np.delete(data, 3, axis=1)
    meter = pyloudnorm.Meter(rate)
    integrated = float(meter.integrated_loudness(data))
    lra = float(meter.loudness_range(data))
    return Reading(integrated, None, lra)


def load_libebur128() -> ctypes.CDLL:
    candidates = [os.environ.get("CUMPLE_LIBEBUR128"), ctypes.util.find_library("ebur128")]
    try:
        prefix = subprocess.run(["brew", "--prefix", "libebur128"], capture_output=True, text=True).stdout.strip()
    except OSError:
        prefix = ""
    if prefix:  # brew prints a prefix for an uninstalled formula too, so the file check below is the real test
        candidates += [os.path.join(prefix, "lib", f"libebur128.{ext}") for ext in ("dylib", "so")]
    path = next((c for c in candidates if c and os.path.exists(c)), None)
    if path is None:
        sys.exit("libebur128 not found: brew install libebur128, or set CUMPLE_LIBEBUR128 to the shared library")
    lib = ctypes.CDLL(path)
    double_p = ctypes.POINTER(ctypes.c_double)
    lib.ebur128_init.argtypes = [ctypes.c_uint, ctypes.c_ulong, ctypes.c_int]
    lib.ebur128_init.restype = ctypes.c_void_p
    lib.ebur128_destroy.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    lib.ebur128_destroy.restype = None
    lib.ebur128_set_channel.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int]
    lib.ebur128_set_channel.restype = ctypes.c_int
    lib.ebur128_add_frames_double.argtypes = [ctypes.c_void_p, double_p, ctypes.c_size_t]
    lib.ebur128_add_frames_double.restype = ctypes.c_int
    for name in ("ebur128_loudness_global", "ebur128_loudness_range"):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.c_void_p, double_p]
        fn.restype = ctypes.c_int
    lib.ebur128_true_peak.argtypes = [ctypes.c_void_p, ctypes.c_uint, double_p]
    lib.ebur128_true_peak.restype = ctypes.c_int
    lib.ebur128_get_version.argtypes = [ctypes.POINTER(ctypes.c_int)] * 3
    lib.ebur128_get_version.restype = None
    return lib


def libebur128_version(lib: ctypes.CDLL) -> str:
    parts = [ctypes.c_int() for _ in range(3)]
    lib.ebur128_get_version(*(ctypes.byref(p) for p in parts))
    return ".".join(str(p.value) for p in parts)


def _ok(code: int, call: str) -> None:
    if code != 0:
        raise RuntimeError(f"libebur128 {call} returned error {code}")


def libebur128_reading(path: str, lib: ctypes.CDLL) -> Reading:
    """The reference library, fed in blocks like cumple's own meter; true peak over every channel."""
    info = sf.info(path)
    state = lib.ebur128_init(info.channels, info.samplerate, MODE)
    if not state:
        raise MemoryError("ebur128_init returned NULL")
    try:
        for index, role in enumerate(CHANNEL_MAP.get(info.channels, ())):
            _ok(lib.ebur128_set_channel(state, index, role), "set_channel")
        for block in sf.blocks(path, blocksize=4 * info.samplerate, always_2d=True, dtype="float64"):
            block = np.ascontiguousarray(block)
            frames = block.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            _ok(lib.ebur128_add_frames_double(state, frames, block.shape[0]), "add_frames_double")
        out = ctypes.c_double()
        _ok(lib.ebur128_loudness_global(state, ctypes.byref(out)), "loudness_global")
        integrated = out.value
        _ok(lib.ebur128_loudness_range(state, ctypes.byref(out)), "loudness_range")
        lra = out.value
        peak = 0.0
        for index in range(info.channels):
            _ok(lib.ebur128_true_peak(state, index, ctypes.byref(out)), "true_peak")
            peak = max(peak, out.value)
    finally:
        handle = ctypes.c_void_p(state)
        lib.ebur128_destroy(ctypes.byref(handle))
    return Reading(integrated, 20 * math.log10(peak) if peak > 0 else float("-inf"), lra)


def find_loudcheck() -> str:
    exe = shutil.which("loudcheck") or os.path.join(os.path.dirname(sys.executable), "loudcheck")
    if not os.path.exists(exe):
        sys.exit("loudcheck not found: uv sync --group dev, then run this script with uv run")
    return exe


def loudcheck_reading(path: str, exe: str) -> Reading:
    """loudcheck in measurement-only mode; exit 2 is an error, 0 and 1 carry readings."""
    run = subprocess.run([exe, path, "--standard", "BS_1770", "--json"], capture_output=True, text=True)
    if run.returncode == 2:
        print(f"loudcheck failed on {os.path.basename(path)}: {run.stderr.strip()}", file=sys.stderr)
        return Reading(float("nan"), float("nan"), float("nan"))
    metrics = json.loads(run.stdout)["metrics"]
    return Reading(metrics["integrated"]["measured"], metrics["true_peak"]["measured"], metrics["lra"]["measured"])


def within(x: float | None, expected: float | None, kind: str) -> bool | None:
    """kind: I (±0.1 LU), TP (+0.2/−0.4 dBTP per Tech 3341), LRA (±1 LU per Tech 3342); None = no expectation."""
    if x is None or expected is None:
        return None
    if kind == "TP":
        return expected - 0.4 <= x <= expected + 0.2
    if kind == "LRA":
        return abs(x - expected) <= 1.0
    return abs(x - expected) <= 0.1


def fmt(x: float | None, expected: float | None, kind: str) -> str:
    if x is None:
        return ""
    s = "nan" if math.isnan(x) else f"{x:.2f}"
    ok = within(x, expected, kind)
    if ok is None:
        return s
    return s + (" ✓" if ok else " ✗")


def print_table(
    title: str,
    field: str,
    kind: str,
    tools: tuple[str, ...],
    results: dict[str, dict[str, Reading]],
    tally: dict[str, list[int]],
) -> None:
    print(f"## {title}\n")
    print(f"| file | expected {kind} | " + " | ".join(tools) + " |")
    print("|---" * (2 + len(tools)) + "|")
    for name, ei, etp, elra in CASES:
        expected = {"i": ei, "tp": etp, "lra": elra}[field]
        cells = []
        for tool in tools:
            x = getattr(results[name][tool], field)
            cells.append(fmt(x, expected, kind))
            ok = within(x, expected, kind)
            if ok is not None:
                tally[tool][1] += 1
                tally[tool][0] += int(ok)
        shown = "" if expected is None else (f"{expected:+g}" if kind == "TP" else f"{expected:g}")
        print(f"| {name} | {shown} | " + " | ".join(cells) + " |")
    print()


def main() -> None:
    lib = load_libebur128()
    exe = find_loudcheck()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    ff = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
    readers: dict[str, Callable[[str], Reading]] = {
        "cumple": cumple_reading,
        "libebur128": functools.partial(libebur128_reading, lib=lib),
        "pyloudnorm": pyloudnorm_reading,
        "ffmpeg ebur128": ffmpeg_reading,
        "loudcheck": functools.partial(loudcheck_reading, exe=exe),
    }
    results: dict[str, dict[str, Reading]] = {}
    for name, *_ in CASES:
        path = find_case(name)
        results[name] = {tool: readers[tool](path) for tool in TOOLS}

    print("# cumple against libebur128, pyloudnorm, ffmpeg ebur128 and loudcheck on the EBU Loudness Test Set v5.0\n")
    print(
        f"Generated {date.today().isoformat()} with cumple {__version__}, libebur128 {libebur128_version(lib)}, "
        f"pyloudnorm {dist_version('pyloudnorm')}, `{ff}` and loudcheck {dist_version('loudcheck')}. "
        "Expected values from EBU Tech 3341 Table 1 (±0.1 LU; true peak +0.2/−0.4 dBTP) and Tech 3342 (±1 LU). "
        "✓ means inside the published tolerance, ✗ outside; a value without a mark has no expectation on that file. "
        "Every tool ran once on every file on the same machine. pyloudnorm has no true peak, so it is absent from "
        "that table. loudcheck's readings are ffmpeg's loudnorm filter as loudcheck runs it: loudness and range at "
        "192 kHz, true peak as the sample peak after resampling to 192 kHz, two decimals.\n"
    )
    tally = {tool: [0, 0] for tool in TOOLS}
    print_table("Integrated loudness, LUFS", "i", "I", TOOLS, results, tally)
    print_table("True peak, dBTP", "tp", "TP", tuple(t for t in TOOLS if t != "pyloudnorm"), results, tally)
    print_table("Loudness range, LU", "lra", "LRA", TOOLS, results, tally)
    print("## Readings inside tolerance\n")
    for tool in TOOLS:
        inside, total = tally[tool]
        print(f"**{tool}: {inside} of {total} readings inside tolerance**\n")
    print(
        "Notes: ffmpeg's ebur128 is an independent implementation with no published conformance report. "
        "On the five- and six-channel case 6 files it reports a true peak of −28 dBFS where the centre channel "
        "sits at −24 dBFS; cumple, libebur128 and loudcheck report the centre channel. "
        "On the true-peak burst files ffmpeg reports a loudness range of about 20 LU, and pyloudnorm 2.7 LU, for "
        "what is a single steady tone; those files carry no LRA expectation in Tech 3342, so this is noted, not "
        "scored. loudcheck reads case 5 at −23.14 LUFS, 0.04 LU outside the tolerance, where ffmpeg's own "
        "ebur128 filter reads −23.00 on the same file; loudnorm measures after resampling to 192 kHz, and the "
        "cause was not traced further. "
        "pyloudnorm reads the whole file into memory and takes at most five channels, so the six-channel case 6 "
        "file was passed to it without its LFE channel; the other tools read the file as delivered. "
        "libebur128 was called through ctypes on its Homebrew build with the channel map L R C Ls Rs for the "
        "five-channel file and L R C unused Ls Rs for the six-channel one, which is the library's own default; "
        "its header calls the true-peak algorithm implementation defined."
    )
    print("\nSpeed and memory on long programmes are in [PERF.md](PERF.md).")


if __name__ == "__main__":
    main()
