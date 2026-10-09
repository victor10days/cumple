"""Repair chains: the modules to run, in order, with their parameters.

Two forms carry the same chain. The one-line form is for the command line:
`declick(threshold=5),declip(threshold=0.95)`, steps separated by commas, each `name(key=value, ...)`,
whitespace free anywhere between tokens, values read by the parameter models. The YAML form is for
presets, strict like the profiles: an unknown key fails to load. Built-in presets live beside this file
in `presets/`; a user's live in `$XDG_CONFIG_HOME/cumple/repair/` (default `~/.config/cumple/repair/`),
and one overrides a built-in with the same id.
"""

from __future__ import annotations

import difflib
import os
import re
from importlib import resources
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, ValidationInfo, field_validator

from .params import MODULES, DeclickParams, DeclipParams


def explain(e: ValidationError) -> str:
    """A pydantic error as one line: each problem's location (the key at fault) and what is wrong."""
    parts = []
    for err in e.errors():
        where = ".".join(str(p) for p in err["loc"])
        what = err["msg"].removeprefix("Value error, ")
        parts.append(f"{where}: {what}" if where else what)
    return "; ".join(parts)


class ChainStep(BaseModel):
    """One module of a chain and its parameters, checked by that module's own model."""

    model_config = ConfigDict(extra="forbid")

    module: Literal["declick", "declip"]
    params: DeclickParams | DeclipParams = Field(default_factory=dict, validate_default=True)

    @field_validator("params", mode="wrap")
    @classmethod
    def _params_of_the_module(cls, value: Any, handler, info: ValidationInfo) -> Any:
        # The module, not the union, picks the model (a wrap validator keeps the union in the JSON schema);
        # another module's model is refused by model_validate itself.
        model = MODULES.get(info.data.get("module"))
        if model is None:  # the module itself failed; its error is the one to read
            return value
        return model.model_validate(value)

    def text(self) -> str:
        """The step in the one-line form, every parameter spelled out."""
        args = ",".join(f"{k}={v}" for k, v in self.params.model_dump().items())
        return f"{self.module}({args})"


class Chain(BaseModel):
    """Modules run in order over a file; each one's output is the next one's input."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field("custom", min_length=1)
    summary: str = ""
    steps: list[ChainStep] = Field(min_length=1)

    def text(self) -> str:
        """The chain in the one-line form, which `parse` reads back to the same steps."""
        return ",".join(step.text() for step in self.steps)


_STEP = re.compile(r"\s*([A-Za-z_][\w-]*)\s*\(([^()]*)\)\s*(,|\Z)")
_ARG = re.compile(r"\s*([A-Za-z_]\w*)\s*=\s*(\S(?:.*\S)?)\s*")


def parse(text: str) -> Chain:
    """Read the one-line form. Raises ValueError naming the step and the key at fault."""
    if not text.strip():
        raise ValueError("an empty chain: give steps such as declick(),declip(threshold=0.95)")
    steps: list[ChainStep] = []
    pos = 0
    while pos < len(text):
        m = _STEP.match(text, pos)
        if m is None:
            raise ValueError(
                f"cannot read the chain from {text[pos:].strip()!r}: write each step as name(key=value, ...) "
                "and separate steps with commas, such as declick(threshold=5),declip()"
            )
        name, args, comma = m.groups()
        pos = m.end()
        if comma and not text[pos:].strip():
            raise ValueError(f"the chain {text!r} ends with a comma; a step must follow it")
        if name not in MODULES:
            raise ValueError(f"unknown module {name!r} in the chain; the modules are {', '.join(MODULES)}")
        kwargs: dict[str, str] = {}
        for arg in args.split(",") if args.strip() else []:
            a = _ARG.fullmatch(arg)
            if a is None:
                raise ValueError(f"{name}: cannot read {arg.strip()!r}; write each parameter as key=value")
            key, value = a.groups()
            if key in kwargs:
                raise ValueError(f"{name}: {key} is given twice")
            kwargs[key] = value
        model = MODULES[name]
        try:
            steps.append(ChainStep(module=name, params=model.model_validate(kwargs)))
        except ValidationError as e:
            unknown = any(err["type"] == "extra_forbidden" for err in e.errors())
            hint = f" ({name} takes {', '.join(model.model_fields)})" if unknown else ""
            raise ValueError(f"{name}: {explain(e)}{hint}") from None
    return Chain(steps=steps)


def load(path: str | Path) -> Chain:
    """Read the YAML form. Raises ValueError naming the file and the key at fault."""
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Chain.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"{path.name}: {explain(e)}") from None
    except yaml.YAMLError as e:
        raise ValueError(f"{path.name}: not YAML: {e}") from None


def dump(chain: Chain) -> str:
    """The chain in the YAML form, which `load` reads back to the same chain."""
    return yaml.safe_dump(chain.model_dump(mode="json"), sort_keys=False, allow_unicode=True)


def builtin_dir() -> Path:
    return Path(str(resources.files("cumple.repair") / "presets"))


def user_repair_dir() -> Path:
    """`$XDG_CONFIG_HOME/cumple/repair`, by the rule of specs/registry.py's user_dir(), which names the profiles."""
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "cumple" / "repair"


def presets() -> dict[str, Chain]:
    """Every preset by id: the built-ins, then the user's, which override a built-in with the same id."""
    found: dict[str, Chain] = {}
    folders = [builtin_dir()]
    if user_repair_dir().is_dir():
        folders.append(user_repair_dir())
    for folder in folders:
        for path in sorted(folder.glob("*.yaml")):
            chain = load(path)
            if chain.id != path.stem:
                raise ValueError(f"{path.name}: id '{chain.id}' does not match the file name")
            found[chain.id] = chain
    return found


def resolve(text_or_id: str) -> Chain:
    """A chain in the one-line form (anything with a parenthesis), or else a preset id."""
    if "(" in text_or_id:
        return parse(text_or_id)
    found = presets()
    if text_or_id in found:
        return found[text_or_id]
    close = difflib.get_close_matches(text_or_id, list(found), n=3, cutoff=0.4)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    raise ValueError(f"no preset named '{text_or_id}'.{hint} The presets are {', '.join(sorted(found))}.")
