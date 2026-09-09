# SERVATI Codex Phase 2 FOSS Register

## Scope

This register records the GitHub-first research boundary for encyclopedia-depth
work. SERVATI remains a Quartz v5 site; source prose and canon authority are not
delegated to third-party software.

## Authority Pins

| Authority | Display branch | Immutable build revision |
| --- | --- | --- |
| Version 11 released manuscript | `main` | `21b72ea0bbdaa4c8f9372270bb06b9501c5b9965` |
| Version 12 draft tranches 01-03 | `v12-faiths-choirs-custody-wars-20260907` | `5bd417299c4e99163404f655e569dcc2fc03789b` |

The branch names remain visible for editorial context and current-source links.
Generation exact revisions above control extraction and make repeated builds of a
Codex commit deterministic.

## Reused Components

| Project | Exact revision | Licence | Phase 2 use |
| --- | --- | --- | --- |
| [jackyzha0/quartz](https://github.com/jackyzha0/quartz/tree/f1fba3fc55cbf60a60a5d09c95a49c042cdab63a) | `f1fba3fc55cbf60a60a5d09c95a49c042cdab63a` | MIT | Static page engine, virtual tag/folder pages, build graph, layouts, and component resources. |
| [quartz-community/tag-page](https://github.com/quartz-community/tag-page/tree/a651839686ed2bd7e58beb01709b9a682dc9add8) | `a651839686ed2bd7e58beb01709b9a682dc9add8` | MIT | Slash-delimited hierarchical tag browsing beneath the curated category layer. |
| [quartz-community/backlinks](https://github.com/quartz-community/backlinks/tree/cb445dcc3f6969e4088bb0ff4254ba59071e4243) | `cb445dcc3f6969e4088bb0ff4254ba59071e4243` | MIT | Immediate per-page incoming links. Generated What Links Here pages add type, state, and source context. |
| [quartz-community/search](https://github.com/quartz-community/search/tree/1d9ba593230b997ee4cf0cc3c1ed4a30b571cee2) | `1d9ba593230b997ee4cf0cc3c1ed4a30b571cee2` | MIT | FlexSearch full text, highlighted matches, keyboard navigation, and conjunctive tag filters. |
| [quartz-community/content-index](https://github.com/quartz-community/content-index/tree/1342d1eacfdabbcefa2c6a26f8346945a9d9860f) | `1342d1eacfdabbcefa2c6a26f8346945a9d9860f` | MIT | Search and client-side discovery data. |
| [quartz-community/obsidian-flavored-markdown](https://github.com/quartz-community/obsidian-flavored-markdown/tree/dc9256d44b903d6188ef432626dd620090b88c3b) | `dc9256d44b903d6188ef432626dd620090b88c3b` | MIT | Explicit-path wikilinks, callouts, tags, and internal-link normalization. |

## Adapted Patterns

| Project | Exact revision | Licence | Adoption boundary |
| --- | --- | --- | --- |
| [foambubble/foam](https://github.com/foambubble/foam/tree/97b82e4ed7f363ff9cdbbfab0bb4dd90c7c4d487) | `97b82e4ed7f363ff9cdbbfab0bb4dd90c7c4d487` | MIT | Graph terminology for backlinks, orphans, and missing-link reports. No VS Code UI code is used. |
| [Pagefind/pagefind](https://github.com/Pagefind/pagefind/tree/3e48197b82b20c0a31a5c13e662efe37f49ce431) | `3e48197b82b20c0a31a5c13e662efe37f49ce431` | MIT | Evaluated for static facets. Not bundled because Quartz Search already supplies full text and hierarchical tag conjunction without another index. |

## Reference Only

MediaWiki and TiddlyWiki were reviewed for mature Special-page, category,
What-Links-Here, random-page, and navbox behaviour. Their runtime and licensing
models are not copied into SERVATI. MediaWiki is GPL-2.0-or-later and remains a
behavioural reference only.

Generated Special pages, category indexes, provenance, mention analysis, and
depth reports are original SERVATI build logic in `codex/servati_codex.py`.

## Evaluated but not included

[`satche/quartz-navbar`](https://github.com/satche/quartz-navbar/tree/b62e37616a1cc08451ff2f4e6f07d39963f61140)
at `b62e37616a1cc08451ff2f4e6f07d39963f61140` was tested under its MIT licence.
Its transformer and component registered under pinned Quartz v5, but the
pre-built component bundled a separate Preact runtime and its VNode was omitted
from emitted pages. The upstream code is not copied or patched. SERVATI instead
generates a small static navigation landmark from its own controlled routes.
