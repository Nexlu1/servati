#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import threading
import urllib.parse
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


MINIMUM_SOURCE_PAGES = 228
BASE_PATH = "/servati"
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
    args = parser.parse_args()

    generation_path = args.content / "SERVATI_GENERATION_RESULT.json"
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    source_pages = sorted(args.content.rglob("*.md"))
    generated_count = generation.get("generated_pages")
    require(generated_count == len(source_pages), "Generation manifest does not match Markdown count")
    require(generated_count >= MINIMUM_SOURCE_PAGES, f"Only {generated_count} source pages were generated")

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

    index_html = (args.output / "index.html").read_text(encoding="utf-8").lower()
    site_html = "\n".join(path.read_text(encoding="utf-8").lower() for path in html_pages)
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
    asset_paths = re.findall(r'(?:href|src)="(/servati/[^"]+\.(?:css|js))"', index_html)
    require(any(path.endswith(".css") for path in asset_paths), "Homepage has no stylesheet asset")
    require(any(path.endswith(".js") for path in asset_paths), "Homepage has no script asset")
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
