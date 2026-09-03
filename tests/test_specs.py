from __future__ import annotations

import pytest

from cumple.specs import ProfileNotFound, get, load_all
from cumple.specs.registry import builtin_dir
from cumple.specs.schema import Grade, LoudnessRule


def test_all_builtin_profiles_load():
    profiles = load_all()
    assert len(profiles) >= 5
    for path in builtin_dir().glob("*.yaml"):
        assert path.stem in profiles


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
    assert netflix.grade == Grade.SE and netflix.has_defaults
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
