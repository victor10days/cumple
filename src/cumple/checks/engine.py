"""Turn a profile plus a measurement into findings: what passed, what failed, why, and the fix."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from ..meters.measure import Measurement
from ..specs.schema import LoudnessRule, Profile

# Where a source is silent, these are the tool's choices. They are printed as such.
PADDING_TOLERANCE_S = 0.25  # "not permitted" still allows a few frames of black
METADATA_TOLERANCE_LU = 0.5
DC_OFFSET_WARN_DBFS = -60.0
SPEECH_ASSUMED_FRACTION = 1.0  # until the speech detector lands, treat programmes as dialogue-led
LFE_FULL_RANGE_DB = -15.0  # LFE with more high-band energy than this is carrying full-range programme


class Status(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    INFO = "info"
    SKIP = "skip"


@dataclass
class Finding:
    code: str  # rule code, matches the profile's clause keys
    status: Status
    what: str
    measured: str
    limit: str
    note: str | None = None
    clause: str | None = None
    fix: str | None = None
    value: float | None = None

    @property
    def failed(self) -> bool:
        return self.status is Status.FAIL


@dataclass
class Report:
    profile: Profile
    measurement: Measurement
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(f.failed for f in self.findings)

    @property
    def verdict(self) -> str:
        return "PASS" if self.passed else "FAIL"

    def fixes(self) -> list[str]:
        return [f.fix for f in self.findings if f.fix and f.status in (Status.FAIL, Status.WARN)]


def _db(x: float, unit: str = "") -> str:
    if x is None or not np.isfinite(x):
        return "silence" if x == -np.inf else "n/a"
    return f"{x:+.1f} {unit}".strip() if unit in ("dBTP", "dBFS", "dB") else f"{x:.1f} {unit}".strip()


def _bounds(rule: LoudnessRule) -> str:
    unit = "LKFS" if rule.method == "dialogue_gated" else "LUFS"
    if rule.target is not None and rule.tolerance is not None:
        return f"{rule.target:g} ±{rule.tolerance:g} {unit}"
    if rule.min is not None and rule.max is not None:
        return f"{rule.min:g} to {rule.max:g} {unit}"
    return f"≤ {rule.max:g} {unit}" if rule.max is not None else f"≥ {rule.min:g} {unit}"


def _in_window(value: float, rule: LoudnessRule) -> bool:
    if not np.isfinite(value):
        return False
    if rule.min is not None and value < rule.min:
        return False
    if rule.max is not None and value > rule.max:
        return False
    return True


def _gain_fix(delta: float, m: Measurement, p: Profile) -> str:
    """Say what a plain gain change would do, and whether true peak allows it."""
    tp = m.peaks.true_peak_dbtp
    after = tp + delta
    cap = p.peaks.true_peak_max
    verb = "raise" if delta > 0 else "lower"
    if cap is not None and after > cap:
        return f"{verb} by {abs(delta):.1f} dB would put the true peak at {after:+.1f} dBTP, above {cap:g} dBTP; gain alone cannot fix this, the mix needs headroom"
    return f"{verb} the whole file by {abs(delta):.1f} dB (true peak would become {after:+.1f} dBTP)"


def evaluate(profile: Profile, m: Measurement) -> Report:
    p = profile
    out: list[Finding] = []
    clause = p.clauses.get

    # ---- loudness -------------------------------------------------------------
    if p.loudness:
        speech = m.speech_fraction if m.speech_fraction is not None else SPEECH_ASSUMED_FRACTION
        if m.speech_fraction is None and any(r.when != "always" for r in p.loudness.rules):
            out.append(Finding("loudness.speech", Status.INFO, "speech share", "not measured", "switches at 15 %",
                               note="assumed dialogue-led until the speech detector lands"))

        def applicable(r: LoudnessRule) -> bool:
            if r.when == "speech_below_15pct":
                return speech < 0.15
            if r.when == "speech_at_or_above_15pct":
                return speech >= 0.15
            return True

        primary = [r for r in p.loudness.rules if r.role == "primary" and applicable(r)]
        fallback = [r for r in p.loudness.rules if r.role == "fallback" and applicable(r)]
        results: list[tuple[LoudnessRule, float, bool, str | None]] = []
        for r in primary + fallback:
            if r.method == "dialogue_gated":
                value = m.loudness.integrated_ungated if not r.gated_relative else m.loudness.integrated
                note = "approximation: full programme, BS.1770-1, no speech gate yet"
            else:
                value = m.loudness.integrated if r.gated_relative else m.loudness.integrated_ungated
                note = None
            results.append((r, value, _in_window(value, r), note))

        primary_results = [x for x in results if x[0].role == "primary"]
        policy_ok = (any(ok for _, _, ok, _ in primary_results) if p.loudness.policy == "any" else all(ok for _, _, ok, _ in primary_results)) if primary_results else False
        used_fallback = False
        if not policy_ok and fallback:
            fb = [x for x in results if x[0].role == "fallback"]
            if any(ok for _, _, ok, _ in fb):
                policy_ok, used_fallback = True, True

        for r, value, ok, note in results:
            code = "loudness.dialogue_gated" if r.method == "dialogue_gated" else "loudness.integrated"
            unit = "LKFS" if r.method == "dialogue_gated" else "LUFS"
            what = ("dialogue-gated loudness" if r.method == "dialogue_gated" else "integrated loudness") + (" (fallback)" if r.role == "fallback" else "")
            if ok:
                status = Status.PASS
            elif policy_ok:
                status = Status.INFO  # another rule carried the day
                note = (note + "; " if note else "") + ("not required: the fallback rule passed" if used_fallback and r.role == "primary" else "not required: another accepted measurement passed")
            elif r.role == "fallback":
                status = Status.INFO
            else:
                status = Status.FAIL
            fix = None
            if status is Status.FAIL:
                target = r.target if r.target is not None else ((r.min + r.max) / 2 if r.min is not None and r.max is not None else (r.max if r.max is not None else r.min))
                fix = _gain_fix(target - value, m, p) if np.isfinite(value) else "the file is effectively silent"
            if r.method == "dialogue_gated" and status is Status.PASS:
                status = Status.WARN if note else status
            out.append(Finding(code, status, what, _db(value, unit), _bounds(r) + f", {r.standard.upper().replace('BS', 'BS.')}", note=note, clause=clause(code), fix=fix, value=value))

    # ---- peaks -----------------------------------------------------------------
    tp, sp = m.peaks.true_peak_dbtp, m.peaks.sample_peak_dbfs
    if p.peaks.true_peak_max is not None:
        cap = p.peaks.true_peak_max
        ok = tp <= cap
        fix = None if ok else f"lower by {tp - cap:.1f} dB, or limit at {cap:g} dBTP and re-check loudness"
        note = None
        if ok and p.peaks.true_peak_recommended is not None and tp > p.peaks.true_peak_recommended:
            note = f"above the recommended {p.peaks.true_peak_recommended:g} dBTP; passes, but the destination's own renders may push peaks higher"
        out.append(Finding("peak.true", Status.PASS if ok else Status.FAIL, "true peak", _db(tp, "dBTP"), f"≤ {cap:g} dBTP", note=note, clause=clause("peak.true"), fix=fix, value=tp))
    if p.peaks.sample_peak_max is not None:
        cap = p.peaks.sample_peak_max
        ok = sp <= cap
        out.append(Finding("peak.sample", Status.PASS if ok else Status.FAIL, "sample peak", _db(sp, "dBFS"), f"≤ {cap:g} dBFS", clause=clause("peak.sample"), fix=None if ok else f"lower by {sp - cap:.1f} dB", value=sp))
    if m.peaks.clipped_runs:
        out.append(Finding("peak.clipping", Status.WARN, "clipping", f"{m.peaks.clipped_runs} run(s) of 3+ full-scale samples", "none expected", note="no profile forbids this outright; a run of consecutive full-scale samples is almost always a clipped stage", value=float(m.peaks.clipped_runs)))

    # ---- dynamics ----------------------------------------------------------------
    lra = m.loudness.lra
    if p.dynamics.lra_max is not None:
        ok = lra <= p.dynamics.lra_max
        out.append(Finding("dynamics.lra", Status.PASS if ok else Status.FAIL, "loudness range", f"{lra:.1f} LU", f"≤ {p.dynamics.lra_max:g} LU", clause=clause("dynamics.lra"), fix=None if ok else "reduce the dynamic range of the mix; a gain change does not alter LRA", value=lra))
    elif p.dynamics.lra_guide_max is not None:
        ok = lra <= p.dynamics.lra_guide_max
        out.append(Finding("dynamics.lra", Status.PASS if ok else Status.WARN, "loudness range", f"{lra:.1f} LU", f"guide ≤ {p.dynamics.lra_guide_max:g} LU", clause=clause("dynamics.lra"), value=lra))
    if p.dynamics.short_term_max is not None:
        v = m.loudness.short_term_max
        ok = v <= p.dynamics.short_term_max
        out.append(Finding("dynamics.short_term_max", Status.PASS if ok else Status.FAIL, "max short-term loudness", _db(v, "LUFS"), f"≤ {p.dynamics.short_term_max:g} LUFS", clause=clause("dynamics.short_term_max"), fix=None if ok else f"the loudest 3 s window is {v - p.dynamics.short_term_max:.1f} LU too loud", value=v))

    # ---- format ----------------------------------------------------------------
    f = p.format
    info = m.info
    if f.sample_rates:
        ok = m.samplerate in f.sample_rates
        out.append(Finding("format.sample_rate", Status.PASS if ok else Status.FAIL, "sample rate", f"{m.samplerate / 1000:g} kHz", ", ".join(f"{r / 1000:g} kHz" for r in f.sample_rates), clause=clause("format.sample_rate"), fix=None if ok else "resample with a high-quality converter, then re-measure", value=float(m.samplerate)))
    if f.bit_depths and info is not None:
        depth = info.bit_depth
        if info.is_float:
            ok = f.allow_float
            measured = f"{depth}-bit float"
        else:
            ok = depth in f.bit_depths
            measured = f"{depth}-bit"
        out.append(Finding("format.bit_depth", Status.PASS if ok else Status.FAIL, "bit depth", measured, ", ".join(f"{b}-bit" for b in f.bit_depths), clause=clause("format.bit_depth"), fix=None if ok else "bounce as fixed-point PCM at the required depth, with dither", value=float(depth or 0)))
    if f.channel_counts:
        ok = m.channels in f.channel_counts
        out.append(Finding("format.channels", Status.PASS if ok else Status.FAIL, "channels", str(m.channels), ", ".join(map(str, f.channel_counts)), clause=clause("format.channels"), value=float(m.channels)))
    if f.layouts:
        layout = m.layout
        candidates = {layout}
        if layout == "stereo":
            candidates.add("lt-rt")  # a stereo file may be an Lt/Rt; the file cannot tell us
        ok = bool(candidates & set(f.layouts))
        note = "a 2-channel file may be L/R or Lt/Rt; both accepted" if layout == "stereo" and "lt-rt" in f.layouts and "stereo" in f.layouts else None
        out.append(Finding("format.layout", Status.PASS if ok else Status.FAIL, "layout", layout + (f" ({', '.join(m.roles)})" if m.channels > 2 else ""), ", ".join(f.layouts), note=note, clause=clause("format.layout")))
    if f.packaging != "either":
        actual = "discrete" if m.is_package else "interleaved"
        ok = actual == f.packaging
        out.append(Finding("format.packaging", Status.PASS if ok else Status.FAIL, "packaging", actual, f.packaging, clause=clause("format.packaging"), fix=None if ok else ("split into one mono file per channel" if f.packaging == "discrete" else "interleave the channels into one file")))
    if f.containers and info is not None:
        name = {"WAV": "wav", "WAVEX": "wav", "RF64": "rf64", "W64": "rf64", "AIFF": "aiff", "AIFC": "aiff", "FLAC": "flac"}.get(info.container, info.container.lower())
        have = {name}
        if name == "wav" and info.bext:
            have.add("bwf")
        if name == "rf64":
            have.add("bwf")
        ok = bool(have & set(f.containers))
        out.append(Finding("format.container", Status.PASS if ok else Status.FAIL, "container", info.container + (" with bext" if info.bext else ""), ", ".join(f.containers), clause=clause("format.container")))
    ls = m.layout_stats
    if f.lfe_lowpass_hz is not None and "LFE" in m.roles and ls is not None:
        i = m.roles.index("LFE")
        ratio = ls.hf_ratio_db[i]
        if ls.silent(i):
            out.append(Finding("format.lfe_band", Status.INFO, "LFE content", "channel is silent", f"nothing above {f.lfe_lowpass_hz:g} Hz", note="an empty LFE passes trivially; make sure that is intended", clause=clause("format.lfe_band"), value=ratio))
        else:
            ok = ratio <= LFE_FULL_RANGE_DB
            out.append(Finding("format.lfe_band", Status.PASS if ok else Status.FAIL, "LFE content", f"{ratio:+.1f} dB of its energy above {ls.corner_hz:g} Hz", f"below {LFE_FULL_RANGE_DB:g} dB (tool default)", note=None if ok else "the LFE channel carries full-range programme; either a full-range channel sits in the LFE slot or the LFE was never low-passed", clause=clause("format.lfe_band"), fix=None if ok else f"low-pass the LFE at {f.lfe_lowpass_hz:g} Hz, or check the channel order", value=ratio))
    if f.channel_order == "smpte" and ls is not None and m.channels in (6, 8) and not m.is_package:
        expected = 3
        guess = ls.lfe_like
        if guess is None:
            out.append(Finding("format.channel_order", Status.INFO, "channel order", "no channel looks like an LFE", "L R C LFE Ls Rs (SMPTE)", note="cannot confirm the order from the audio: the LFE is empty or every channel is full-range", clause=clause("format.layout")))
        elif guess == expected:
            out.append(Finding("format.channel_order", Status.PASS, "channel order", "LFE-like channel at position 4", "L R C LFE Ls Rs (SMPTE)", clause=clause("format.layout")))
        elif guess == 5 and m.channels == 6:
            out.append(Finding("format.channel_order", Status.FAIL, "channel order", "LFE-like channel at position 6", "L R C LFE Ls Rs (SMPTE)", note="this looks like Film order (L C R Ls Rs LFE); the destination expects SMPTE order", clause=clause("format.layout"), fix="re-export with the channels in SMPTE order L R C LFE Ls Rs"))
        else:
            out.append(Finding("format.channel_order", Status.WARN, "channel order", f"LFE-like channel at position {guess + 1}", "L R C LFE Ls Rs (SMPTE)", note="the only low-frequency-only channel is not where the LFE should be; check the channel mapping", clause=clause("format.layout")))
    if ls is not None:
        silent = [r for r, i in zip(m.roles, range(m.channels)) if ls.silent(i)]
        if silent and len(silent) < m.channels:
            out.append(Finding("signal.silent_channels", Status.WARN, "silent channels", ", ".join(silent), "none expected", note="a silent channel in a multichannel deliverable is usually a routing mistake"))

    # ---- padding ---------------------------------------------------------------
    if p.padding.head_max_s is not None:
        ok = m.head_silence_s <= p.padding.head_max_s + PADDING_TOLERANCE_S
        out.append(Finding("padding.head", Status.PASS if ok else Status.FAIL, "head padding", f"{m.head_silence_s:.2f} s", f"≤ {p.padding.head_max_s:g} s", clause=clause("padding.head"), fix=None if ok else f"trim {m.head_silence_s - p.padding.head_max_s:.2f} s of leading silence", value=m.head_silence_s))
    if p.padding.tail_max_s is not None:
        ok = m.tail_silence_s <= p.padding.tail_max_s + PADDING_TOLERANCE_S
        out.append(Finding("padding.tail", Status.PASS if ok else Status.FAIL, "tail padding", f"{m.tail_silence_s:.2f} s", "none" if p.padding.tail_max_s == 0 else f"≤ {p.padding.tail_max_s:g} s", note=f"{PADDING_TOLERANCE_S:g} s of black is tolerated (tool default)" if p.padding.tail_max_s == 0 else None, clause=clause("padding.tail"), fix=None if ok else f"trim {m.tail_silence_s:.2f} s of trailing silence", value=m.tail_silence_s))
    if p.padding.head_min_s is not None:
        ok = m.head_silence_s >= p.padding.head_min_s
        out.append(Finding("padding.head_min", Status.PASS if ok else Status.FAIL, "head room tone", f"{m.head_silence_s:.2f} s", f"≥ {p.padding.head_min_s:g} s", clause=clause("padding.head_min"), value=m.head_silence_s))
    if p.padding.tail_min_s is not None:
        ok = m.tail_silence_s >= p.padding.tail_min_s
        out.append(Finding("padding.tail_min", Status.PASS if ok else Status.FAIL, "tail room tone", f"{m.tail_silence_s:.2f} s", f"≥ {p.padding.tail_min_s:g} s", clause=clause("padding.tail_min"), value=m.tail_silence_s))

    # ---- signal sanity ---------------------------------------------------------
    dc_db = 20 * np.log10(np.abs(m.dc_offset).max()) if np.abs(m.dc_offset).max() > 0 else -np.inf
    if dc_db > DC_OFFSET_WARN_DBFS:
        out.append(Finding("signal.dc_offset", Status.WARN, "DC offset", _db(dc_db, "dBFS"), f"< {DC_OFFSET_WARN_DBFS:g} dBFS (tool default)", note="a DC offset wastes headroom and thumps at edits; remove it with a high-pass around 5 Hz", value=dc_db))
    if p.checks.mono_compatibility and m.phase_correlation is not None:
        corr = m.phase_correlation
        loss = (m.loudness.integrated - m.mono_fold_loudness) if m.mono_fold_loudness is not None and np.isfinite(m.mono_fold_loudness) else None
        ok = corr >= 0.0
        measured = f"correlation {corr:+.2f}" + (f", mono fold {loss:+.1f} LU quieter" if loss is not None else "")
        out.append(Finding("mono.compat", Status.PASS if ok else Status.FAIL, "mono compatibility", measured, "correlation ≥ 0", clause=clause("mono.compat"), fix=None if ok else "check polarity of one channel or wide stereo processing; the mix cancels in mono", value=corr))
    elif m.phase_correlation is not None and m.phase_correlation < -0.2:
        out.append(Finding("mono.compat", Status.WARN, "mono compatibility", f"correlation {m.phase_correlation:+.2f}", "no rule in this profile", note="the channels are largely anti-phase; the mix will cancel in mono", value=m.phase_correlation))

    # ---- embedded metadata ------------------------------------------------------
    if p.checks.metadata_must_match:
        bext = info.bext if info is not None else {}
        raw = bext.get("loudness_value")
        if raw in (None, 0x7FFF):
            out.append(Finding("metadata.bext_loudness", Status.INFO, "embedded loudness", "none", "bext LoudnessValue", note="no loudness metadata in the file; nothing to contradict", clause=clause("metadata.bext_loudness")))
        else:
            embedded = float(raw) / 100.0 if abs(float(raw)) > 100 else float(raw)
            diff = embedded - m.loudness.integrated
            ok = abs(diff) <= METADATA_TOLERANCE_LU
            out.append(Finding("metadata.bext_loudness", Status.PASS if ok else Status.FAIL, "embedded loudness", f"bext says {embedded:.1f} LUFS, measured {m.loudness.integrated:.1f}", f"within {METADATA_TOLERANCE_LU:g} LU (tool default)", clause=clause("metadata.bext_loudness"), fix=None if ok else "re-write the bext loudness fields from the actual measurement", value=diff))

    # ---- not yet implemented rules, said out loud ---------------------------------
    if p.leqm is not None:
        out.append(Finding("leqm.level", Status.SKIP, "Leq(m)", "not measured yet", f"≤ {p.leqm.max_db:g} dB", note="the cinema meter lands in a later build", clause=clause("leqm.level")))
    if p.rms is not None:
        out.append(Finding("rms.level", Status.SKIP, "RMS level", "not measured yet", f"{p.rms.rms_min_dbfs:g} to {p.rms.rms_max_dbfs:g} dBFS", note="lands in a later build", clause=clause("rms.level")))

    return Report(profile=p, measurement=m, findings=out)
