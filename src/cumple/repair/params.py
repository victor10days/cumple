"""The parameters of each repair module, checked before the compiled core sees them.

One pydantic model per module, strict about unknown keys. Their JSON schema is what the app's forms
will read, so each field carries its unit and its reason in the description.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DeclickParams(BaseModel):
    """De-click, ported from cathar: impulse clicks found against a sliding local RMS and rebuilt by AR interpolation."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(
        5.0,
        allow_inf_nan=False,
        description=(
            "Detection threshold in multiples of the local RMS, from 1 to below sqrt(window). The local RMS includes "
            "the sample tested, so no ratio exceeds sqrt(window) (8 at window 64): the detector sees only narrow "
            "clicks, and a lone low-level sample in digital silence sits exactly on the bound, so it fires there."
        ),
    )
    window: int = Field(64, ge=8, le=1024, description="Local RMS window in samples (cathar's CLI fixes 64).")
    method: Literal["ar", "cubic"] = Field(
        "ar", description="Gap filler: ar (autoregressive interpolation) or cubic (a cubic curve across the gap)."
    )
    iterations: int = Field(3, ge=1, le=10, description="AR refinement passes per gap (cathar passes 3).")

    @model_validator(mode="after")
    def _threshold_the_detector_can_reach(self) -> DeclickParams:
        bound = math.sqrt(self.window)
        if self.threshold < 1.0:
            raise ValueError(f"threshold {self.threshold:g} must be at least 1 local-RMS multiple")
        if self.threshold >= bound:
            raise ValueError(
                f"threshold {self.threshold:g} must be below sqrt(window) = {bound:g}: the local RMS includes the "
                "sample tested, so no ratio exceeds sqrt(window) and the detector would never fire"
            )
        return self


class DeclipParams(BaseModel):
    """De-clip, ported from cathar: samples at or above the threshold rebuilt by A-SPADE or a cubic curve."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(
        0.95,
        ge=1e-4,
        le=1.0,
        allow_inf_nan=False,
        description=(
            "Clip level as a linear sample value from 1e-4 to 1.0; a sample at or above it in magnitude counts as "
            "clipped. 0.95 suits a file clipped at full scale; a file clipped lower needs its own level."
        ),
    )
    method: Literal["spade", "cubic"] = Field(
        "spade",
        description=(
            "spade (A-SPADE over a 1,024-sample frame; every unclipped sample comes back unchanged) or cubic "
            "(a cubic curve across each run and 4 samples of shoulder, which rebuilds no peak)."
        ),
    )


MODULES: dict[str, type[DeclickParams] | type[DeclipParams]] = {"declick": DeclickParams, "declip": DeclipParams}
