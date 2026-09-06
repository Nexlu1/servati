#!/usr/bin/env python3
"""Enforce the small set of validation rules specific to SERVATI."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data"
V12_DATA_ROOT = DATA_ROOT / "drafts"
V12_DRAFT_ROOT = ROOT / "drafts" / "v12"
V11_INDEX = DATA_ROOT / "v11-canon-index.yaml"
PROVENANCE_POLICY = ROOT / "canon" / "PROVENANCE.md"
THIRD_PARTY_ROOT = ROOT / "third_party"
THIRD_PARTY_REGISTER = ROOT / "THIRD_PARTY.md"


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.datasets = 0
        self.entries = 0
        self.provenance_records = 0

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def finish(self) -> None:
        if self.errors:
            for error in self.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            raise SystemExit(1)
        print(
            "SERVATI policy validation: PASS "
            f"({self.datasets} datasets, {self.entries} entries, "
            f"{self.provenance_records} provenance records)"
        )


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path, validation: Validation) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        validation.errors.append(f"{relative(path)} cannot be read as JSON: {error}")
        return None


def load_yaml(path: Path, validation: Validation) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        validation.errors.append(f"{relative(path)} cannot be read as YAML: {error}")
        return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def has_absolute_chronology(entry: dict[str, Any]) -> bool:
    chronology = entry.get("servati", {}).get("chronology", {})
    for key in ("start", "end"):
        if chronology.get(key) is not None:
            return True
    nature = entry.get("Nature", {})
    return "start_date" in nature or "end_date" in nature


def validate_datasets(validation: Validation) -> None:
    dataset_paths = sorted(DATA_ROOT.rglob("*.json"))
    datasets: list[tuple[Path, dict[str, Any]]] = []
    entry_ids: dict[str, str] = {}
    servati_ids: dict[str, str] = {}
    declared_worlds: set[str] = set()

    for path in dataset_paths:
        dataset = load_json(path, validation)
        if not isinstance(dataset, dict):
            continue
        validation.datasets += 1
        datasets.append((path, dataset))
        world = dataset.get("world_reference", {}).get("Id")
        if isinstance(world, str):
            declared_worlds.add(world)
        entries = dataset.get("entries", [])
        if not isinstance(entries, list):
            validation.errors.append(f"{relative(path)} entries must be a list")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                validation.errors.append(f"{relative(path)} contains a non-object entry")
                continue
            validation.entries += 1
            entry_id = entry.get("Id")
            servati_id = entry.get("servati", {}).get("servati_id")
            if isinstance(entry_id, str):
                if entry_id in entry_ids:
                    validation.errors.append(
                        f"duplicate entry Id {entry_id} in {entry_ids[entry_id]} and {relative(path)}"
                    )
                else:
                    entry_ids[entry_id] = relative(path)
            if isinstance(servati_id, str):
                if servati_id in servati_ids:
                    validation.errors.append(
                        f"duplicate SERVATI Id {servati_id} in {servati_ids[servati_id]} "
                        f"and {relative(path)}"
                    )
                else:
                    servati_ids[servati_id] = relative(path)

    known_ids = set(entry_ids)
    for path, dataset in datasets:
        is_v12_draft = path.is_relative_to(V12_DATA_ROOT) and path.name.startswith("v12")
        if is_v12_draft:
            validation.require(
                dataset.get("canon_status") == "DRAFT",
                f"{relative(path)} must have dataset canon_status DRAFT",
            )
        for entry in dataset.get("entries", []):
            if not isinstance(entry, dict):
                continue
            label = f"{relative(path)}::{entry.get('Name', entry.get('Id', '<unknown>'))}"
            metadata = entry.get("servati", {})
            if is_v12_draft:
                validation.require(
                    metadata.get("canon_status") == "DRAFT",
                    f"{label} must remain DRAFT",
                )
                validation.require(
                    not has_absolute_chronology(entry),
                    f"{label} assigns absolute chronology inside a relative-only V12 tranche",
                )

            world = entry.get("World")
            validation.require(
                world in known_ids or world in declared_worlds,
                f"{label} references unknown World Id {world}",
            )
            references = list(entry.get("Involves", {}).get("locations", []))
            references += list(entry.get("Nature", {}).get("triggers", []))
            for target in references:
                validation.require(
                    target in known_ids,
                    f"{label} references unknown entity Id {target}",
                )

            records = metadata.get("provenance", [])
            validation.require(bool(records), f"{label} requires provenance")
            for record in records:
                if not isinstance(record, dict):
                    validation.errors.append(f"{label} has a non-object provenance record")
                    continue
                validation.provenance_records += 1
                for key in ("source_kind", "source_ref", "verification", "note"):
                    validation.require(bool(record.get(key)), f"{label} provenance lacks {key}")
                if record.get("verification") == "VERIFIED":
                    validation.require(
                        bool(record.get("source_location")),
                        f"{label} VERIFIED provenance requires source_location",
                    )
                if record.get("source_kind") == "released-manuscript":
                    source_ref = record.get("source_ref", "")
                    source_path = Path(source_ref)
                    validation.require(
                        not source_path.is_absolute()
                        and re.match(r"^[A-Za-z]:[\\/]", source_ref) is None,
                        f"{label} manuscript source_ref must be repository-relative",
                    )
                    validation.require(
                        (ROOT / source_path).is_file(),
                        f"{label} manuscript source does not exist: {source_ref}",
                    )
                    if is_v12_draft and record.get("verification") == "VERIFIED":
                        validation.require(
                            "DRAFT" in record.get("note", ""),
                            f"{label} must scope VERIFIED V11 provenance away from DRAFT details",
                        )
                if metadata.get("canon_status") == "CORE":
                    validation.require(
                        record.get("verification") != "SOURCE-UNAVAILABLE",
                        f"{label} CORE material cannot use SOURCE-UNAVAILABLE provenance",
                    )


def validate_v12_markdown(validation: Validation) -> None:
    for path in sorted(V12_DRAFT_ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        heading = next((line for line in text.splitlines() if line.startswith("# ")), "")
        validation.require("DRAFT" in heading, f"{relative(path)} heading must declare DRAFT")
        for status in re.findall(r"^- \*\*Status:\*\*\s*(.+)$", text, re.MULTILINE):
            validation.require(status.strip() == "DRAFT", f"{relative(path)} contains non-DRAFT status")


def validate_relative_chronology(validation: Validation) -> None:
    index = load_yaml(V11_INDEX, validation)
    if not isinstance(index, dict):
        return
    chronology = index.get("chronology", {})
    validation.require(
        chronology.get("precision") == "relative-order-only",
        "data/v11-canon-index.yaml chronology must remain relative-order-only",
    )
    validation.require(
        isinstance(chronology.get("items"), list)
        and chronology.get("count") == len(chronology.get("items", [])),
        "data/v11-canon-index.yaml chronology count must match its ordered items",
    )
    validation.require(
        all(isinstance(item, str) and item for item in chronology.get("items", [])),
        "data/v11-canon-index.yaml chronology items must be relative stage names",
    )
    forbidden = {"start", "end", "year", "date", "duration", "timestamp"}
    validation.require(
        not forbidden.intersection(chronology),
        "data/v11-canon-index.yaml chronology must not add absolute fields",
    )


def validate_authoritative_source(validation: Validation) -> None:
    policy = PROVENANCE_POLICY.read_text(encoding="utf-8")
    pattern = re.compile(
        r"SERVATI_V11_AUTHORITATIVE_MANUSCRIPT\.md.*?SHA-256\s+`([0-9a-f]{64})`",
        re.DOTALL,
    )
    match = pattern.search(policy)
    validation.require(match is not None, "canon/PROVENANCE.md must record the V11 manuscript hash")
    if match:
        manuscript = ROOT / "SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md"
        validation.require(manuscript.is_file(), "authoritative Version 11 manuscript is missing")
        if manuscript.is_file():
            validation.require(
                file_sha256(manuscript) == match.group(1),
                "authoritative Version 11 manuscript hash differs from canon/PROVENANCE.md",
            )


def validate_third_party(validation: Validation) -> None:
    register = THIRD_PARTY_REGISTER.read_text(encoding="utf-8")
    for directory in sorted(path for path in THIRD_PARTY_ROOT.iterdir() if path.is_dir()):
        licence = directory / "LICENSE"
        notice = directory / "NOTICE.md"
        label = relative(directory)
        validation.require(licence.is_file(), f"{label} requires LICENSE")
        validation.require(notice.is_file(), f"{label} requires NOTICE.md")
        validation.require(relative(licence) in register, f"THIRD_PARTY.md must reference {relative(licence)}")
        validation.require(relative(notice) in register, f"THIRD_PARTY.md must reference {relative(notice)}")
        if not licence.is_file() or not notice.is_file():
            continue
        notice_text = notice.read_text(encoding="utf-8")
        match = re.search(r"Licence SHA-256:\s*`([0-9a-f]{64})`", notice_text)
        validation.require(match is not None, f"{relative(notice)} must record its licence hash")
        if match:
            validation.require(
                file_sha256(licence) == match.group(1),
                f"{relative(licence)} differs from the hash in {relative(notice)}",
            )


def main() -> None:
    validation = Validation()
    validate_datasets(validation)
    validate_v12_markdown(validation)
    validate_relative_chronology(validation)
    validate_authoritative_source(validation)
    validate_third_party(validation)
    validation.finish()


if __name__ == "__main__":
    main()
