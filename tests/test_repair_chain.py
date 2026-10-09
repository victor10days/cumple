"""Repair chains: the one-line form, the YAML form, the presets and where they are read from. No core needed."""

from __future__ import annotations

from pathlib import Path

import pytest

from cumple.repair import chain, params

BUILT_INS = {"declick", "declip", "declick-declip"}


@pytest.fixture
def config_home(tmp_path, monkeypatch) -> Path:
    """An empty XDG_CONFIG_HOME, so no preset of the machine running the tests is read."""
    home = tmp_path / "config"
    home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home))
    return home


def write_preset(folder: Path, name: str, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


DECLICK_AT_6 = """id: declick
summary: A gentler click preset kept by the user.
steps:
  - module: declick
    params: { threshold: 6.0 }
"""


def test_parse_reads_each_step_with_its_parameters():
    c = chain.parse("declick(threshold=6),declip()")
    assert [s.module for s in c.steps] == ["declick", "declip"]
    assert c.steps[0].params == params.DeclickParams(threshold=6.0)
    assert c.steps[0].params.window == 64 and c.steps[0].params.method == "ar"
    assert c.steps[1].params == params.DeclipParams()
    assert c.steps[1].params.threshold == 0.95
    # whitespace is free anywhere between tokens
    spaced = chain.parse(" declick( threshold = 6 , window=64 ) , declip ( ) ")
    assert spaced.steps == c.steps


def test_parse_names_a_parameter_the_module_does_not_have():
    with pytest.raises(ValueError, match="foo"):
        chain.parse("declick(foo=1)")
    with pytest.raises(ValueError, match="window"):
        chain.parse("declip(window=64)")  # a De-click parameter given to De-clip


def test_the_declick_threshold_is_held_below_sqrt_window():
    """The local RMS includes the sample tested, so no ratio exceeds sqrt(window): 8 at window 64."""
    with pytest.raises(ValueError, match=r"sqrt\(window\)"):
        chain.parse("declick(threshold=9)")
    with pytest.raises(ValueError, match=r"sqrt\(window\) = 8"):
        params.DeclickParams(threshold=8.0)  # the bound itself never fires either
    with pytest.raises(ValueError, match="at least 1"):
        params.DeclickParams(threshold=0.5)
    with pytest.raises(ValueError):
        params.DeclickParams(threshold=float("nan"))
    assert params.DeclickParams(threshold=7.99).threshold == 7.99
    assert params.DeclickParams(threshold=9.0, window=128).threshold == 9.0  # sqrt(128) = 11.3
    for bad in ("window=4", "window=2048", "iterations=0", "iterations=11", "method=spline"):
        with pytest.raises(ValueError):
            chain.parse(f"declick({bad})")


def test_the_declip_threshold_is_a_sample_value_up_to_full_scale():
    assert chain.parse("declip(threshold=1e-4)").steps[0].params.threshold == 1e-4
    for bad in ("threshold=0", "threshold=1.5", "threshold=nan", "method=omp"):
        with pytest.raises(ValueError):
            chain.parse(f"declip({bad})")


def test_parse_refuses_an_unknown_module_and_text_that_is_not_a_chain():
    with pytest.raises(ValueError, match="dehum"):
        chain.parse("declick(),dehum()")
    for bad in ("", "declick", "declick(threshold)", "declick(),", "declick(threshold=5,threshold=6)", "declick()x"):
        with pytest.raises(ValueError):
            chain.parse(bad)


def test_dump_round_trips_through_load_and_the_line_form_through_parse(tmp_path):
    for text in ("declick(threshold=6),declip()", "declip(threshold=0.3,method=cubic)", "declick(window=128)"):
        c = chain.parse(text)
        path = tmp_path / "chain.yaml"
        path.write_text(chain.dump(c), encoding="utf-8")
        assert chain.load(path) == c
        assert chain.parse(c.text()).steps == c.steps


def test_a_preset_with_an_unknown_key_fails_to_load_naming_the_key(tmp_path):
    bad_param = write_preset(tmp_path, "a.yaml", DECLICK_AT_6.replace("threshold: 6.0", "threshold: 6.0, bogus: 1"))
    with pytest.raises(ValueError, match="bogus"):
        chain.load(bad_param)
    bad_top = write_preset(tmp_path, "b.yaml", DECLICK_AT_6 + "colour: red\n")
    with pytest.raises(ValueError, match="colour"):
        chain.load(bad_top)
    bad_module = write_preset(tmp_path, "c.yaml", DECLICK_AT_6.replace("module: declick", "module: dehum"))
    with pytest.raises(ValueError, match="module"):
        chain.load(bad_module)


def test_the_three_built_in_presets_load(config_home):
    found = chain.presets()
    assert set(found) == BUILT_INS
    both = found["declick-declip"]
    assert [s.module for s in both.steps] == ["declick", "declip"]
    assert both.steps[0].params == params.DeclickParams(threshold=5.0, window=64, method="ar", iterations=3)
    assert both.steps[1].params == params.DeclipParams(threshold=0.95, method="spade")
    assert all(c.summary for c in found.values())
    assert chain.resolve("declick-declip") == both
    assert chain.resolve("declick(threshold=6)").steps[0].params.threshold == 6.0
    with pytest.raises(ValueError, match="declick"):
        chain.resolve("declik")  # close enough to suggest the real one


def test_a_user_preset_overrides_the_built_in_with_its_id(config_home):
    assert chain.user_repair_dir() == config_home / "cumple" / "repair"
    write_preset(config_home / "cumple" / "repair", "declick.yaml", DECLICK_AT_6)
    found = chain.presets()
    assert set(found) == BUILT_INS
    assert found["declick"].steps[0].params.threshold == 6.0
    assert chain.resolve("declick").steps[0].params.threshold == 6.0
    write_preset(config_home / "cumple" / "repair", "gentle.yaml", DECLICK_AT_6)  # the id must match the name
    with pytest.raises(ValueError, match="gentle.yaml"):
        chain.presets()


def test_the_user_folder_defaults_to_dot_config(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert chain.user_repair_dir() == Path.home() / ".config" / "cumple" / "repair"


def test_the_profiles_folder_is_not_read_as_repair_presets(config_home):
    write_preset(config_home / "cumple" / "profiles", "declick.yaml", DECLICK_AT_6)
    write_preset(config_home / "cumple" / "profiles", "extra.yaml", DECLICK_AT_6.replace("id: declick", "id: extra"))
    found = chain.presets()
    assert set(found) == BUILT_INS
    assert found["declick"].steps[0].params.threshold == 5.0
