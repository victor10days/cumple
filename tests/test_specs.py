from __future__ import annotations

import pytest

from cumple.specs import ProfileNotFound, get, load_all
from cumple.specs.registry import builtin_dir
from cumple.specs.schema import Grade, LoudnessRule


def test_all_builtin_profiles_load():
    profiles = load_all()
    assert len(profiles) >= 39
    for path in builtin_dir().glob("*.yaml"):
        assert path.stem in profiles


STUDIO_PROFILES = {
    # id: (grade, has_defaults)
    "disney-a85": (Grade.READ, False),
    "disney-r128": (Grade.READ, False),
    "disney-trailer": (Grade.READ, False),
    "cbs-commercial": (Grade.READ, False),
    "abc-commercial": (Grade.READ, False),
    "fox-program-2018": (Grade.READ, True),
    "fox-commercial-2024": (Grade.READ, True),
    "peacock": (Grade.COMMUNITY, True),
    "apple-immersive": (Grade.READ, True),
}


@pytest.mark.parametrize("pid", sorted(STUDIO_PROFILES))
def test_studio_profiles_quote_their_sources(pid):
    p = get(pid)
    grade, has_defaults = STUDIO_PROFILES[pid]
    assert p.clauses_verbatim
    assert p.grade == grade and p.has_defaults == has_defaults
    assert all(s.retrieved.isoformat() >= "2026-09-03" for s in p.provenance)
    assert p.loudness is not None and p.loudness.rules


def test_studio_profile_numbers_follow_the_documents():
    cbs = get("cbs-commercial").loudness.rules[0]
    assert cbs.standard == "bs1770-2" and (cbs.min, cbs.max) == (-26.0, -22.0)
    abc = get("abc-commercial")
    assert abc.loudness.rules[0].max == -23.0 and abc.peaks.true_peak_max == -6.0
    r128 = get("disney-r128")
    assert (r128.peaks.true_peak_max, r128.dynamics.short_term_max, r128.dynamics.lra_max) == (-3.0, -15.0, 20.0)
    trailer = get("disney-trailer")
    assert (trailer.padding.head_min_s, trailer.padding.head_max_s) == (1.0, 1.0)
    assert "5.1+lt-rt" in trailer.format.layouts and trailer.stems.me_must_have_no_speech
    assert get("fox-commercial-2024").peaks.sample_peak_max == -6.0
    assert get("apple-immersive").loudness.rules[0].max == -18.0


def test_prose_has_no_dashes():
    """Names, summaries, notes and titles are cumple's prose; clauses are quotes and may keep the source's characters."""
    dashes = ("–", "—")
    for p in load_all().values():
        texts = [p.name, p.summary] + [r.notes or "" for r in (p.loudness.rules if p.loudness else [])]
        texts += [s.title for s in p.provenance] + [s.notes or "" for s in p.provenance]
        for t in texts:
            assert not any(d in t for d in dashes), (p.id, t)


def test_every_profile_is_traceable():
    for p in load_all().values():
        assert p.provenance, p.id
        assert p.summary
        assert p.loudness_summary()
        assert isinstance(p.grade, Grade)
        # every clause key should look like a rule code
        for code in p.clauses:
            assert "." in code, (p.id, code)


def test_grade_follows_primary_sources_only():
    netflix = get("netflix-2.0")
    assert netflix.grade == Grade.READ and netflix.has_defaults
    assert get("max-wbd").grade == Grade.READ and not get("max-wbd").has_defaults
    apple = get("apple-tv")
    assert apple.grade == Grade.READ and apple.has_defaults
    assert get("tasa-trailer").grade == Grade.READ  # the paywalled ISO entry is supporting only


def test_unknown_profile_suggests_close_names():
    with pytest.raises(ProfileNotFound) as e:
        get("netflix-stereo")
    assert "netflix-2.0" in str(e.value)


def test_target_tolerance_becomes_bounds():
    r = LoudnessRule(target=-23.0, tolerance=1.0)
    assert (r.min, r.max) == (-24.0, -22.0)
    assert r.gated_relative
    assert not LoudnessRule(standard="bs1770-1", target=-27, tolerance=2).gated_relative


def test_rule_needs_some_bound():
    with pytest.raises(ValueError):
        LoudnessRule()
