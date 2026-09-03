"""Find and load profiles: the built-in set, plus any the user keeps in ~/.config/cumple/profiles."""

from __future__ import annotations

import difflib
import os
from functools import lru_cache
from importlib import resources
from pathlib import Path

import yaml

from .schema import Profile


class ProfileNotFound(KeyError):
    def __init__(self, profile_id: str, candidates: list[str]):
        self.profile_id = profile_id
        self.candidates = candidates
        hint = f" Did you mean: {', '.join(candidates)}?" if candidates else ""
        super().__init__(f"no profile named '{profile_id}'.{hint}")


def builtin_dir() -> Path:
    return Path(str(resources.files("cumple.specs") / "profiles"))


def user_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "cumple" / "profiles"


def _load_file(path: Path) -> Profile:
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    try:
        profile = Profile.model_validate(raw)
    except Exception as e:  # re-raise with the file name so a bad YAML is easy to find
        raise ValueError(f"{path.name}: {e}") from e
    if profile.id != path.stem:
        raise ValueError(f"{path.name}: id '{profile.id}' does not match the file name")
    return profile


@lru_cache(maxsize=1)
def load_all() -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    dirs = [builtin_dir()]
    if user_dir().is_dir():
        dirs.append(user_dir())
    for d in dirs:
        for path in sorted(d.glob("*.yaml")):
            profile = _load_file(path)
            profiles[profile.id] = profile  # user profiles override built-ins by id
    return profiles


def profile_ids() -> list[str]:
    return sorted(load_all())


def get(profile_id: str) -> Profile:
    profiles = load_all()
    if profile_id in profiles:
        return profiles[profile_id]
    candidates = difflib.get_close_matches(profile_id, list(profiles), n=3, cutoff=0.4)
    raise ProfileNotFound(profile_id, candidates)
