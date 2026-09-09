from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


REPOSITORY_URL = "https://github.com/Nexlu1/servati"
V11_BRANCH = "main"
V11_REF = "21b72ea0bbdaa4c8f9372270bb06b9501c5b9965"
V12_BRANCH = "v12-faiths-choirs-custody-wars-20260907"
V12_REF = "5bd417299c4e99163404f655e569dcc2fc03789b"
INHERITANCE_LOGICS = ("Remains", "Memory", "Seed", "Ritual", "Structure", "Pattern")
PART_LABELS = {
    "Part I — The Burdened Earth": "burdened-earth",
    "Part II — Reliquary Earth": "reliquary-earth",
    "Part III — The Sepulchral Reach": "sepulchral-reach",
    "Part IV — The Scattered Lamps": "scattered-lamps",
    "Part V — The Choirs of Ruin": "choirs-of-ruin",
    "Part VI — The Last Maintenance": "last-maintenance",
}


@dataclass
class Source:
    key: str
    path: str
    branch: str
    ref: str
    text: str
    commit: str
    modified: str
    author: str
    first_commit: str
    first_date: str
    sha256: str

    @property
    def source_url(self) -> str:
        return f"{REPOSITORY_URL}/blob/{self.branch}/{self.path}"

    @property
    def permanent_url(self) -> str:
        return f"{REPOSITORY_URL}/blob/{self.commit}/{self.path}"


@dataclass
class Entry:
    rel: str
    title: str
    status: str
    record_type: str
    source: Source
    section: str
    body: str
    start_line: int
    end_line: int
    source_order: int
    template: str
    register: str
    categories: list[str]
    era: str | None = None
    part: str | None = None
    inheritance: list[str] = field(default_factory=list)
    listed: bool = True
    aliases: list[str] = field(default_factory=list)
    outgoing: set[str] = field(default_factory=set)
    wanted: set[str] = field(default_factory=set)
    ambiguous: set[str] = field(default_factory=set)
    mention_context: dict[str, str] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        return Path(self.rel).with_suffix("").as_posix()

    @property
    def word_count(self) -> int:
        text = re.sub(r"[`*#>\[\](){|}_-]", " ", self.body)
        return len(re.findall(r"\b[\w’'-]+\b", text, re.UNICODE))


CATEGORY_DEFINITIONS: dict[str, tuple[str, str | None, str]] = {
    "history": ("History", None, "Narrative eras and the controlled chronology of the Continuance."),
    "history/burdened-earth": ("Burdened Earth", "history", "Part I of the Version 11 narrative."),
    "history/reliquary-earth": ("Reliquary Earth", "history", "Part II of the Version 11 narrative."),
    "history/sepulchral-reach": ("Sepulchral Reach", "history", "Part III of the Version 11 narrative."),
    "history/scattered-lamps": ("Scattered Lamps", "history", "Part IV of the Version 11 narrative."),
    "history/choirs-of-ruin": ("Choirs of Ruin", "history", "Part V of the Version 11 narrative."),
    "history/last-maintenance": ("Last Maintenance", "history", "Part VI of the Version 11 narrative."),
    "entities": ("Entities", None, "Curated registers of places, peoples, systems, concepts, and records."),
    "entities/chapters": ("Chapters", "entities", "The thirty controlled Version 11 chapters."),
    "entities/worlds": ("Worlds", "entities", "World-scale and Lamp-scale custody settings."),
    "entities/environments": ("Environments", "entities", "Custody environments and spatial systems."),
    "entities/lineages": ("Lineages", "entities", "Custodial and post-human lineages."),
    "entities/concepts": ("Concepts", "entities", "Controlled SERVATI vocabulary."),
    "entities/faiths": ("Faiths and Doctrines", "entities", "Archive Faiths, doctrines, and schisms."),
    "entities/choirs": ("Choir Civilizations", "entities", "Large custodial civilizations organized by Choir logic."),
    "entities/events": ("Events, Crises, and Wars", "entities", "Conflicts, crises, and controlled historical events."),
    "entities/artefacts": ("Artefacts and Technologies", "entities", "Custody objects, systems, and megastructures."),
    "entities/people": ("People and Collective Minds", "entities", "Named actors, offices, and collective intelligences."),
    "entities/recovered-records": ("Recovered Records", "entities", "Version 11 archaeological recovery fragments."),
    "inheritance": ("Inheritance Logic", None, "The six controlled preservation logics."),
    "inheritance/remains": ("Remains", "inheritance", "Physical custody of preserved dead matter."),
    "inheritance/memory": ("Memory", "inheritance", "Names, identities, relations, uncertainty, and archive."),
    "inheritance/seed": ("Seed", "inheritance", "Dormant futures and controlled developmental possibility."),
    "inheritance/ritual": ("Ritual", "inheritance", "Inherited act, interval, and procedure."),
    "inheritance/structure": ("Structure", "inheritance", "Chambers, thresholds, routes, and spatial order."),
    "inheritance/pattern": ("Pattern", "inheritance", "Continuity through relation across changing substrate."),
    "canon-state": ("Canon State", None, "The authority boundary applied to generated records."),
    "canon-state/v11-core": ("V11 CORE", "canon-state", "Released Version 11 canon."),
    "canon-state/v12-draft": ("V12 DRAFT", "canon-state", "Unreleased GitHub-hosted development material."),
    "evidence": ("Evidence State", None, "Source-supported interpretive or documentary states."),
    "evidence/reconstructed": ("Reconstructed", "evidence", "Records explicitly presented as archaeological reconstruction."),
    "evidence/doctrinal": ("Doctrinal", "evidence", "Records explicitly concerned with doctrine or faith."),
}


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_show(repo: Path, spec: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", spec],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout if result.returncode == 0 else None


def load_source(repo: Path, key: str, path: str, branch: str, ref: str) -> Source:
    spec = f"{ref}:{path}"
    text = git_show(repo, spec)
    if text is None:
        raise SystemExit(f"Pinned source is unavailable: {spec}")
    log = run_git(repo, "log", "--format=%H%x09%cs%x09%an", ref, "--", path).splitlines()
    if not log:
        raise SystemExit(f"No Git provenance found for {spec}")
    latest = log[0].split("\t", 2)
    first = log[-1].split("\t", 2)
    return Source(
        key=key,
        path=path,
        branch=branch,
        ref=ref,
        text=text,
        commit=latest[0],
        modified=latest[1],
        author=latest[2],
        first_commit=first[0],
        first_date=first[1],
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def slug(value: str) -> str:
    value = re.sub(r"[’'`]", "", value.lower().strip())
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "page"


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def wikilink(title: str, rel: str) -> str:
    return f"[[{Path(rel).with_suffix('').as_posix()}|{title}]]"


def relative_href(current_rel: str, target_rel: str) -> str:
    del current_rel
    return Path(target_rel).with_suffix("").as_posix()


def html_link(title: str, rel: str, current_rel: str, class_name: str | None = None) -> str:
    classes = f' class="{class_name}"' if class_name else ""
    return f'<a href="{relative_href(current_rel, rel)}"{classes}>{html.escape(title)}</a>'


def global_navigation(current_rel: str) -> str:
    current = Path(current_rel).with_suffix("").as_posix()
    links = (
        ("SERVATI", "index.md", ("index",)),
        ("History", "portals/history.md", ("history/", "portals/history")),
        (
            "Entities",
            "categories/entities.md",
            (
                "artefacts-and-technologies/",
                "choirs/",
                "core-terms/",
                "events-crises-and-wars/",
                "faiths/",
                "lineages/",
                "people-and-collective-minds/",
                "recovered-records/",
                "worlds-and-places/",
                "categories/entities",
            ),
        ),
        ("Timeline", "timeline/index.md", ("timeline/",)),
        ("Inheritance", "categories/inheritance.md", ("categories/inheritance",)),
        ("V12 Draft", "portals/v12-draft.md", ("v12-draft/", "portals/v12-draft")),
        ("Special", "special/index.md", ("special/",)),
    )
    items = []
    for label, target, prefixes in links:
        active = any(current == prefix or current.startswith(prefix) for prefix in prefixes)
        href = posixpath.relpath(
            Path(target).with_suffix("").as_posix(),
            Path(current_rel).parent.as_posix(),
        )
        classes = ' class="current"' if active else ""
        items.append(f'<a href="{href}"{classes}>{html.escape(label)}</a>')
    return '<nav class="codex-navbar" aria-label="SERVATI encyclopedia">' + "".join(items) + "</nav>"


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def demote_headings(body: str) -> str:
    body = re.sub(r"\A#\s+[^\n]+\n+", "", body.strip())
    return re.sub(r"^#(\s+)", r"##\1", body, flags=re.MULTILINE)


def section_span(text: str, start_pattern: str, end_pattern: str | None = None) -> tuple[str, int]:
    start = re.search(start_pattern, text, re.MULTILINE)
    if not start:
        return "", 0
    begin = start.end()
    if end_pattern:
        end = re.search(end_pattern, text[begin:], re.MULTILINE)
        if end:
            return text[begin : begin + end.start()], begin
    return text[begin:], begin


def parse_definitions(
    source: Source,
    start_pattern: str,
    end_pattern: str,
    pattern: str,
) -> list[tuple[re.Match[str], int, int]]:
    section, offset = section_span(source.text, start_pattern, end_pattern)
    matches = list(re.finditer(pattern, section, re.MULTILINE))
    return [
        (
            match,
            offset + match.start(),
            offset + (matches[index + 1].start() if index + 1 < len(matches) else match.end()),
        )
        for index, match in enumerate(matches)
    ]


def inheritance_from_text(text: str) -> list[str]:
    found: list[str] = []
    field_pattern = re.compile(
        r"(?:Primary inheritances?|Secondary inheritance|Inheritance):\*\*\s*([^\n]+)",
        re.IGNORECASE,
    )
    candidates = [match.group(1) for match in field_pattern.finditer(text)]
    for candidate in candidates:
        for logic in INHERITANCE_LOGICS:
            if re.search(rf"(?<!\w){logic}(?!\w)", candidate, re.IGNORECASE) and logic not in found:
                found.append(logic)
    return found


def category_for_type(record_type: str) -> str:
    return {
        "chapter": "entities/chapters",
        "world": "entities/worlds",
        "environment": "entities/environments",
        "world / environment": "entities/worlds",
        "lineage": "entities/lineages",
        "core term": "entities/concepts",
        "faith / doctrine": "entities/faiths",
        "Choir civilization": "entities/choirs",
        "event / crisis / war": "entities/events",
        "artefact / technology": "entities/artefacts",
        "person / collective mind": "entities/people",
        "recovered record": "entities/recovered-records",
        "chronology stage": "history",
    }.get(record_type, "entities/concepts")


def base_categories(status: str, record_type: str) -> list[str]:
    state = "canon-state/v12-draft" if status == "V12 DRAFT" else "canon-state/v11-core"
    return [category_for_type(record_type), state]


def make_entry(
    *,
    rel: str,
    title: str,
    status: str,
    record_type: str,
    source: Source,
    section: str,
    body: str,
    start: int,
    end: int,
    source_order: int,
    template: str,
    register: str,
    era: str | None = None,
    part: str | None = None,
    inheritance: list[str] | None = None,
    categories: list[str] | None = None,
    listed: bool = True,
    aliases: list[str] | None = None,
) -> Entry:
    all_categories = list(categories) if categories is not None else base_categories(status, record_type)
    for logic in inheritance or []:
        all_categories.append(f"inheritance/{logic.lower()}")
    return Entry(
        rel=rel,
        title=title,
        status=status,
        record_type=record_type,
        source=source,
        section=section,
        body=body.strip(),
        start_line=line_number(source.text, start),
        end_line=line_number(source.text, max(start, end - 1)),
        source_order=source_order,
        template=template,
        register=register,
        categories=list(dict.fromkeys(all_categories)),
        era=era,
        part=part,
        inheritance=list(inheritance or []),
        listed=listed,
        aliases=list(aliases or []),
    )


def extract_v11(source: Source) -> list[Entry]:
    entries: list[Entry] = []
    text = source.text
    chapters = list(re.finditer(r"^## Chapter (\d+) - (.+)$", text, re.MULTILINE))
    parts = list(re.finditer(r"^# Part ([IVX]+) - (.+)$", text, re.MULTILINE))
    appendix = re.search(r"^# Appendix I -", text, re.MULTILINE)
    for index, match in enumerate(chapters):
        number = int(match.group(1))
        title = match.group(2).strip()
        boundaries = [
            chapters[index + 1].start()
            if index + 1 < len(chapters)
            else appendix.start() if appendix else len(text)
        ]
        boundaries.extend(part.start() for part in parts if part.start() > match.start())
        end = min(boundaries)
        current_part = next(part for part in reversed(parts) if part.start() < match.start())
        part_label = f"Part {current_part.group(1)} — {current_part.group(2).strip()}"
        entries.append(
            make_entry(
                rel=f"history/{number:02d}-{slug(title)}.md",
                title=f"Chapter {number}: {title}",
                status="V11 CORE",
                record_type="chapter",
                source=source,
                section=f"Chapter {number} - {title}",
                body=text[match.end() : end],
                start=match.start(),
                end=end,
                source_order=number,
                template="chapter",
                register="History",
                era=part_label,
                part=part_label,
                categories=["entities/chapters", "history", f"history/{PART_LABELS[part_label]}", "canon-state/v11-core"],
                aliases=[f"Chapter {number}", title],
            )
        )

    definitions = [
        (
            r"^# Appendix I - Core Terms\s*$",
            r"^# Appendix II -",
            r"^\*\*(.+?)\.\*\*\s*(.+)$",
            "core-terms",
            "core term",
            "Core Terms",
            "core-term",
        ),
        (
            r"^# Appendix III - Principal Environments\s*$",
            r"^# Appendix IV -",
            r"^\*\*(.+?)\.\*\*\s*(.+)$",
            "worlds-and-places",
            "environment",
            "Worlds & Environments",
            "environment",
        ),
        (
            r"^# Appendix IV - Chronology of the Continuance\s*$",
            r"^# Appendix V -",
            r"^\*\*(.+?)\.\*\*\s*(.+)$",
            "timeline",
            "chronology stage",
            "Timeline",
            "chronology-stage",
        ),
        (
            r"^# Appendix XIV - Custody Schisms and Archive Faith Divergence\s*$",
            r"^# Appendix XV -",
            r"^\*\*(.+?)\.\*\*\s*(.+)$",
            "faiths",
            "faith / doctrine",
            "Faiths & Doctrines",
            "faith-doctrine",
        ),
        (
            r"^# Appendix XV - Cosmological Reliquary Systems\s*$",
            r"^# Appendix XVI -",
            r"^\*\*(.+?)\.\*\*\s*(.+)$",
            "artefacts-and-technologies",
            "artefact / technology",
            "Artefacts & Technologies",
            "artefact-technology",
        ),
    ]
    for start_pattern, end_pattern, pattern, folder, record_type, register, template in definitions:
        for order, (match, start, end) in enumerate(
            parse_definitions(source, start_pattern, end_pattern, pattern), 1
        ):
            title = match.group(1).strip()
            inheritance = [title] if title in INHERITANCE_LOGICS else []
            categories = base_categories("V11 CORE", record_type)
            if record_type == "faith / doctrine":
                categories.append("evidence/doctrinal")
            entries.append(
                make_entry(
                    rel=f"{folder}/{slug(title)}.md",
                    title=title,
                    status="V11 CORE",
                    record_type=record_type,
                    source=source,
                    section=register,
                    body=match.group(2),
                    start=start,
                    end=end,
                    source_order=order,
                    template=template,
                    register=register,
                    inheritance=inheritance,
                    categories=categories,
                )
            )

    lineage_pattern = r"^\*\*(.+?)\*\*\s*\((.+?)\)\.\s*(.+)$"
    for order, (match, start, end) in enumerate(
        parse_definitions(
            source,
            r"^# Appendix II - Principal Custodial Lineages\s*$",
            r"^# Appendix III -",
            lineage_pattern,
        ),
        1,
    ):
        title, era, description = (group.strip() for group in match.groups())
        inheritance = [logic for logic in INHERITANCE_LOGICS if f"{logic} Inheritance" in era]
        entries.append(
            make_entry(
                rel=f"lineages/{slug(title)}.md",
                title=title,
                status="V11 CORE",
                record_type="lineage",
                source=source,
                section="Principal Custodial Lineages",
                body=description,
                start=start,
                end=end,
                source_order=order,
                template="lineage",
                register="Post-Human Lineages",
                era=era,
                inheritance=inheritance,
            )
        )

    recovery_pattern = r"^\*\*(Fragment [A-Z]) - (.+?)\.\*\*\s*(.+)$"
    for order, (match, start, end) in enumerate(
        parse_definitions(
            source,
            r"^# Appendix XIII - Archaeological Recovery Fragments\s*$",
            r"^# Appendix XIV -",
            recovery_pattern,
        ),
        1,
    ):
        label, name, description = (group.strip() for group in match.groups())
        entries.append(
            make_entry(
                rel=f"recovered-records/{slug(label + '-' + name)}.md",
                title=f"{label}: {name}",
                status="V11 CORE",
                record_type="recovered record",
                source=source,
                section="Archaeological Recovery Fragments",
                body=description,
                start=start,
                end=end,
                source_order=order,
                template="recovered-record",
                register="Recovered Records",
                categories=["entities/recovered-records", "canon-state/v11-core", "evidence/reconstructed"],
                aliases=[name],
            )
        )
    return entries


def h2_sections(source: Source) -> list[tuple[str, str, str, int, int]]:
    headings = list(re.finditer(r"^(#{1,2})\s+(.+)$", source.text, re.MULTILINE))
    parent = ""
    sections = []
    for index, match in enumerate(headings):
        if match.group(1) == "#":
            parent = match.group(2).strip()
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(source.text)
        sections.append((match.group(2).strip(), source.text[match.end() : end].strip(), parent, match.start(), end))
    return sections


def clean_draft_title(raw: str) -> str:
    value = re.sub(r"^\d+\.\s*", "", raw.strip())
    value = re.sub(r"\s+[—-]\s+(?:DRAFT|V11 CORE name and basis)$", "", value, flags=re.IGNORECASE)
    campaign = re.match(r"^Campaign\s+(\d+)\s+[—-]\s+(.+)$", value, re.IGNORECASE)
    return f"Campaign {campaign.group(1)}: {campaign.group(2)}" if campaign else value.strip()


def draft_type(source: Source, parent: str) -> tuple[str, str, str]:
    if source.key == "v12-lamps":
        return "world / environment", "Worlds & Environments", "world-environment"
    if source.key == "v12-incidents":
        return "event / crisis / war", "Events, Crises & Wars", "event-crisis-war"
    if source.key == "v12-faiths":
        return "faith / doctrine", "Faiths & Doctrines", "faith-doctrine"
    normalized = re.sub(r"\s+[—-]\s+DRAFT.*$", "", parent).lower()
    if "choir civilizations" in normalized:
        return "Choir civilization", "Choir Civilizations", "choir-civilization"
    if "custody wars" in normalized or "crises" in normalized:
        return "event / crisis / war", "Events, Crises & Wars", "event-crisis-war"
    if "actors and collective" in normalized:
        return "person / collective mind", "People & Collective Minds", "person-collective-mind"
    if "artefacts and systems" in normalized:
        return "artefact / technology", "Artefacts & Technologies", "artefact-technology"
    return "development record", "Version 12 Development", "development-record"


def extract_draft(source: Source, folder: str, label: str) -> list[Entry]:
    entries: list[Entry] = []
    order = 0
    for raw, body, parent, start, end in h2_sections(source):
        if raw.lower() in {"canon anchor", "next controlled block"}:
            continue
        if re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX)\.", raw):
            continue
        title = clean_draft_title(raw)
        if not title or len(title) > 100:
            continue
        record_type, register, template = draft_type(source, parent)
        if record_type == "development record":
            continue
        order += 1
        inheritance = inheritance_from_text(body)
        categories = base_categories("V12 DRAFT", record_type)
        if record_type == "faith / doctrine":
            categories.append("evidence/doctrinal")
        entries.append(
            make_entry(
                rel=f"v12-draft/entries/{slug(title)}.md",
                title=title,
                status="V12 DRAFT",
                record_type=record_type,
                source=source,
                section=parent,
                body=body,
                start=start,
                end=end,
                source_order=order,
                template=template,
                register=register,
                inheritance=inheritance,
                categories=categories,
                aliases=[re.sub(r"^Campaign \d+:\s*", "", title)],
            )
        )
    return entries


def build_alias_map(entries: list[Entry]) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        names = {entry.title, *entry.aliases}
        if entry.title.lower().startswith("the "):
            names.add(entry.title[4:])
        for name in names:
            aliases[name.casefold()].add(entry.rel)
    return aliases


def excerpt(text: str, position: int, length: int = 260) -> str:
    start = max(text.rfind("\n\n", 0, position), 0)
    end = text.find("\n\n", position)
    if end < 0:
        end = len(text)
    value = re.sub(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]", lambda match: match.group(2) or match.group(1), text[start:end])
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\s+", " ", value).strip(" -*#>\t")
    if len(value) > length:
        value = value[: length - 1].rstrip() + "…"
    return value


def analyze_relations(entries: list[Entry]) -> tuple[dict[str, list[tuple[Entry, str]]], Counter[str]]:
    aliases = build_alias_map(entries)
    by_rel = {entry.rel: entry for entry in entries}
    incoming: dict[str, list[tuple[Entry, str]]] = defaultdict(list)
    wanted = Counter()
    title_candidates = sorted(aliases, key=len, reverse=True)

    for entry in entries:
        for match in re.finditer(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]", entry.body):
            label = match.group(1).strip()
            targets = aliases.get(label.casefold(), set())
            if len(targets) == 1:
                target = next(iter(targets))
                if target != entry.rel:
                    entry.outgoing.add(target)
                    entry.mention_context.setdefault(target, excerpt(entry.body, match.start()))
            elif len(targets) > 1:
                entry.ambiguous.add(label)
            else:
                entry.wanted.add(label)
                wanted[label] += 1

        lowered = entry.body.casefold()
        occupied: list[tuple[int, int]] = []
        for candidate in title_candidates:
            targets = aliases[candidate]
            if len(targets) != 1:
                continue
            target = next(iter(targets))
            if target == entry.rel:
                continue
            for match in re.finditer(rf"(?<!\w){re.escape(candidate)}(?!\w)", lowered):
                if any(match.start() < end and match.end() > start for start, end in occupied):
                    continue
                occupied.append((match.start(), match.end()))
                entry.outgoing.add(target)
                entry.mention_context.setdefault(target, excerpt(entry.body, match.start()))
                break

    registers: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        if entry.listed:
            registers[entry.register].append(entry)
    for register_entries in registers.values():
        ordered = sorted(register_entries, key=lambda item: (item.source.key, item.source_order, item.title))
        for index, entry in enumerate(ordered):
            if index:
                entry.outgoing.add(ordered[index - 1].rel)
            if index + 1 < len(ordered):
                entry.outgoing.add(ordered[index + 1].rel)

    for entry in entries:
        for target in sorted(entry.outgoing):
            if target in by_rel:
                incoming[target].append((entry, entry.mention_context.get(target, "Register navigation.")))
    return incoming, wanted


def resolve_source_links(body: str, aliases: dict[str, set[str]], entry: Entry) -> str:
    def replace_wikilink(match: re.Match[str]) -> str:
        target_name = match.group(1).strip()
        label = (match.group(2) or target_name).strip()
        targets = aliases.get(target_name.casefold(), set())
        if len(targets) == 1:
            return wikilink(label, next(iter(targets)))
        kind = "ambiguous" if len(targets) > 1 else "missing"
        return wikilink(f"{label} ({kind} record)", "special/wanted-links.md")

    body = re.sub(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]", replace_wikilink, body)

    def replace_markdown_link(match: re.Match[str]) -> str:
        label, destination = match.group(1), match.group(2)
        if destination.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        targets = aliases.get(label.casefold(), set())
        if len(targets) == 1:
            return wikilink(label, next(iter(targets)))
        chapter = re.search(r"Chapter\s+(\d+)", label, re.IGNORECASE)
        if chapter:
            chapter_targets = aliases.get(f"chapter {chapter.group(1)}".casefold(), set())
            if len(chapter_targets) == 1:
                return wikilink(label, next(iter(chapter_targets)))
        return label

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_markdown_link, body)


def category_link(category: str) -> str:
    label = CATEGORY_DEFINITIONS[category][0]
    return wikilink(label, f"categories/{category}.md")


def source_line_url(entry: Entry, permanent: bool = False) -> str:
    base = entry.source.permanent_url if permanent else entry.source.source_url
    return f"{base}#L{entry.start_line}-L{entry.end_line}"


def type_label(entry: Entry) -> str:
    return entry.record_type.upper().replace(" / ", " · ")


def render_navbox(entry: Entry, entries_by_rel: dict[str, Entry]) -> str:
    related = [entries_by_rel[rel] for rel in sorted(entry.outgoing) if rel in entries_by_rel]
    if not related:
        return ""
    links = "\n".join(
        f'<a href="{relative_href(entry.rel, target.rel)}" data-status="{slug(target.status)}"><span>{html.escape(type_label(target))}</span><strong>{html.escape(target.title)}</strong></a>'
        for target in related[:18]
    )
    return f"""## Related records

<nav class="record-navbox" aria-label="Related SERVATI records">
{links}
</nav>
"""


def render_entry(entry: Entry, entries_by_rel: dict[str, Entry], incoming: dict[str, list[tuple[Entry, str]]]) -> str:
    aliases = build_alias_map(list(entries_by_rel.values()))
    body = resolve_source_links(demote_headings(entry.body), aliases, entry)
    inheritance = " / ".join(entry.inheritance) if entry.inheritance else "Not explicitly assigned"
    context = f"""<div class="record-identity record-identity--{slug(entry.template)}">
  <span>{html.escape(entry.status)}</span>
  <span>{html.escape(type_label(entry))}</span>
  <span>{html.escape(entry.register)}</span>
</div>
"""
    if entry.inheritance:
        context += f'<p class="record-inheritance"><strong>Inheritance:</strong> {html.escape(inheritance)}</p>\n'

    incoming_records = [
        item for item in incoming.get(entry.rel, []) if item[1] != "Register navigation."
    ]
    mention_section = ""
    if incoming_records:
        items = []
        for source_entry, source_excerpt in sorted(
            incoming_records, key=lambda item: (item[0].status, item[0].record_type, item[0].title)
        )[:24]:
            snippet = f"<small>{html.escape(source_excerpt)}</small>"
            items.append(
                f'<li>{html_link(source_entry.title, source_entry.rel, entry.rel)} '
                f'<span class="record-link-meta">{html.escape(source_entry.status)} / {html.escape(source_entry.record_type)}</span>{snippet}</li>'
            )
        mention_section = "## Appearances and mentions\n\n<ul class=\"mention-list\">\n" + "\n".join(items) + "\n</ul>\n"

    what_links_rel = f"special/what-links-here/{entry.slug.replace('/', '--')}.md"
    tools_html = "\n".join(
        (
            html_link("What links here", what_links_rel, entry.rel),
            '<a href="#related-records">Related records</a>',
            html_link("Categories", "categories/index.md", entry.rel),
        )
    )
    categories = " · ".join(
        html_link(CATEGORY_DEFINITIONS[category][0], f"categories/{category}.md", entry.rel)
        for category in entry.categories
    )
    source = entry.source
    provenance = f"""## Source and provenance

- **Source record:** [{source.path} lines {entry.start_line}-{entry.end_line}]({source_line_url(entry)})
- **Permanent source:** [{source.commit[:12]} lines {entry.start_line}-{entry.end_line}]({source_line_url(entry, permanent=True)})
- **Source section:** {entry.section}
- **First source commit:** [{source.first_commit[:12]}]({REPOSITORY_URL}/commit/{source.first_commit}) on {source.first_date}
- **Last source commit:** [{source.commit[:12]}]({REPOSITORY_URL}/commit/{source.commit}) on {source.modified}, by {source.author}
"""
    toolbox = f"""## Page tools

<div class="page-toolbox">
{tools_html}
<a href="{source_line_url(entry)}">GitHub source</a>
<a href="{source_line_url(entry, permanent=True)}">Permanent source version</a>
<span><strong>Canon state:</strong> {entry.status}</span>
</div>
"""
    category_section = f"## Categories\n\n<div class=\"article-categories\">{categories}</div>\n"
    return "\n\n".join(
        part.strip()
        for part in (
            global_navigation(entry.rel),
            context,
            body,
            mention_section,
            render_navbox(entry, entries_by_rel),
            provenance,
            toolbox,
            category_section,
        )
        if part.strip()
    )


def frontmatter(entry: Entry) -> list[str]:
    state_tag = (
        "canon/v12-draft"
        if entry.status == "V12 DRAFT"
        else "canon/v11" if entry.status == "V11 CORE" else "navigation"
    )
    tags = [
        state_tag,
        f"type/{slug(entry.record_type)}",
        f"register/{slug(entry.register)}",
        *(f"category/{category}" for category in entry.categories),
    ]
    rows = [
        "---",
        f"title: {quote(entry.title)}",
        f"status: {quote(entry.status)}",
        f"type: {quote(entry.record_type)}",
        f"template: {quote(entry.template)}",
        f"register: {quote(entry.register)}",
        f"modified: {quote(entry.source.modified)}",
        f"created: {quote(entry.source.first_date)}",
    ]
    if entry.era:
        rows.append(f"era: {quote(entry.era)}")
    if entry.part:
        rows.append(f"part: {quote(entry.part)}")
    if entry.inheritance:
        rows.extend(["inheritance_logic:", *(f"  - {logic}" for logic in entry.inheritance)])
    rows.extend(
        [
            f"source_file: {quote(entry.source.path)}",
            f"source_branch: {quote(entry.source.branch)}",
            f"source_commit: {quote(entry.source.commit)}",
            f"source_section: {quote(entry.section)}",
            f"source_lines: {quote(f'{entry.start_line}-{entry.end_line}')}",
            f"source_order: {entry.source_order}",
            f"word_count: {entry.word_count}",
            "categories:",
            *(f"  - {category}" for category in entry.categories),
            "tags:",
            *(f"  - {tag}" for tag in dict.fromkeys(tags)),
            "---",
            "",
        ]
    )
    return rows


def write_entry(root: Path, entry: Entry, body: str) -> None:
    path = root / entry.rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter(entry)) + body.strip() + "\n", encoding="utf-8")


def generated_source(repo: Path, latest: Source) -> Source:
    path = "codex/servati_codex.py"
    text = (repo / path).read_text(encoding="utf-8")
    committed_text = git_show(repo, f"HEAD:{path}")
    if committed_text != text:
        raise SystemExit(f"Generator must be committed before publication: {path}")
    commit, modified, author = run_git(repo, "show", "-s", "--format=%H%x09%cs%x09%an", "HEAD").split("\t", 2)
    history = run_git(repo, "log", "--format=%H%x09%cs", "HEAD", "--", path).splitlines()
    first_commit, first_date = history[-1].split("\t", 1) if history else (commit, modified)
    return Source(
        key="generated",
        path=path,
        branch="codex-quartz-site-20260908",
        ref="HEAD",
        text=text,
        commit=commit,
        modified=max(modified, latest.modified),
        author=author,
        first_commit=first_commit,
        first_date=first_date,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def page_entry(
    source: Source,
    rel: str,
    title: str,
    body: str,
    template: str,
    record_type: str,
    register: str,
    categories: list[str] | None = None,
) -> Entry:
    return make_entry(
        rel=rel,
        title=title,
        status="CONTROLLED",
        record_type=record_type,
        source=source,
        section="Generated encyclopedia index",
        body=body,
        start=0,
        end=len(source.text),
        source_order=0,
        template=template,
        register=register,
        categories=categories or [],
        listed=False,
    )


def table(rows: list[list[str]], headings: list[str]) -> str:
    header = "| " + " | ".join(headings) + " |"
    rule = "| " + " | ".join("---" for _ in headings) + " |"
    return "\n".join([header, rule, *("| " + " | ".join(row) + " |" for row in rows)])


def generate_category_pages(source: Source, entries: list[Entry]) -> list[Entry]:
    pages = []
    members: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        if entry.listed:
            for category in entry.categories:
                members[category].append(entry)
    for category, (label, parent, description) in CATEGORY_DEFINITIONS.items():
        children = [key for key, value in CATEGORY_DEFINITIONS.items() if value[1] == category]
        child_links = "\n".join(
            f"- {category_link(child)} — {CATEGORY_DEFINITIONS[child][2]}" for child in children
        )
        member_rows = [
            [wikilink(entry.title, entry.rel), entry.record_type, entry.status, str(entry.word_count)]
            for entry in sorted(members.get(category, []), key=lambda item: item.title.casefold())
        ]
        body = f"""<div class="category-header"><span>CATEGORY</span><strong>{html.escape(label)}</strong><b>{len(member_rows)} records</b></div>

{description}

## Subcategories

{child_links or "No narrower categories are currently generated."}

## Records

{table(member_rows, ["Record", "Type", "Canon state", "Words"]) if member_rows else "No records are directly assigned to this category."}

## Category path

{category_link(parent) if parent else wikilink("All categories", "categories/index.md")}
"""
        pages.append(
            page_entry(
                source,
                f"categories/{category}.md",
                f"Category: {label}",
                body,
                "category",
                "category",
                "Categories",
                [parent] if parent else [],
            )
        )
    root_rows = [
        [category_link(category), description, str(len(members.get(category, [])))]
        for category, (label, parent, description) in CATEGORY_DEFINITIONS.items()
        if parent is None
    ]
    pages.append(
        page_entry(
            source,
            "categories/index.md",
            "SERVATI Categories",
            "Hierarchical category paths connect broad archive domains to controlled records.\n\n"
            + table(root_rows, ["Category", "Scope", "Direct records"]),
            "category-index",
            "category index",
            "Categories",
        )
    )
    return pages


def record_rows(entries: list[Entry]) -> list[list[str]]:
    return [
        [wikilink(entry.title, entry.rel), entry.record_type, entry.status, entry.register, str(entry.word_count)]
        for entry in entries
    ]


def generate_special_pages(
    source: Source,
    entries: list[Entry],
    incoming: dict[str, list[tuple[Entry, str]]],
    wanted: Counter[str],
) -> tuple[list[Entry], dict[str, object]]:
    listed = [entry for entry in entries if entry.listed]
    canon = [entry for entry in listed if entry.status == "V11 CORE"]
    drafts = [entry for entry in listed if entry.status == "V12 DRAFT"]
    orphaned = [
        entry
        for entry in listed
        if not [item for item in incoming.get(entry.rel, []) if item[1] != "Register navigation."]
    ]
    short = sorted(listed, key=lambda item: (item.word_count, item.title))
    long = list(reversed(short))
    most_linked = sorted(listed, key=lambda item: (-len(incoming.get(item.rel, [])), item.title))
    type_counts = Counter(entry.record_type for entry in listed)
    register_counts = Counter(entry.register for entry in listed)
    source_counts = Counter(entry.source.path for entry in listed)
    ambiguous = Counter(label for entry in listed for label in entry.ambiguous)
    internal_links = sum(len(entry.outgoing) for entry in listed)
    tag_count = len({category for entry in listed for category in entry.categories})
    stats = {
        "total_records": len(listed),
        "v11_canon": len(canon),
        "v12_draft": len(drafts),
        "record_types": dict(sorted(type_counts.items())),
        "registers": dict(sorted(register_counts.items())),
        "internal_links": internal_links,
        "backlinks": sum(len(value) for value in incoming.values()),
        "orphaned_records": len(orphaned),
        "wanted_titles": len(wanted),
        "wanted_link_occurrences": sum(wanted.values()),
        "ambiguous_titles": len(ambiguous),
        "ambiguous_link_occurrences": sum(ambiguous.values()),
        "categories": tag_count,
        "source_files": len(source_counts),
    }
    pages: list[Entry] = []

    def special(rel: str, title: str, body: str) -> None:
        pages.append(page_entry(source, f"special/{rel}.md", title, body, "special-page", "special page", "Special Pages"))

    special(
        "all-pages",
        "Special: All Pages",
        table(record_rows(sorted(listed, key=lambda item: item.title.casefold())), ["Record", "Type", "State", "Register", "Words"]),
    )
    special("canon", "Special: All Canon Pages", table(record_rows(canon), ["Record", "Type", "State", "Register", "Words"]))
    special("drafts", "Special: All Draft Pages", table(record_rows(drafts), ["Record", "Type", "State", "Register", "Words"]))
    special(
        "categories",
        "Special: Categories",
        f"The Codex currently exposes **{tag_count} populated category paths**.\n\n{wikilink('Browse the hierarchical category index', 'categories/index.md')}",
    )
    special(
        "most-linked",
        "Special: Most Linked Records",
        table(
            [[wikilink(entry.title, entry.rel), str(len(incoming.get(entry.rel, []))), entry.record_type, entry.status] for entry in most_linked],
            ["Record", "Incoming record links", "Type", "State"],
        ),
    )
    special(
        "orphaned",
        "Special: Orphaned Records",
        "Orphans have no source-derived semantic links from another content record; sequential register, portal, category, and Special-page links are excluded.\n\n"
        + (table(record_rows(orphaned), ["Record", "Type", "State", "Register", "Words"]) if orphaned else "No record orphans were found."),
    )
    wanted_rows = [[title, str(count)] for title, count in wanted.most_common()]
    aliases = build_alias_map(entries)
    entries_by_rel = {entry.rel: entry for entry in entries}
    ambiguous_rows = [
        [
            title,
            str(count),
            ", ".join(
                wikilink(entries_by_rel[rel].title, rel)
                for rel in sorted(aliases[title.casefold()])
            ),
        ]
        for title, count in ambiguous.most_common()
    ]
    special(
        "wanted-links",
        "Special: Wanted and Missing Links",
        "Wanted titles preserve unresolved GitHub draft link intent without emitting broken Quartz links. Ambiguous titles resolve to more than one controlled record and require editorial disambiguation.\n\n"
        "## Missing targets\n\n"
        + (table(wanted_rows, ["Missing title", "References"]) if wanted_rows else "No missing link targets were found.")
        + "\n\n## Ambiguous targets\n\n"
        + (table(ambiguous_rows, ["Ambiguous title", "References", "Candidate records"]) if ambiguous_rows else "No ambiguous link targets were found."),
    )
    special(
        "short-pages",
        "Special: Short Records",
        "Short records are reported for editorial awareness; authoritative one-sentence definitions are not integrity failures.\n\n"
        + table(record_rows(short[:75]), ["Record", "Type", "State", "Register", "Words"]),
    )
    special(
        "long-pages",
        "Special: Long Records",
        table(record_rows(long[:75]), ["Record", "Type", "State", "Register", "Words"]),
    )
    recent = sorted(listed, key=lambda item: (item.source.modified, item.source.commit, item.title), reverse=True)
    recent_rows = [
        [wikilink(entry.title, entry.rel), entry.source.modified, f"[{entry.source.commit[:12]}]({REPOSITORY_URL}/commit/{entry.source.commit})", entry.source.path]
        for entry in recent
    ]
    special(
        "recent-changes",
        "Special: Recent Source Changes",
        "This is generated from authoritative Git history, not filesystem timestamps. Extracted records share their source file's commit.\n\n"
        + table(recent_rows, ["Record", "Date", "Commit", "Source file"]),
    )
    stat_rows = [
        ["Total content records", str(stats["total_records"])],
        ["V11 canon", str(stats["v11_canon"])],
        ["V12 draft", str(stats["v12_draft"])],
        *[[label, str(count)] for label, count in sorted(type_counts.items())],
        ["Internal record links", str(stats["internal_links"])],
        ["Backlinks", str(stats["backlinks"])],
        ["Orphaned records", str(stats["orphaned_records"])],
        ["Wanted titles", str(stats["wanted_titles"])],
        ["Populated categories", str(stats["categories"])],
        ["Source files", str(stats["source_files"])],
    ]
    special("statistics", "Special: Statistics", table(stat_rows, ["Measure", "Count"]))
    special(
        "search",
        "Special: Search",
        "Use the Search control from the permanent navigation. Search supports full text, keyboard navigation, highlighted matches, and conjunctive hierarchical tag filters.\n\n"
        "## Useful filters\n\n"
        "- `#canon/v11` — released canon only\n"
        "- `#canon/v12-draft` — development records only\n"
        "- `#type/chapter` — chapters\n"
        "- `#category/entities/lineages` — lineages\n"
        "- `#category/inheritance/memory` — Memory inheritance\n",
    )
    special(
        "index",
        "SERVATI Special Pages",
        "Static-build equivalents of MediaWiki Special pages, derived from the generated corpus.\n\n"
        + "\n".join(
            f"- {wikilink(label, f'special/{rel}.md')}"
            for rel, label in (
                ("all-pages", "All Pages"),
                ("categories", "Categories"),
                ("canon", "All Canon Pages"),
                ("drafts", "All Draft Pages"),
                ("recent-changes", "Recent Source Changes"),
                ("most-linked", "Most Linked Records"),
                ("orphaned", "Orphaned Records"),
                ("wanted-links", "Wanted and Missing Links"),
                ("short-pages", "Short Records"),
                ("long-pages", "Long Records"),
                ("statistics", "Statistics"),
                ("search", "Search Help and Filters"),
                ("what-links-here/index", "What Links Here Index"),
            )
        ),
    )

    what_links_rows = []
    for entry in sorted(listed, key=lambda item: item.title.casefold()):
        sources = incoming.get(entry.rel, [])
        route = f"special/what-links-here/{entry.slug.replace('/', '--')}.md"
        what_links_rows.append([wikilink(entry.title, route), str(len(sources)), entry.record_type, entry.status])
        source_items = []
        for source_entry, source_excerpt in sources:
            snippet = "" if source_excerpt == "Register navigation." else f"\n  > {source_excerpt}"
            source_items.append(
                f"- {wikilink(source_entry.title, source_entry.rel)} — {source_entry.record_type}; {source_entry.status}{snippet}"
            )
        body = f"""{wikilink('Return to the target record', entry.rel)}

## Pages linking here

{chr(10).join(source_items) if source_items else "No other content records link to this record."}

## Target metadata

- **Type:** {entry.record_type}
- **Canon state:** {entry.status}
- **Register:** {entry.register}
"""
        pages.append(page_entry(source, route, f"What Links Here: {entry.title}", body, "what-links-here", "special page", "What Links Here"))
    special(
        "what-links-here/index",
        "Special: What Links Here",
        table(what_links_rows, ["Target record", "Incoming links", "Type", "State"]),
    )
    return pages, stats


def portal_body(
    current_rel: str,
    title: str,
    overview: str,
    members: list[Entry],
    branches: list[str],
    related: list[tuple[str, str]],
) -> str:
    featured = members[:6]
    branch_links = "\n".join(f"- {category_link(category)}" for category in branches)
    featured_links = "\n".join(
        f'<a href="{relative_href(current_rel, entry.rel)}"><span>{html.escape(entry.record_type.upper())}</span><strong>{html.escape(entry.title)}</strong><b>{html.escape(entry.status)}</b></a>'
        for entry in featured
    )
    browse_rows = table(record_rows(members), ["Record", "Type", "State", "Register", "Words"])
    related_links = " · ".join(wikilink(label, rel) for label, rel in related)
    return f"""<div class="portal-masthead"><span>CURATED PORTAL</span><strong>{html.escape(title)}</strong><b>{len(members)} records</b></div>

{overview}

## Major branches

{branch_links}

## Featured records

<div class="portal-featured">
{featured_links}
</div>

## Browse this portal

{browse_rows}

## Related portals

{related_links}
"""


def generate_portals(source: Source, entries: list[Entry]) -> list[Entry]:
    listed = [entry for entry in entries if entry.listed]
    specs = [
        ("history", "History & Eras Portal", "The controlled chapter sequence and chronology of the Continuance.", lambda e: e.record_type in {"chapter", "chronology stage"}, ["history"], [("Custody / Continuance", "portals/custody.md"), ("Worlds", "portals/worlds.md")]),
        ("worlds", "Worlds Portal", "Worlds, environments, Lamps, and custody settings explicitly present in the sources.", lambda e: e.record_type in {"world", "environment", "world / environment"}, ["entities/worlds", "entities/environments"], [("Lineages", "portals/lineages.md"), ("History", "portals/history.md")]),
        ("lineages", "Lineages Portal", "Principal custodial and post-human lineages across the controlled record.", lambda e: e.record_type == "lineage", ["entities/lineages"], [("Worlds", "portals/worlds.md"), ("Custody / Continuance", "portals/custody.md")]),
        ("custody", "Custody / Continuance Portal", "Concepts, events, and systems concerned with custody and the Continuance.", lambda e: e.record_type in {"core term", "event / crisis / war", "artefact / technology"}, ["entities/concepts", "entities/events", "entities/artefacts"], [("Faiths", "portals/faiths.md"), ("Choirs", "portals/choirs.md")]),
        ("faiths", "Faiths Portal", "Source-backed Archive Faiths, doctrines, and schisms with canon state kept explicit.", lambda e: e.record_type == "faith / doctrine", ["entities/faiths", "evidence/doctrinal"], [("Choirs", "portals/choirs.md"), ("V12 Development", "portals/v12-draft.md")]),
        ("choirs", "Choirs Portal", "Choir civilizations and the inheritance logics they enlarge.", lambda e: e.record_type == "Choir civilization", ["entities/choirs", "inheritance"], [("Faiths", "portals/faiths.md"), ("Worlds", "portals/worlds.md")]),
        ("core-terms", "Core Terms Portal", "Controlled vocabulary from Version 11 Appendix I.", lambda e: e.record_type == "core term", ["entities/concepts", "inheritance"], [("History", "portals/history.md"), ("Custody / Continuance", "portals/custody.md")]),
        ("v12-draft", "Version 12 Development Portal", "GitHub-hosted development material. Every record in this portal remains visibly DRAFT.", lambda e: e.status == "V12 DRAFT", ["canon-state/v12-draft"], [("Faiths", "portals/faiths.md"), ("Choirs", "portals/choirs.md")]),
    ]
    pages = []
    for slug_name, title, overview, predicate, branches, related in specs:
        members = sorted((entry for entry in listed if predicate(entry)), key=lambda item: (item.source_order, item.title))
        rel = f"portals/{slug_name}.md"
        pages.append(page_entry(source, rel, title, portal_body(rel, title, overview, members, branches, related), "portal", "portal", "Portals"))
    pages.append(
        page_entry(
            source,
            "portals/index.md",
            "SERVATI Portals",
            "Curated paths through the archive.\n\n"
            + "\n".join(f"- {wikilink(title, f'portals/{slug_name}.md')}" for slug_name, title, *_ in specs),
            "portal-index",
            "portal index",
            "Portals",
        )
    )
    return pages


def generate_register_indexes(source: Source, entries: list[Entry]) -> list[Entry]:
    paths = {
        "History": ("history/index.md", "History Register"),
        "Timeline": ("timeline/index.md", "Timeline Register"),
        "Worlds & Environments": ("worlds-and-places/index.md", "Worlds & Environments Register"),
        "Post-Human Lineages": ("lineages/index.md", "Post-Human Lineages Register"),
        "Core Terms": ("core-terms/index.md", "Core Terms Register"),
        "Faiths & Doctrines": ("faiths/index.md", "Faiths & Doctrines Register"),
        "Choir Civilizations": ("choirs/index.md", "Choir Civilizations Register"),
        "Events, Crises & Wars": ("events-and-crises/index.md", "Events, Crises & Wars Register"),
        "Artefacts & Technologies": ("artefacts-and-technologies/index.md", "Artefacts & Technologies Register"),
        "People & Collective Minds": ("people-and-collective-minds/index.md", "People & Collective Minds Register"),
        "Recovered Records": ("recovered-records/index.md", "Recovered Records Register"),
        "Version 12 Development": ("v12-draft/index.md", "Version 12 Development Register"),
    }
    pages = []
    for register, (rel, title) in paths.items():
        members = sorted((entry for entry in entries if entry.listed and entry.register == register), key=lambda item: (item.source_order, item.title))
        body = table(record_rows(members), ["Record", "Type", "State", "Register", "Words"]) if members else "No records currently exist in this register."
        pages.append(page_entry(source, rel, title, body, "register-index", "register index", register))
    return pages


def generate_homepage(source: Source, entries: list[Entry], stats: dict[str, object]) -> Entry:
    listed = [entry for entry in entries if entry.listed]
    featured = {
        "Featured Article": next(entry for entry in listed if entry.record_type == "chapter"),
        "Featured World": next(entry for entry in listed if entry.record_type in {"world", "environment"}),
        "Featured Lineage": next(entry for entry in listed if entry.record_type == "lineage"),
        "Featured Recovered Record": next(entry for entry in listed if entry.record_type == "recovered record"),
    }
    featured_html = "\n".join(
        f'<a href="{relative_href("index.md", entry.rel)}"><span>{label.upper()}</span><strong>{html.escape(entry.title)}</strong><b>{html.escape(entry.status)}</b></a>'
        for label, entry in featured.items()
    )
    recent = sorted(listed, key=lambda item: (item.source.modified, item.title), reverse=True)[:8]
    recent_links = "\n".join(f"- {wikilink(entry.title, entry.rel)} — {entry.source.modified}; {entry.status}" for entry in recent)
    portal_links = "\n".join(
        f'<a class="archive-portal" href="./portals/{path}"><span class="archive-portal-code">PORTAL / {label.upper()}</span><strong>{label}</strong><span>{description}</span></a>'
        for path, label, description in (
            ("history", "History & Eras", "Narrative sequence and controlled chronology."),
            ("worlds", "Worlds", "Worlds, Lamps, environments, and custody settings."),
            ("lineages", "Lineages", "Custodial and post-human lineages."),
            ("custody", "Custody / Continuance", "Concepts, events, and custody systems."),
            ("faiths", "Faiths", "Archive Faiths, doctrines, and schisms."),
            ("choirs", "Choirs", "Choir civilizations and their logics."),
            ("v12-draft", "V12 Development", "Clearly separated unreleased development records."),
        )
    )
    stat_items = "\n".join(
        f"<span><b>{value}</b>{label}</span>"
        for label, value in (
            ("records", stats["total_records"]),
            ("V11 canon", stats["v11_canon"]),
            ("V12 draft", stats["v12_draft"]),
            ("categories", stats["categories"]),
            ("record links", stats["internal_links"]),
            ("source files", stats["source_files"]),
        )
    )
    body = f"""<p class="archive-kicker">CONTROLLED SETTING ENCYCLOPEDIA / GITHUB-BACKED EDITION</p>
<p class="archive-lede">The Worlds That Held the Dead. A browsable reference for the controlled SERVATI setting.</p>
<div class="archive-status-line" aria-label="Record status legend"><span class="archive-status archive-status--verified">V11 CORE / VERIFIED</span><span class="archive-status archive-status--draft">V12 / DRAFT RECORDS</span></div>

> Version 11 is released canon. Version 12 material remains **DRAFT** unless explicitly promoted.

## Major portals

<nav class="archive-portals" aria-label="Major SERVATI portals">{portal_links}</nav>

## Browse by era

<div class="category-browse">{" · ".join(html_link(CATEGORY_DEFINITIONS[f'history/{part}'][0], f'categories/history/{part}.md', 'index.md') for part in PART_LABELS.values())}</div>

## Browse by entity type

<div class="category-browse">{" · ".join(html_link(CATEGORY_DEFINITIONS[category][0], f'categories/{category}.md', 'index.md') for category in ('entities/worlds','entities/environments','entities/lineages','entities/concepts','entities/faiths','entities/choirs','entities/events','entities/artefacts','entities/people','entities/recovered-records'))}</div>

## Browse by inheritance logic

<div class="category-browse">{" · ".join(html_link(logic, f'categories/inheritance/{logic.lower()}.md', 'index.md') for logic in INHERITANCE_LOGICS)}</div>

## Featured records

<div class="archive-featured">{featured_html}</div>

## Canon and development

Released Version 11 records and Version 12 development records share navigation but never authority state. Use {wikilink('All Canon Pages', 'special/canon.md')} or {wikilink('All Draft Pages', 'special/drafts.md')} to browse either boundary directly.

## Recent source changes

{recent_links}

{wikilink('Open the Git-backed Recent Changes report', 'special/recent-changes.md')}

## Archive statistics

<div class="archive-statistics">{stat_items}</div>

{wikilink('Open complete statistics', 'special/statistics.md')}

## Discovery

<nav class="archive-actions" aria-label="Library actions">
  <a href="./special/all-pages">All pages</a>
  <a href="./categories">Categories</a>
  <a href="./special/most-linked">Most linked</a>
  <a href="./special/orphaned">Orphaned records</a>
  <a href="./special/wanted-links">Wanted links</a>
  <a href="./special/index">Special pages</a>
</nav>

The GitHub repository remains the authoritative project record.
"""
    return page_entry(source, "index.md", "SERVATI Codex", body, "homepage", "navigation", "Main", [])


def validate_entries(entries: list[Entry]) -> dict[str, object]:
    rel_counts = Counter(entry.rel.casefold() for entry in entries)
    duplicate_slugs = sorted(rel for rel, count in rel_counts.items() if count > 1)
    title_groups: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        title_groups[entry.title.casefold()].append(entry.rel)
    duplicate_titles = {title: paths for title, paths in title_groups.items() if len(paths) > 1}
    uncategorized = [entry.rel for entry in entries if entry.listed and not entry.categories]
    malformed = [entry.rel for entry in entries if not entry.source.commit or not entry.source.path or not entry.status]
    leakage = [
        entry.rel
        for entry in entries
        if (entry.source.branch == V12_BRANCH and entry.status != "V12 DRAFT")
        or (entry.source.branch == V11_BRANCH and entry.status != "V11 CORE")
    ]
    if duplicate_slugs:
        raise SystemExit(f"Duplicate generated slugs: {duplicate_slugs}")
    if uncategorized or malformed or leakage:
        raise SystemExit(
            f"Entry integrity failure: uncategorized={uncategorized}, malformed={malformed}, leakage={leakage}"
        )
    return {
        "duplicate_slugs": duplicate_slugs,
        "duplicate_titles": duplicate_titles,
        "uncategorized_records": uncategorized,
        "malformed_records": malformed,
        "canon_draft_leakage": leakage,
    }


def build(repo: Path, out: Path) -> dict[str, object]:
    target = out
    backup = target.with_name(f"{target.name}.previous")
    backup_marker = backup / ".servati_generated_content"
    if backup.exists() and any(backup.iterdir()) and not backup_marker.exists():
        raise SystemExit(f"Refusing to replace non-generated backup directory: {backup}")
    if not target.exists() and backup.exists():
        backup.replace(target)
    marker = target / ".servati_generated_content"
    if out.exists() and any(out.iterdir()):
        if not marker.exists():
            raise SystemExit(f"Refusing to replace non-generated content directory: {out}")

    sources = [
        load_source(repo, "v11", "SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md", V11_BRANCH, V11_REF),
        load_source(repo, "v12-lamps", "drafts/v12/tranche-01/scattered-lamps.md", V12_BRANCH, V12_REF),
        load_source(repo, "v12-incidents", "drafts/v12/tranche-01/custody-war-incidents.md", V12_BRANCH, V12_REF),
        load_source(repo, "v12-faiths", "drafts/v12/tranche-02/archive-faiths.md", V12_BRANCH, V12_REF),
        load_source(repo, "v12-choirs", "drafts/v12/tranche-03/choirs-custody-wars.md", V12_BRANCH, V12_REF),
    ]
    v11 = sources[0]
    entries = extract_v11(v11)
    entries.extend(extract_draft(sources[1], "scattered-lamps", "Scattered Lamp Cultures, Tranche 01"))
    entries.extend(extract_draft(sources[2], "custody-war-incidents", "Custody War Incidents, Tranche 01"))
    entries.extend(extract_draft(sources[3], "archive-faiths", "Archive Faiths, Tranche 02"))
    entries.extend(extract_draft(sources[4], "choirs-custody-wars", "Choirs and Custody Wars, Tranche 03"))

    integrity = validate_entries(entries)
    incoming, wanted = analyze_relations(entries)
    entries_by_rel = {entry.rel: entry for entry in entries}
    generated = generated_source(repo, max(sources, key=lambda item: item.modified))
    special_pages, statistics = generate_special_pages(generated, entries, incoming, wanted)
    category_pages = generate_category_pages(generated, entries)
    portal_pages = generate_portals(generated, entries)
    register_pages = generate_register_indexes(generated, entries)
    homepage = generate_homepage(generated, entries, statistics)

    out = target.with_name(f"{target.name}.building")
    staging_marker = out / ".servati_generated_content"
    if out.exists():
        if any(out.iterdir()) and not staging_marker.exists():
            raise SystemExit(f"Refusing to replace non-generated staging directory: {out}")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    staging_marker.write_text("generated\n", encoding="utf-8")

    for entry in entries:
        write_entry(out, entry, render_entry(entry, entries_by_rel, incoming))
    for page in [*special_pages, *category_pages, *portal_pages, *register_pages, homepage]:
        body = global_navigation(page.rel) + "\n\n" + demote_headings(page.body)
        write_entry(out, page, body)

    listed = [entry for entry in entries if entry.listed]
    aliases = build_alias_map(entries)
    ambiguous_labels = {label for entry in listed for label in entry.ambiguous}
    depth_report = {
        "statistics": statistics,
        "integrity": integrity,
        "orphaned_records": sorted(
            entry.rel
            for entry in listed
            if not [item for item in incoming.get(entry.rel, []) if item[1] != "Register navigation."]
        ),
        "wanted_links": dict(wanted.most_common()),
        "ambiguous_links": {
            label: sorted(aliases[label.casefold()]) for label in sorted(ambiguous_labels)
        },
        "thin_records": [
            {"path": entry.rel, "title": entry.title, "type": entry.record_type, "words": entry.word_count}
            for entry in sorted(listed, key=lambda item: item.word_count)
            if entry.word_count < 50
        ],
        "no_backlinks": sorted(entry.rel for entry in listed if not incoming.get(entry.rel)),
        "source_files": {
            source.path: {
                "branch": source.branch,
                "ref": source.ref,
                "commit": source.commit,
                "modified": source.modified,
                "first_commit": source.first_commit,
                "first_date": source.first_date,
                "sha256": source.sha256,
            }
            for source in sources
        },
        "generator": {
            "path": generated.path,
            "ref": generated.ref,
            "commit": generated.commit,
            "sha256": generated.sha256,
        },
    }
    result = {
        "generated_pages": len(list(out.rglob("*.md"))),
        "content_records": len(listed),
        "special_pages": len(special_pages),
        "category_pages": len(category_pages),
        "portal_pages": len(portal_pages),
        "register_pages": len(register_pages),
        "statistics": statistics,
        "note": "All V12 sources remain DRAFT; no source prose is promoted or invented.",
    }
    (out / "SERVATI_DEPTH_REPORT.json").write_text(json.dumps(depth_report, indent=2) + "\n", encoding="utf-8")
    (out / "SERVATI_GENERATION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        target.replace(backup)
    try:
        out.replace(target)
    except Exception:
        if backup.exists() and not target.exists():
            backup.replace(target)
        raise
    if backup.exists():
        shutil.rmtree(backup)
    print(json.dumps(result, indent=2), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    build(args.repo.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
