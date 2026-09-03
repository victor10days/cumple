"""The profile schema: what a destination requires, and how we know.

A profile is data, not code. Every number in it should be traceable to a document,
and the `provenance` block says how good that trace is.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Grade(str, Enum):
    """How the numbers in a profile were obtained. Printed next to every verdict."""

    READ = "READ"  # the primary document was read directly
    SE = "SE"  # a primary page exists but is a JavaScript app; values via search extraction
    GATED = "GATED"  # partner portal or NDA; values from secondary summaries
    SECONDARY = "SECONDARY"  # taken from another standards body's summary table
    COMMUNITY = "COMMUNITY"  # the platform publishes nothing; third-party measurement
    TOOL_DEFAULT = "TOOL_DEFAULT"  # the source is silent; this is the tool's own choice


GRADE_LABEL = {
    Grade.READ: "primary document read directly",
    Grade.SE: "primary page exists (JavaScript app); values recovered via search extraction",
    Grade.GATED: "partner portal or NDA; values from secondary summaries",
    Grade.SECONDARY: "taken from another standards body's summary table",
    Grade.COMMUNITY: "platform publishes nothing; third-party measurement",
    Grade.TOOL_DEFAULT: "source is silent; the tool's own default",
}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Provenance(Strict):
    title: str
    publisher: str
    version: str | None = None
    published: str | None = None  # as printed on the document
    url: str | None = None
    retrieved: date
    grade: Grade
    role: Literal["primary", "supporting", "default"] = "primary"
    notes: str | None = None


Standard = Literal["bs1770-1", "bs1770-2", "bs1770-3", "bs1770-4", "bs1770-5"]
Method = Literal["integrated", "dialogue_gated"]
When = Literal["always", "speech_below_15pct", "speech_at_or_above_15pct"]


class LoudnessRule(Strict):
    """One way of measuring programme loudness and the window it must land in.

    Either target + tolerance, or explicit min/max. Apple publishes a range with no
    target, so min/max is the general form; target ± tolerance is sugar for it.
    """

    method: Method = "integrated"
    standard: Standard = "bs1770-4"
    target: float | None = None
    tolerance: float | None = None
    min: float | None = None
    max: float | None = None
    when: When = "always"
    role: Literal["primary", "fallback"] = "primary"
    notes: str | None = None

    @model_validator(mode="after")
    def _derive_bounds(self) -> "LoudnessRule":
        if self.target is not None and self.tolerance is not None:
            if self.min is None:
                self.min = self.target - self.tolerance
            if self.max is None:
                self.max = self.target + self.tolerance
        if self.min is None and self.max is None:
            raise ValueError("a loudness rule needs target+tolerance or min/max")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("loudness min is above max")
        return self

    @property
    def gated_relative(self) -> bool:
        """BS.1770-1 has no relative gate; -2 and later add the -10 LU gate."""
        return self.standard != "bs1770-1"

    def compact(self) -> str:
        """Short form for tables: '-27 ±2 dialogue-gated' or '-31 to -10 dialogue-gated'."""
        if self.target is not None and self.tolerance is not None:
            window = f"{self.target:g} ±{self.tolerance:g}"
        elif self.min is not None and self.max is not None:
            window = f"{self.min:g} to {self.max:g}"
        elif self.max is not None:
            window = f"≤ {self.max:g}"
        else:
            window = f"≥ {self.min:g}"
        how = "dialogue-gated" if self.method == "dialogue_gated" else "integrated"
        cond = {"always": "", "speech_below_15pct": " (speech < 15 %)", "speech_at_or_above_15pct": ""}[self.when]
        return f"{window} {how}{cond}"

    def describe(self) -> str:
        unit = "LKFS" if self.method == "dialogue_gated" else "LUFS"
        if self.target is not None and self.tolerance is not None:
            window = f"{self.target:g} ±{self.tolerance:g} {unit}"
        elif self.min is not None and self.max is not None:
            window = f"{self.min:g} to {self.max:g} {unit}"
        elif self.max is not None:
            window = f"≤ {self.max:g} {unit}"
        else:
            window = f"≥ {self.min:g} {unit}"
        how = "dialogue-gated" if self.method == "dialogue_gated" else "integrated"
        cond = {
            "always": "",
            "speech_below_15pct": ", if speech < 15 %",
            "speech_at_or_above_15pct": ", if speech ≥ 15 %",
        }[self.when]
        tail = " (fallback)" if self.role == "fallback" else ""
        return f"{window} {how}, {self.standard.upper().replace('BS', 'BS.')}{cond}{tail}"


class LoudnessPolicy(Strict):
    rules: list[LoudnessRule] = Field(min_length=1)
    policy: Literal["all", "any"] = "all"  # all applicable rules must pass, or any one


class Peaks(Strict):
    true_peak_max: float | None = None  # dBTP
    true_peak_recommended: float | None = None  # e.g. Netflix limiter at -2.3, DPP -3
    sample_peak_max: float | None = None  # dBFS, for specs that say "peak" without "true"


class Dynamics(Strict):
    lra_max: float | None = None  # LU, a hard limit
    lra_guide_max: float | None = None  # LU, guidance only
    short_term_max: float | None = None  # LUFS (EBU R 128 s1: -18)
    momentary_max: float | None = None


Layout = Literal["mono", "stereo", "lt-rt", "5.1", "7.1", "5.1+lt-rt", "atmos-adm"]
Container = Literal["wav", "bwf", "rf64", "aiff", "flac", "mxf", "mp3", "aac", "adm-bwf"]


class Format(Strict):
    sample_rates: list[int] | None = None
    bit_depths: list[int] | None = None
    channel_counts: list[int] | None = None
    layouts: list[Layout] | None = None
    channel_order: Literal["smpte", "film"] | None = None
    packaging: Literal["interleaved", "discrete", "either"] = "either"
    containers: list[Container] | None = None
    lfe_lowpass_hz: float | None = None  # LFE must carry no content above this
    allow_float: bool = False


class Padding(Strict):
    head_max_s: float | None = None
    tail_max_s: float | None = None  # 0 means not permitted
    head_min_s: float | None = None  # ACX room tone
    tail_min_s: float | None = None


class Stems(Strict):
    must_sum_to_printmaster: bool = False
    residual_max_dbfs: float | None = None  # tool default where the source is silent
    me_must_have_no_speech: bool = False


class RmsRule(Strict):
    """ACX-style level rules measured in RMS, not BS.1770."""

    rms_min_dbfs: float
    rms_max_dbfs: float
    noise_floor_max_dbfs: float | None = None


class Leqm(Strict):
    """ISO 21727 style Leq(m) for cinema trailers and ads."""

    max_db: float
    calibration_dbfs: float = -20.0
    calibration_spl_db: float = 85.0
    surround_offset_db: float = -3.0


class Checks(Strict):
    metadata_must_match: bool = False  # bext loudness fields vs measurement
    mono_compatibility: bool = False  # stereo must fold to mono
    duration_max_s: float | None = None
    av_duration_tolerance_s: float | None = None


Family = Literal["streaming", "broadcast", "cinema", "music", "podcast", "audiobook", "standard"]


class Profile(Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9.+-]*$")
    name: str
    family: Family
    summary: str
    loudness: LoudnessPolicy | None = None
    peaks: Peaks = Field(default_factory=Peaks)
    dynamics: Dynamics = Field(default_factory=Dynamics)
    format: Format = Field(default_factory=Format)
    padding: Padding = Field(default_factory=Padding)
    stems: Stems = Field(default_factory=Stems)
    rms: RmsRule | None = None
    leqm: Leqm | None = None
    checks: Checks = Field(default_factory=Checks)
    clauses: dict[str, str] = Field(default_factory=dict)  # rule code -> the source's words
    clauses_verbatim: bool = False  # True once every clause is a verbatim quote
    provenance: list[Provenance] = Field(min_length=1)

    @property
    def grade(self) -> Grade:
        """The weakest grade among the primary sources: a chain is as good as its weakest link.

        Supporting references (a paywalled standard cited for context) and the tool's own
        defaults do not lower the grade; defaults are flagged separately.
        """
        order = [Grade.READ, Grade.SE, Grade.SECONDARY, Grade.GATED, Grade.COMMUNITY, Grade.TOOL_DEFAULT]
        primary = [p.grade for p in self.provenance if p.role == "primary"]
        if not primary:
            return Grade.TOOL_DEFAULT
        return max(primary, key=order.index)

    @property
    def has_defaults(self) -> bool:
        """True when some number in this profile is the tool's choice, not the source's."""
        return any(p.role == "default" or p.grade == Grade.TOOL_DEFAULT for p in self.provenance)

    def loudness_summary(self) -> str:
        if self.loudness is None:
            if self.leqm is not None:
                return f"≤ {self.leqm.max_db:g} dB Leq(m)"
            if self.rms is not None:
                return f"{self.rms.rms_min_dbfs:g} to {self.rms.rms_max_dbfs:g} dBFS RMS"
            return "no loudness target"
        primary = [r for r in self.loudness.rules if r.role == "primary"]
        joiner = " or " if self.loudness.policy == "any" else "; "
        return joiner.join(r.describe() for r in primary)

    def loudness_compact(self) -> str:
        if self.loudness is None:
            return self.loudness_summary()
        primary = [r for r in self.loudness.rules if r.role == "primary"]
        joiner = " or " if self.loudness.policy == "any" else "; "
        return joiner.join(r.compact() for r in primary)

    def peak_summary(self) -> str:
        parts = []
        if self.peaks.true_peak_max is not None:
            parts.append(f"{self.peaks.true_peak_max:g} dBTP")
        if self.peaks.sample_peak_max is not None:
            parts.append(f"{self.peaks.sample_peak_max:g} dBFS sample")
        return ", ".join(parts) if parts else "none stated"
