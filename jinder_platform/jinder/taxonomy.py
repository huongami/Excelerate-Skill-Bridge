"""The ICT taxonomy: the one list of names of the product (V2_PLAN.md, section 4.2).

The file is `jinder_backend_engine/data/reference/ict_taxonomy.json`. The formulas (`engine_common.py`) and the CV reader
(`cv_lexicon.py`) load the same file. This module is for the platform: the pick-lists, the skill patterns, the translation library,
the seed data and the checks of the values that users send.

The file is read once. If it is missing or it is not valid JSON, `get()` raises `TaxonomyError` with a plain message.
Names are case-sensitive. Use the canonical names. An alias is only for reading text (a CV, a job ad).
"""
import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config


class TaxonomyError(RuntimeError):
    """The taxonomy file cannot be used."""


class Taxonomy:
    """The taxonomy as lists and dictionaries that the platform needs."""

    def __init__(self, data: Dict[str, Any], path: Path):
        self.path = path
        self.data = data
        self.levels: List[str] = [x["name"] for x in sorted(data["levels"], key=lambda x: x["rank"])]
        self.skill_levels: Dict[int, str] = {int(x["level"]): x["label"] for x in data["skillLevels"]}
        self.domains: List[str] = [d["name"] for d in data["domains"]]
        self.specialisations: Dict[str, List[str]] = {d["name"]: list(d["specialisations"]) for d in data["domains"]}
        self.all_specialisations: List[str] = [s for d in self.domains for s in self.specialisations[d]]
        self.skill_groups: Dict[str, str] = {k: v["label"] for k, v in data["skillGroups"].items()}
        self.skills: List[Dict[str, Any]] = list(data["skills"])
        self.skill_by_name: Dict[str, Dict[str, Any]] = {s["name"]: s for s in self.skills}
        self.occupations: Dict[str, Dict[str, Any]] = {str(o["code"]): o for o in data["occupations"]}
        self.certifications: List[Dict[str, Any]] = list(data["certifications"])
        self.certification_names: List[str] = [c["name"] for c in self.certifications]
        self.award_kinds: List[str] = [a["kind"] for a in data["awardKinds"]]
        self.award_labels: Dict[str, str] = {a["kind"]: a["label"] for a in data["awardKinds"]}
        self.roles: List[Dict[str, Any]] = list(data["roles"])
        self.role_titles: List[str] = [r["title"] for r in self.roles]
        self.role_by_title: Dict[str, Dict[str, Any]] = {r["title"].lower(): r for r in self.roles}
        self.fields_of_study: List[str] = list(data["fieldsOfStudy"])
        self.cities: List[str] = list(data["cities"])
        self.work_modes: List[str] = list(data["workModes"])
        self.work_types: List[str] = list(data["workTypes"])

    # ----- skills -----
    def skill(self, name: str) -> Optional[Dict[str, Any]]:
        return self.skill_by_name.get(name)

    def kind_of(self, name: str) -> str:
        """hard, method or soft. A name that is not in the taxonomy counts as hard."""
        s = self.skill_by_name.get(name)
        return s["kind"] if s else "hard"

    # ----- occupations and roles -----
    def occupation_of_role(self, title: str) -> Optional[Dict[str, Any]]:
        """The occupation (code, title ...) of a role of the pick-list, or None."""
        role = self.role_by_title.get(str(title or "").strip().lower())
        return self.occupations.get(str(role["occupationCode"])) if role else None

    def role_title(self, text: str) -> Optional[str]:
        """The pick-list spelling of a role title, or None."""
        role = self.role_by_title.get(str(text or "").strip().lower())
        return role["title"] if role else None


_lock = threading.Lock()
_cache: Dict[str, Taxonomy] = {}


def get() -> Taxonomy:
    """The taxonomy of the platform. It is read once (and again if the path in the config changes)."""
    path = Path(config.TAXONOMY_PATH)
    key = str(path)
    found = _cache.get(key)
    if found is not None:
        return found
    with _lock:
        found = _cache.get(key)
        if found is not None:
            return found
        if not path.is_file():
            raise TaxonomyError(
                f"The taxonomy file was not found: {path}\n"
                "It holds the names of skills, roles, certifications and domains. Set JINDER_TAXONOMY_PATH to the file ict_taxonomy.json, "
                "or JINDER_DATA_DIR to the data folder of jinder_backend_engine.")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            tax = Taxonomy(data, path)
        except (ValueError, KeyError, TypeError) as exc:
            raise TaxonomyError(f"The taxonomy file is not valid: {path} ({type(exc).__name__}: {exc}). Run validate_taxonomy.py to find the problem.") from exc
        _cache.clear()
        _cache[key] = tax
        return tax
