#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import threading
import urllib.parse
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


EXPECTED_SOURCE_PAGES = 608
BASE_PATH = "/servati"
EXPECTED_SOURCE_REFS = {
    "SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md": "21b72ea0bbdaa4c8f9372270bb06b9501c5b9965",
    "drafts/v12/tranche-01/scattered-lamps.md": "5bd417299c4e99163404f655e569dcc2fc03789b",
    "drafts/v12/tranche-01/custody-war-incidents.md": "5bd417299c4e99163404f655e569dcc2fc03789b",
    "drafts/v12/tranche-02/archive-faiths.md": "5bd417299c4e99163404f655e569dcc2fc03789b",
    "drafts/v12/tranche-03/choirs-custody-wars.md": "5bd417299c4e99163404f655e569dcc2fc03789b",
}
EXPECTED_AMBIGUOUS_TITLES = {
    "Choir Ascendants",
    "Hollow Archivists",
    "Quiet Route",
    "Weight Doctrine",
}
EXPECTED_PLUGIN_NAMES = {
    "article-title",
    "backlinks",
    "bases-page",
    "breadcrumbs",
    "content-index",
    "content-meta",
    "content-page",
    "crawl-links",
    "created-modified-date",
    "darkmode",
    "description",
    "explorer",
    "folder-page",
    "footer",
    "github-flavored-markdown",
    "graph",
    "note-properties",
    "obsidian-flavored-markdown",
    "page-title",
    "quartz_randomPage",
    "reader-mode",
    "recent-notes",
    "search",
    "table-of-contents",
    "tag-list",
    "tag-page",
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def translate_path(self, path: str) -> str:
        route = urllib.parse.urlsplit(path).path
        if route == BASE_PATH:
            route = "/"
        elif route.startswith(BASE_PATH + "/"):
            route = route[len(BASE_PATH) :]
        else:
            route = "/__outside_servati_base_path__"
        return super().translate_path(route)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def committed_source_hash(repo: Path, commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(result.returncode == 0, f"Cannot load committed source {commit}:{path}")
    return hashlib.sha256(result.stdout).hexdigest()


def find_sample(content: Path, output: Path, directory: str) -> Path:
    source = next(iter(sorted((content / directory).glob("*.md"))), None)
    require(source is not None, f"No generated source page found in {directory}")
    relative = source.relative_to(content).with_suffix(".html")
    require((output / relative).is_file(), f"Built sample page is missing: {relative.as_posix()}")
    return relative


def http_smoke_test(output: Path, paths: list[str]) -> list[dict[str, object]]:
    handler = partial(QuietHandler, directory=str(output))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = []
    try:
        for path in paths:
            with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}{path}") as response:
                require(response.status == 200, f"HTTP smoke test failed for {path}: {response.status}")
                response.read()
                results.append({"path": path, "status": response.status})
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plugin-result", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args()

    generation_path = args.content / "SERVATI_GENERATION_RESULT.json"
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    source_pages = sorted(args.content.rglob("*.md"))
    generated_count = generation.get("generated_pages")
    require(generated_count == len(source_pages), "Generation manifest does not match Markdown count")
    require(generated_count == EXPECTED_SOURCE_PAGES, f"Expected {EXPECTED_SOURCE_PAGES} source pages, found {generated_count}")
    require(generation.get("content_records") == 268, "Content record count changed")
    require(generation.get("special_pages") == 285, "Special-page count changed")
    require(generation.get("category_pages") == 33, "Category-page count changed")
    require(generation.get("portal_pages") == 9, "Portal-page count changed")
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in source_pages)
    require(not re.search(r"^#\s+", source_text, re.M), "Generated content contains body-level H1 headings")
    require(
        not re.search(r"\[\[[^\]|#]+\]\]", source_text),
        "Generated content contains unresolved title-only wikilinks",
    )
    require(
        all(re.search(r'^modified:\s+"\d{4}-\d{2}-\d{2}"$', path.read_text(encoding="utf-8"), re.M) for path in source_pages),
        "One or more generated pages lack a source-derived modification date",
    )
    require(
        all(re.search(r'^source_commit:\s+"[0-9a-f]{40}"$', path.read_text(encoding="utf-8"), re.M) for path in source_pages),
        "One or more generated pages lack an exact source commit",
    )
    depth_path = args.content / "SERVATI_DEPTH_REPORT.json"
    require(depth_path.is_file(), "Depth and integrity report is missing")
    depth = json.loads(depth_path.read_text(encoding="utf-8"))
    statistics = depth.get("statistics", {})
    require(
        statistics.get("generated_navigation_backlinks", 0) >= 1000,
        "Generated navigation backlink graph is unexpectedly sparse",
    )
    require(
        statistics.get("records_with_navigation_backlinks") == 268,
        "Not every record is represented in generated navigation",
    )
    integrity = depth.get("integrity", {})
    required_integrity = {
        "duplicate_slugs",
        "duplicate_titles",
        "uncategorized_records",
        "unknown_categories",
        "invalid_category_parents",
        "category_cycles",
        "malformed_records",
        "canon_draft_leakage",
    }
    require(required_integrity <= set(integrity), "Depth report is missing required integrity checks")
    require(not integrity.get("duplicate_slugs"), "Generated records contain duplicate slugs")
    require(not integrity.get("uncategorized_records"), "Content records without categories were generated")
    require(not integrity.get("unknown_categories"), "Records reference undefined categories")
    require(not integrity.get("invalid_category_parents"), "Taxonomy contains undefined parent categories")
    require(not integrity.get("category_cycles"), "Taxonomy contains parent cycles")
    require(not integrity.get("malformed_records"), "Malformed content metadata was generated")
    require(not integrity.get("canon_draft_leakage"), "Canon/draft authority leakage was detected")
    ambiguous_links = depth.get("ambiguous_links")
    require(isinstance(ambiguous_links, dict), "Depth report is missing ambiguous-link analysis")
    require(set(ambiguous_links) == EXPECTED_AMBIGUOUS_TITLES, "Ambiguous-title analysis changed")
    require(all(len(paths) == 2 for paths in ambiguous_links.values()), "Ambiguous targets are incomplete")
    require(depth.get("wanted_links") == {"Transfer Site Nine": 1}, "Wanted-link analysis changed")
    require(len(depth.get("record_depth", {})) == 268, "Per-record depth metrics are incomplete")
    category_population = depth.get("category_population", {})
    require(
        len(category_population) == 33
        and all(set(population) == {"direct", "descendants"} for population in category_population.values()),
        "Category population analysis is malformed",
    )
    require(isinstance(depth.get("empty_categories"), list), "Empty-category analysis is missing")
    require(isinstance(depth.get("isolated_records"), list), "Semantic isolation analysis is missing")
    require(isinstance(depth.get("no_semantic_backlinks"), list), "Semantic backlink coverage is missing")
    record_provenance = depth.get("record_provenance", {})
    require(len(record_provenance) == 268, "Record-level Git provenance is incomplete")
    require(
        all(
            re.fullmatch(r"[0-9a-f]{64}", provenance.get("body_sha256", ""))
            and provenance.get("revisions")
            and provenance.get("created") <= provenance.get("modified")
            for provenance in record_provenance.values()
        ),
        "Record-level Git provenance contains malformed values",
    )
    source_files = depth.get("source_files", {})
    require(set(source_files) == set(EXPECTED_SOURCE_REFS), "Depth report source-file set changed")
    for source_path, provenance in source_files.items():
        source_ref = provenance.get("ref", "")
        commit = provenance.get("commit", "")
        expected_hash = provenance.get("sha256", "")
        require(source_ref == EXPECTED_SOURCE_REFS[source_path], f"Wrong pinned source revision for {source_path}")
        require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, f"Invalid source commit for {source_path}")
        require(re.fullmatch(r"[0-9a-f]{64}", expected_hash) is not None, f"Invalid source hash for {source_path}")
        require(
            committed_source_hash(args.repo.resolve(), source_ref, source_path) == expected_hash,
            f"Source hash does not match committed bytes for {source_path}",
        )
    generator = depth.get("generator", {})
    generator_path = generator.get("path")
    head = subprocess.run(
        ["git", "-C", str(args.repo.resolve()), "rev-parse", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    require(generator_path == "codex/servati_codex.py", "Depth report identifies the wrong generator")
    require(generator.get("commit") == head, "Generated-page provenance does not match HEAD")
    require(
        committed_source_hash(args.repo.resolve(), head, generator_path) == generator.get("sha256"),
        "Generated-page source hash does not match committed generator bytes",
    )

    plugin_result = json.loads(args.plugin_result.read_text(encoding="utf-8"))
    require(plugin_result.get("operation") == "verify", "Plugin verification result is not final")
    require(plugin_result.get("plugin_count") == 26, "Not all 26 configured plugins were verified")
    require(
        plugin_result.get("quartz_sha") == "f1fba3fc55cbf60a60a5d09c95a49c042cdab63a",
        "Plugin verification used the wrong Quartz revision",
    )
    verified_plugins = plugin_result.get("plugins", [])
    verified_names = [plugin.get("name") for plugin in verified_plugins]
    require(
        len(verified_plugins) == 26 and set(verified_names) == EXPECTED_PLUGIN_NAMES,
        "Plugin verification result does not contain the exact configured plugin set",
    )
    require(
        all(
            plugin.get("actual_sha") == plugin.get("sha")
            and plugin.get("built") is True
            and plugin.get("load_mode") == "local"
            for plugin in verified_plugins
        ),
        "One or more plugin SHAs were not verified",
    )

    require((args.output / "index.html").is_file(), "Built site is missing index.html")
    missing_pages = []
    for source in source_pages:
        relative = source.relative_to(args.content).with_suffix(".html")
        if not (args.output / relative).is_file():
            missing_pages.append(relative.as_posix())
    require(not missing_pages, f"Built site is missing generated pages: {missing_pages[:10]}")

    html_pages = sorted(args.output.rglob("*.html"))
    require(
        len(html_pages) >= generated_count,
        f"Implausibly low HTML count: {len(html_pages)} for {generated_count} source pages",
    )
    require((args.output / "static" / "contentIndex.json").is_file(), "Search content index is missing")
    random_modes_script = args.output / "static" / "codex-random-modes.js"
    require(random_modes_script.is_file(), "Random discovery modes script is missing")
    require("fetchData" in random_modes_script.read_text(encoding="utf-8"), "Random modes do not use the search content index")

    index_html = (args.output / "index.html").read_text(encoding="utf-8").lower()
    site_html = "\n".join(path.read_text(encoding="utf-8").lower() for path in html_pages)
    entity_templates = {
        "chapter",
        "chronology-stage",
        "core-term",
        "environment",
        "world-environment",
        "lineage",
        "faith-doctrine",
        "choir-civilization",
        "event-crisis-war",
        "artefact-technology",
        "person-collective-mind",
        "recovered-record",
    }
    for template in entity_templates:
        require(
            f'class="entity-template entity-template--{template}"' in site_html,
            f"Distinct entity renderer is missing for {template}",
        )
    broken_links = re.findall(
        r'<a\b(?=[^>]*class="[^"]*\bbroken\b)[^>]*>.*?</a>',
        site_html,
    )
    require(
        not broken_links,
        f"Built site contains broken internal links: {broken_links[:5]}",
    )
    for signature in (
        'class="archive-portals"',
        'class="archive-featured"',
        'class="archive-actions"',
        'class="archive-statistics"',
        'class="category-browse"',
    ):
        require(signature in index_html, f"Homepage archive structure is missing {signature}")
    require('class="codex-navbar"' in index_html, "Permanent archive navigation is missing")
    for label in ("SERVATI", "History", "Entities", "Timeline", "Inheritance", "V12 Draft", "Special"):
        require(f">{label.lower()}</a>" in index_html, f"Permanent archive navigation is missing {label}")
    require(
        site_html.count('class="codex-navbar"') == generated_count,
        "Permanent archive navigation is not present on every controlled page",
    )
    required_routes = [
        "special/index.html",
        "special/all-pages.html",
        "special/categories.html",
        "special/canon.html",
        "special/drafts.html",
        "special/recent-changes.html",
        "special/most-linked.html",
        "special/orphaned.html",
        "special/wanted-links.html",
        "special/disambiguation.html",
        "special/taxonomy.html",
        "special/integrity.html",
        "special/short-pages.html",
        "special/long-pages.html",
        "special/statistics.html",
        "categories/index.html",
        "portals/custody.html",
        "portals/faiths.html",
        "portals/choirs.html",
    ]
    for route in required_routes:
        require((args.output / route).is_file(), f"Required encyclopedia route is missing: {route}")
    what_links_html = (
        args.output / "special" / "what-links-here" / "history--01-intake-exceeded.html"
    ).read_text(encoding="utf-8")
    for signature in ("Semantic record links", "Generated navigation and indexes", "Generated navigation backlinks"):
        require(signature in what_links_html, f"What Links Here is missing {signature}")
    chapter_html = (args.output / "history" / "01-intake-exceeded.html").read_text(encoding="utf-8")
    for signature in (
        "Register index",
        "Next in register",
        "note-properties",
        "metadata-container",
        "Current-line revisions",
        "Versioned Codex permalink",
        "Record body SHA-256",
    ):
        require(signature in chapter_html, f"Context-aware record navigation is missing {signature}")
    recent_html = (args.output / "special" / "recent-changes.html").read_text(encoding="utf-8")
    for signature in ("line-level Git blame", "Latest record commit", "Current-line revisions"):
        require(signature in recent_html, f"Recent Changes is missing record history field {signature}")
    integrity_html = (args.output / "special" / "integrity.html").read_text(encoding="utf-8")
    for signature in ("integrity-status", "Per-record depth", "Semantically isolated records", "Wanted and ambiguous links"):
        require(signature in integrity_html, f"Depth and integrity dashboard is missing {signature}")
    search_html = (args.output / "special" / "search.html").read_text(encoding="utf-8")
    for signature in ("search-facets", "codex-random-modes", "canon/v11", "random-category"):
        require(signature in search_html, f"Search and random discovery is missing {signature}")
    for portal in ("history", "worlds", "lineages", "custody", "faiths", "choirs", "core-terms", "v12-draft"):
        portal_html = (args.output / "portals" / f"{portal}.html").read_text(encoding="utf-8")
        for signature in ("portal-statistics", "portal-lenses", "V11 canon records", "V12 draft records", "Source strata"):
            require(signature in portal_html, f"Portal {portal} is missing curated section {signature}")
    feature_signatures = {
        "search": r'class="[^"]*\bsearch\b',
        "explorer": r'class="[^"]*\bexplorer\b',
        "backlinks": r'class="[^"]*\bbacklinks\b',
        "dark_mode": r'class="[^"]*\bdarkmode\b',
        "random_page": 'id="random-page-btn"',
    }
    for feature, signature in feature_signatures.items():
        require(re.search(signature, site_html), f"Required {feature} UI is absent from built pages")

    samples = {
        "homepage": Path("index.html"),
        "chapter": find_sample(args.content, args.output, "history"),
        "lineage": find_sample(args.content, args.output, "lineages"),
        "environment": find_sample(args.content, args.output, "worlds-and-places"),
    }
    page_paths = [
        BASE_PATH + "/"
        if page.as_posix() == "index.html"
        else BASE_PATH + "/" + urllib.parse.quote(page.as_posix())
        for page in samples.values()
    ]
    asset_urls = re.findall(
        r'(?:href|src)=["\']([^"\']+\.(?:css|js)(?:\?[^"\']*)?)["\']', index_html
    )
    local_asset_urls = [url for url in asset_urls if not url.startswith(("http://", "https://"))]
    require(
        any(urllib.parse.urlsplit(url).path.endswith(".css") for url in local_asset_urls),
        "Homepage has no stylesheet asset",
    )
    require(
        any(urllib.parse.urlsplit(url).path.endswith(".js") for url in local_asset_urls),
        "Homepage has no script asset",
    )
    asset_paths = []
    for url in local_asset_urls:
        path = urllib.parse.urlsplit(url).path
        require(
            not path.startswith("/") or path.startswith(BASE_PATH + "/"),
            f"Asset escapes base path: {path}",
        )
        asset_paths.append(path if path.startswith("/") else BASE_PATH + "/" + path.lstrip("./"))
    smoke_paths = page_paths + sorted(set(asset_paths)) + [BASE_PATH + "/static/contentIndex.json"]
    http_checks = http_smoke_test(args.output, smoke_paths)

    all_files = [path for path in args.output.rglob("*") if path.is_file()]
    result = {
        "source_page_count": len(source_pages),
        "represented_source_pages": len(source_pages) - len(missing_pages),
        "html_page_count": len(html_pages),
        "artifact_file_count": len(all_files) + 2,
        "search_index": "static/contentIndex.json",
        "features": sorted(feature_signatures),
        "depth_statistics": depth.get("statistics", {}),
        "special_page_count": generation.get("special_pages"),
        "category_page_count": generation.get("category_pages"),
        "samples": {name: path.as_posix() for name, path in samples.items()},
        "http_checks": http_checks,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output / args.plugin_result.name).write_bytes(args.plugin_result.read_bytes())
    (args.output / args.result.name).write_bytes(args.result.read_bytes())
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
