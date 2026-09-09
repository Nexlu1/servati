#!/usr/bin/env python3
"""Build the structured Tranches 05-08 dataset from the preserved source."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REL = "sources/v12/SERVATI_V12_PARTICULARISATION_TRANCHES_05_08_AUTHORITATIVE_DRAFT.md"
SOURCE = ROOT / SOURCE_REL
OUTPUT = ROOT / "data/drafts/v12-particularisation-tranches-05-08.json"
SOURCE_SHA256 = "efd87f65a33cfaf560fcf0d239f8c6fa2ebddc754c8e6cf6a3c19346ff5505f0"
WORLD_REFERENCE = "01a07765-3d73-7945-accf-bb285edefe4d"
UUID7_TIMESTAMP_MS = 1788912000000  # 2026-09-09 UTC, the local ingestion date.


@dataclass(frozen=True)
class WorldSpec:
    key: str
    name: str
    logic: str
    choir: str
    preservation_problem: str
    t5_range: tuple[int, int]
    t6_range: tuple[int, int]
    t7_range: tuple[int, int]
    t8_range: tuple[int, int]


WORLDS = (
    WorldSpec("k11", "Low Receiving World K-11", "Remains", "The Low Concordance", "Weight must remain traceable", (15, 31), (123, 138), (260, 279), (412, 433)),
    WorldSpec("paired", "Paired Index Basins", "Memory", "The Counterarchive", "Difference protects evidence", (33, 49), (140, 158), (281, 300), (435, 458)),
    WorldSpec("reserve", "Reserve World Thirty-One-Outer", "Seed", "The Unopened Chorus", "Readiness does not create authority", (51, 67), (160, 178), (302, 321), (460, 485)),
    WorldSpec("meridian", "Long Bell Meridian", "Ritual", "The Processional Measure", "Absence can be preserved", (69, 84), (180, 197), (323, 342), (487, 512)),
    WorldSpec("approaches", "World of Seven Approaches", "Structure", "The Threshold Assembly", "Presence does not equal recognised entry", (86, 102), (199, 214), (344, 363), (514, 539)),
    WorldSpec("sea", "Detuned Sea", "Pattern", "The Divergent Harmonic", "Variation protects independent witness", (104, 119), (216, 233), (365, 384), (541, 566)),
)

# Each tuple is (world key, source line, structured supertype).
NAMED_RECORDS = (
    ("k11", 16, "Agent"), ("k11", 18, "Institution"), ("k11", 20, "Object"), ("k11", 22, "Location"), ("k11", 24, "Concept"),
    ("paired", 34, "Collective"), ("paired", 36, "Institution"), ("paired", 38, "Object"), ("paired", 40, "Location"), ("paired", 42, "Concept"),
    ("reserve", 52, "Agent"), ("reserve", 54, "Institution"), ("reserve", 56, "Object"), ("reserve", 58, "Location"), ("reserve", 60, "Concept"),
    ("meridian", 70, "Agent"), ("meridian", 72, "Institution"), ("meridian", 74, "Object"), ("meridian", 76, "Location"), ("meridian", 78, "Concept"),
    ("approaches", 87, "Agent"), ("approaches", 89, "Institution"), ("approaches", 91, "Object"), ("approaches", 93, "Location"), ("approaches", 95, "Concept"),
    ("sea", 105, "Collective"), ("sea", 107, "Institution"), ("sea", 109, "Object"), ("sea", 111, "Location"), ("sea", 113, "Concept"),
    ("k11", 124, "Agent"), ("k11", 126, "Agent"), ("k11", 130, "Object"), ("k11", 132, "Location"),
    ("paired", 141, "Agent"), ("paired", 143, "Collective"), ("paired", 149, "Object"), ("paired", 151, "Location"),
    ("reserve", 161, "Agent"), ("reserve", 163, "Agent"), ("reserve", 169, "Object"), ("reserve", 171, "Location"),
    ("meridian", 181, "Agent"), ("meridian", 183, "Collective"), ("meridian", 189, "Object"), ("meridian", 191, "Location"),
    ("approaches", 200, "Agent"), ("approaches", 202, "Agent"), ("approaches", 206, "Object"), ("approaches", 208, "Location"),
    ("sea", 217, "Collective"), ("sea", 219, "Agent"), ("sea", 225, "Object"), ("sea", 227, "Location"),
)

RIVALS = (
    ("k11", 128, "Office of Subsequent Weight", "Completion Registry K-11"),
    ("paired", 145, "Office of Unresolved Agreement", "Concordance Bureau"),
    ("reserve", 165, "Unopened Release Court", "Viability Directorate"),
    ("meridian", 185, "Meridian Interval House", "Restoration Choir"),
    ("approaches", 204, "Assembly of Qualified Entry", "Route Engineering Office"),
    ("sea", 221, "House of Necessary Error", "Concordant Tide Office"),
)

RECOVERED_RECORDS = (
    ("k11", 5, 28, 31), ("paired", 5, 46, 49), ("reserve", 5, 64, 67),
    ("meridian", 5, 82, 84), ("approaches", 5, 99, 102), ("sea", 5, 117, 119),
    ("k11", 6, 134, 138), ("paired", 6, 153, 158), ("reserve", 6, 173, 178),
    ("meridian", 6, 193, 197), ("approaches", 6, 210, 214), ("sea", 6, 229, 233),
)

T7_FIELDS = {
    "Habitation": "habitation",
    "Clothing": "clothing",
    "Maintenance/sustenance": "maintenance_sustenance",
    "Transport": "transport",
    "Work rhythm": "work_rhythm",
    "Social custom": "social_custom",
    "Body modification": "body_modification",
    "Death/custody": "death_custody",
    "Repair culture": "repair_culture",
    "Ordinary phrase": "ordinary_phrase",
}
T8_FIELDS = {
    "Friendship": "friendship",
    "Intimacy": "intimacy",
    "Privacy": "privacy",
    "Education": "education",
    "Mourning": "mourning",
    "Art": "art",
    "Recreation": "recreation",
    "Humour": "humour",
    "Shame": "shame",
    "Taboo": "taboo",
    "Hospitality": "hospitality",
    "Social exclusion": "social_exclusion",
}


def stable_uuid7(servati_id: str) -> str:
    random_bits = hashlib.sha256(servati_id.encode("utf-8")).digest()[:10]
    raw = bytearray(UUID7_TIMESTAMP_MS.to_bytes(6, "big") + random_bits)
    raw[6] = (raw[6] & 0x0F) | 0x70
    raw[8] = (raw[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(raw)))


def slug(value: str) -> str:
    value = re.sub(r"[’'`]", "", value.lower())
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Particularisation source hash differs from the authoritative local ingestion copy")
    lines = SOURCE.read_text(encoding="utf-8").splitlines()

    def line(number: int) -> str:
        return lines[number - 1].strip()

    def bold_definition(number: int) -> tuple[str, str]:
        match = re.fullmatch(r"\*\*(.+?)\*\* — (.+)", line(number))
        if not match:
            raise SystemExit(f"Expected a named definition at source line {number}")
        return match.group(1), match.group(2)

    world_by_key = {world.key: world for world in WORLDS}
    entries: list[dict[str, object]] = []
    ids_by_name: dict[str, str] = {}
    local_names: dict[str, dict[str, list[str]]] = {
        world.key: {kind: [] for kind in ("Agent", "Collective", "Institution", "Object", "Location", "Narrative", "Concept")}
        for world in WORLDS
    }

    def metadata(servati_id: str, world: WorldSpec, location: str, preservation: str) -> dict[str, object]:
        return {
            "servati_id": servati_id,
            "canon_status": "DRAFT",
            "era": "Choir age",
            "inheritance_logic": [world.logic],
            "provenance": [
                {
                    "source_kind": "working-pack",
                    "source_ref": SOURCE_REL,
                    "source_location": location,
                    "verification": "VERIFIED",
                    "note": "Verifies this V12 DRAFT record against the authoritative creative source; no canon promotion.",
                }
            ],
            "science_status": "requires-review" if servati_id.startswith("SV-DRAFT-WORLD") else "not-applicable",
            "preservation_problem": preservation,
            "first_appearance": SOURCE_REL,
            "editorial_notes": "Structured ingestion only. All particulars remain V12 DRAFT.",
        }

    def add_entry(entry: dict[str, object], world_key: str) -> None:
        name = str(entry["Name"])
        if name.casefold() in {item.casefold() for item in ids_by_name}:
            raise SystemExit(f"Duplicate structured name: {name}")
        ids_by_name[name] = str(entry["Id"])
        local_names[world_key][str(entry["Supertype"])].append(name)
        entries.append(entry)

    world_entries: dict[str, dict[str, object]] = {}
    historical_lines = {"k11": 26, "paired": 44, "reserve": 62, "meridian": 80, "approaches": 97, "sea": 115}
    material_lines = {"k11": 387, "paired": 388, "reserve": 389, "meridian": 390, "approaches": 391, "sea": 392}
    for index, world in enumerate(WORLDS, start=1):
        servati_id = f"SV-DRAFT-WORLD-05-{index:02d}"
        description = line(historical_lines[world.key]).removeprefix("Historical consequence: ")
        material = line(material_lines[world.key]).split(": **", 1)[1].removesuffix("**")
        particularisation: dict[str, str] = {"historical_consequence": description}
        for number in range(world.t7_range[0] + 1, world.t7_range[1] + 1):
            text = line(number)
            if not text:
                continue
            if world.key == "k11" and number == 261:
                particularisation["habitation"] = text
                continue
            label, separator, value = text.partition(": ")
            if separator and label in T7_FIELDS:
                particularisation[T7_FIELDS[label]] = value
        kin_name, kin_description = bold_definition(world.t8_range[0] + 1)
        particularisation["kinship"] = f"{kin_name} — {kin_description}"
        for number in range(world.t8_range[0] + 2, world.t8_range[1] + 1):
            text = line(number)
            if not text:
                continue
            label, separator, value = text.partition(": ")
            if separator and label in T8_FIELDS:
                particularisation[T8_FIELDS[label]] = value
        entry: dict[str, object] = {
            "Id": stable_uuid7(servati_id),
            "Name": world.name,
            "Description": description,
            "World": WORLD_REFERENCE,
            "Supertype": "Location",
            "Subtype": "Choir-age world",
            "Setting": {"form": particularisation["habitation"], "function": material},
            "Particularisation": particularisation,
            "servati": metadata(
                servati_id,
                world,
                f"Tranche 05 lines {world.t5_range[0]}-{world.t5_range[1]}; Tranche 06 lines {world.t6_range[0]}-{world.t6_range[1]}; Tranche 07 lines {world.t7_range[0]}-{world.t7_range[1]}; Tranche 08 lines {world.t8_range[0]}-{world.t8_range[1]}",
                world.preservation_problem,
            ),
        }
        world_entries[world.key] = entry
        add_entry(entry, world.key)

    counters = {kind: 0 for kind in ("Agent", "Collective", "Institution", "Object", "Location", "Concept")}
    prefixes = {"Agent": "AGT", "Collective": "COL", "Institution": "INS", "Object": "OBJ", "Location": "SITE", "Concept": "TERM"}
    subtypes = {"Agent": "Custodial actor", "Collective": "Collective mind", "Institution": "Custodial institution", "Object": "Artefact", "Location": "Local site", "Concept": "DRAFT terminology"}
    structural_fields = {"Agent": "Agency", "Collective": "Formation", "Institution": "Foundation", "Object": "Form"}
    structural_keys = {"Agent": "role", "Collective": "composition", "Institution": "doctrine", "Object": "aesthetics"}

    for world_key, number, supertype in NAMED_RECORDS:
        world = world_by_key[world_key]
        name, description = bold_definition(number)
        counters[supertype] += 1
        servati_id = f"SV-DRAFT-{prefixes[supertype]}-05-{counters[supertype]:02d}"
        entry = {
            "Id": stable_uuid7(servati_id),
            "Name": name,
            "Description": description,
            "World": world_entries[world_key]["Id"],
            "Supertype": supertype,
            "Subtype": subtypes[supertype],
            "servati": metadata(servati_id, world, f"Tranche {'05' if number < 121 else '06'}, source line {number}", world.preservation_problem),
        }
        if supertype in structural_fields:
            entry[structural_fields[supertype]] = {structural_keys[supertype]: description}
        if supertype == "Object":
            entry["Function"] = {"utility": description}
        if supertype == "Location":
            entry["Setting"] = {"form": description, "function": description, "parent_location": world_entries[world_key]["Id"]}
        add_entry(entry, world_key)

    rivalry_names: dict[str, tuple[str, str]] = {}
    for world_key, number, main_name, rival_name in RIVALS:
        world = world_by_key[world_key]
        text = line(number)
        match = re.fullmatch(r"Institutional rivalry: \*\*(.+?)\*\* vs \*\*(.+?)\*\*\. (.+)", text)
        if not match or (match.group(1), match.group(2)) != (main_name, rival_name):
            raise SystemExit(f"Rivalry changed at source line {number}")
        description = match.group(3)
        counters["Institution"] += 1
        servati_id = f"SV-DRAFT-INS-05-{counters['Institution']:02d}"
        entry = {
            "Id": stable_uuid7(servati_id),
            "Name": rival_name,
            "Description": description,
            "World": world_entries[world_key]["Id"],
            "Supertype": "Institution",
            "Subtype": "Custodial institution",
            "Foundation": {"doctrine": description},
            "servati": metadata(servati_id, world, f"Tranche 06, source line {number}", world.preservation_problem),
        }
        add_entry(entry, world_key)
        rivalry_names[world_key] = (main_name, rival_name)

    counters["Institution"] += 1
    refusal_id = f"SV-DRAFT-INS-05-{counters['Institution']:02d}"
    refusal_description = " ".join(line(number) for number in (236, 246))
    refusal_entry = {
        "Id": stable_uuid7(refusal_id),
        "Name": "The Refusal Correspondence",
        "Description": refusal_description,
        "World": WORLD_REFERENCE,
        "Supertype": "Institution",
        "Subtype": "Correspondence tradition",
        "Foundation": {"doctrine": line(256).removeprefix("Shared answer: ").strip("*")},
        "servati": metadata(refusal_id, WORLDS[0], "Tranche 06, source lines 235-256", "Something important survives between states"),
    }
    refusal_entry["servati"]["inheritance_logic"] = [world.logic for world in WORLDS]
    ids_by_name["The Refusal Correspondence"] = str(refusal_entry["Id"])
    entries.append(refusal_entry)

    for world_key, tranche, start, end in RECOVERED_RECORDS:
        world = world_by_key[world_key]
        counter = len(local_names[world_key]["Narrative"]) + 1
        servati_id = f"SV-DRAFT-REC-{world_key.upper()}-{tranche:02d}-{counter:02d}"
        story = "\n".join(line(number).removeprefix("> ") for number in range(start + 1, end + 1))
        entry = {
            "Id": stable_uuid7(servati_id),
            "Name": f"{world.name} Recovered Record {tranche:02d}",
            "Description": story,
            "World": world_entries[world_key]["Id"],
            "Supertype": "Narrative",
            "Subtype": "Recovered custody record",
            "Context": {"story": story},
            "Involves": {"locations": [world_entries[world_key]["Id"]]},
            "servati": metadata(servati_id, world, f"Tranche {tranche:02d}, source lines {start}-{end}", world.preservation_problem),
        }
        add_entry(entry, world_key)

    # Resolve source-supported local relationships after all IDs exist.
    for world in WORLDS:
        grouped = local_names[world.key]
        world_entries[world.key]["Involves"] = {
            "locations": [ids_by_name[name] for name in grouped["Location"]],
            "institutions": [ids_by_name[name] for name in grouped["Institution"]] + [str(refusal_entry["Id"])],
            "collectives": [ids_by_name[name] for name in grouped["Collective"]],
            "agents": [ids_by_name[name] for name in grouped["Agent"]],
            "objects": [ids_by_name[name] for name in grouped["Object"]],
            "narratives": [ids_by_name[name] for name in grouped["Narrative"]],
            "concepts": [ids_by_name[name] for name in grouped["Concept"]],
        }
        main_name, rival_name = rivalry_names[world.key]
        for name in (main_name, rival_name):
            entry = next(item for item in entries if item["Name"] == name)
            entry["Involves"] = {
                "locations": [world_entries[world.key]["Id"]],
                "institutions": [ids_by_name[rival_name if name == main_name else main_name]],
            }

    refusal_entry["Involves"] = {
        "locations": [world_entries[world.key]["Id"] for world in WORLDS],
        "institutions": [ids_by_name[rivalry_names[world.key][0]] for world in WORLDS],
    }

    dataset = {
        "$schema": "../../schemas/servati-dataset.schema.json",
        "dataset_id": "SV-DRAFT-V12-PARTICULARISATION-05-08",
        "canon_status": "DRAFT",
        "schema_basis": {
            "project": "OnlyWorlds/OnlyWorlds",
            "revision": "ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f",
            "licence": "MIT",
            "scope": "Base entity fields with additive SERVATI Agent, Collective, Institution, Object, Narrative, Concept, typed relation, provenance, and world-particularisation fields.",
        },
        "working_pack": {"filename": SOURCE_REL, "sha256": SOURCE_SHA256},
        "world_reference": {
            "Id": WORLD_REFERENCE,
            "status": "DRAFT_PLACEHOLDER",
            "note": "Shared relational root retained for compatibility. It is not a lore world and does not promote any V12 record.",
        },
        "entries": entries,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"output": str(OUTPUT), "entries": len(entries), "source_sha256": SOURCE_SHA256}, indent=2))


if __name__ == "__main__":
    main()
