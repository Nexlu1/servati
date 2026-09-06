# GitHub-First FOSS and Tooling Register

**Observed:** 2026-09-06

Before SERVATI builds a tool, schema, generator, viewer, map, timeline, or
publishing system, GitHub must be searched for a suitable maintained project.
Public source without clear reusable permission is not reusable FOSS.

## Approved or adopted

| Need | Project and observed revision | Verified licence | Decision |
|---|---|---|---|
| Worldbuilding data vocabulary | [`OnlyWorlds/OnlyWorlds@ed84fa19`](https://github.com/OnlyWorlds/OnlyWorlds/tree/ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f) | [MIT](https://github.com/OnlyWorlds/OnlyWorlds/blob/ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f/LICENSE) | **Adopted in part.** SERVATI's JSON profile derives from the base, Location, and Event schema vocabulary. |
| Public linked-lore site | [`jackyzha0/quartz@f1fba3fc`](https://github.com/jackyzha0/quartz/tree/f1fba3fc55cbf60a60a5d09c95a49c042cdab63a) | [MIT](https://github.com/jackyzha0/quartz/blob/f1fba3fc55cbf60a60a5d09c95a49c042cdab63a/LICENSE.txt) | Candidate when a public Codex is justified; no code included now. |
| Local authoring reference | [`aronjanosch/chronicle-keeper@45cabb16`](https://github.com/aronjanosch/chronicle-keeper/tree/45cabb16fa34b6e1045db45eb4f8af3ae7f48d73) | [MIT](https://github.com/aronjanosch/chronicle-keeper/blob/45cabb16fa34b6e1045db45eb4f8af3ae7f48d73/LICENSE) | Reference for Markdown truth, atlas, timeline, graph, and backlinks; do not copy wholesale. |
| Planetary/regional mapping | [`Azgaar/Fantasy-Map-Generator@f2325b30`](https://github.com/Azgaar/Fantasy-Map-Generator/tree/f2325b3078b939fd368612d494fdd5e17a2cd2cf) | [MIT file verified](https://github.com/Azgaar/Fantasy-Map-Generator/blob/f2325b3078b939fd368612d494fdd5e17a2cd2cf/LICENSE); GitHub API reports `NOASSERTION` | External map tool first; do not assume its generated cultures are SERVATI lore. |
| Galaxy/story scaffolding | [`yudhanjaya/Starmap@f5a8b1a8`](https://github.com/yudhanjaya/Starmap/tree/f5a8b1a8af61b83dc2656f31164e4210e06852db) | [MIT](https://github.com/yudhanjaya/Starmap/blob/f5a8b1a8af61b83dc2656f31164e4210e06852db/LICENSE) | Algorithm reference only; civilisation assumptions are not canon. |
| Solar-system generation research | [`zakski/accrete-starform-stargen@f029fbf0`](https://github.com/zakski/accrete-starform-stargen/tree/f029fbf06bbedb6dbedbaee43c3686a8a1d3745d) | [Apache-2.0](https://github.com/zakski/accrete-starform-stargen/blob/f029fbf06bbedb6dbedbaee43c3686a8a1d3745d/LICENSE) | Algorithm reference; old models require modern science review. |
| Evolutionary-tree viewer | [`veg/phylotree.js@7b61f5d2`](https://github.com/veg/phylotree.js/tree/7b61f5d27f4e5176302033bd9b4ae873bd944cd8) | [MIT](https://github.com/veg/phylotree.js/blob/7b61f5d27f4e5176302033bd9b4ae873bd944cd8/LICENSE) | Candidate when a lineage viewer is built. |
| Historical sound change | [`def-gthill/lexurgy@fa502771`](https://github.com/def-gthill/lexurgy/tree/fa5027711cba3cd6a3f4b6defd0d38181fa98cd4) | [GPL-3.0](https://github.com/def-gthill/lexurgy/blob/fa5027711cba3cd6a3f4b6defd0d38181fa98cd4/LICENSE) | External tool; maintain a clear GPL boundary. |
| Interactive timeline | [`sreegjl/timelines@2119dbd1`](https://github.com/sreegjl/timelines/tree/2119dbd1487861221072c7dc36e793ff41f74caf) | [GPL-3.0](https://github.com/sreegjl/timelines/blob/2119dbd1487861221072c7dc36e793ff41f74caf/LICENSE) | External/reference tool initially. |
| 3D astronomy | [`CelestiaProject/Celestia@5f97614a`](https://github.com/CelestiaProject/Celestia/tree/5f97614a92dcdf63cf59cc65e38f77bcc97c822f) | [GPL-2.0](https://github.com/CelestiaProject/Celestia/blob/5f97614a92dcdf63cf59cc65e38f77bcc97c822f/COPYING) | Future export/viewing target; keep external. |
| Astronomy calculations | [`astropy/astropy@462ee8b8`](https://github.com/astropy/astropy/tree/462ee8b84c2a1677e26987626dd9dfa6554581ac) | [BSD-3-Clause](https://github.com/astropy/astropy/blob/462ee8b84c2a1677e26987626dd9dfa6554581ac/LICENSE.rst) | Preferred library for future astronomy automation. |
| Orbital/N-body checks | [`hannorein/rebound@bdfda4bd`](https://github.com/hannorein/rebound/tree/bdfda4bda4c0a4b6b0c707afae5a86d3341cbc93) | [GPL-3.0](https://github.com/hannorein/rebound/blob/bdfda4bda4c0a4b6b0c707afae5a86d3341cbc93/LICENSE) | External validator for unusual systems. |
| Exoplanet climate modelling | [`alphaparrot/ExoPlaSim@bb46316c`](https://github.com/alphaparrot/ExoPlaSim/tree/bb46316ca917e907b129b0d764b11a9119e0088e) | [GPL-2.0](https://github.com/alphaparrot/ExoPlaSim/blob/bb46316ca917e907b129b0d764b11a9119e0088e/LICENSE.TXT) | External validator for selected major worlds. |
| Stellar evolution | [`MESAHub/mesa@fd396fd7`](https://github.com/MESAHub/mesa/tree/fd396fd73d3f936da8063ffdf9d92361882eb557) | [LGPL-3.0](https://github.com/MESAHub/mesa/blob/fd396fd73d3f936da8063ffdf9d92361882eb557/LICENSE) | External/reference validator for deep-time stellar cases. |
| Link checking | [`lycheeverse/lychee@v0.24.2`](https://github.com/lycheeverse/lychee/releases/tag/lychee-v0.24.2) | [MIT or Apache-2.0](https://github.com/lycheeverse/lychee#license) | Verified Windows release binary used for this branch's link audit (tag object `e85aaf5524b2f808e63bae55e594c843220f10f2`, SHA-256 `32975d1493ee1a975d6bb41e4fb56fe419cb442ded628bb772ba2e614acfacad`); no binary or source is committed. |
| YAML parsing | [`yaml/pyyaml@6.0.3`](https://github.com/yaml/pyyaml/tree/49790e73684bebad1df05ef8d828fa12f685bffb) | [MIT](https://github.com/yaml/pyyaml/blob/49790e73684bebad1df05ef8d828fa12f685bffb/LICENSE) | Used from a temporary install to parse-check repository YAML; not a repository dependency. |
| JSON Schema validation | [`python-jsonschema/jsonschema@v4.26.0`](https://github.com/python-jsonschema/jsonschema/tree/v4.26.0) (tag `c87a9220`) | [MIT](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/COPYING) | Used from a temporary install to validate the V12 dataset; not a repository dependency. |

## Considered, not adopted

| Need | Project and observed revision | Verified licence | Decision |
|---|---|---|---|
| Fictional personal names | [`ironarachne/namegen@472ac3fe`](https://github.com/ironarachne/namegen/tree/472ac3fe67c734e89654dcad0293f6924fd2b87b) | [Apache-2.0](https://github.com/ironarachne/namegen/blob/472ac3fe67c734e89654dcad0293f6924fd2b87b/LICENSE) | Clearly licensed but list-based human names do not fit late SERVATI terminology. |

## Quarantined: no reusable licence established

These repositories may be technically relevant, but GitHub exposed no clear
SPDX licence that grants reuse during this review. Do not copy from them unless
licence provenance is later resolved.

- [`Jimbly/galaxy-gen@d18fa4ca`](https://github.com/Jimbly/galaxy-gen/tree/d18fa4ca397ad37140e5b41884021fd9694993d5)
- [`duchu-net/xenocide-world-generator@497bedaa`](https://github.com/duchu-net/xenocide-world-generator/tree/497bedaa03e9a247836050b03b1a13a58e8cb119)
- [`Azgaar/Armoria@9351aa69`](https://github.com/Azgaar/Armoria/tree/9351aa69ebc9ae52852311dea3f74cec28e67f6e)
- [`mewo2/naming-language@4abc8d39`](https://github.com/mewo2/naming-language/tree/4abc8d392f9e536f86d546d446201002528cffc0)
- [`Tw1ddle/MarkovNameGenerator@c62d781b`](https://github.com/Tw1ddle/MarkovNameGenerator/tree/c62d781b7d294c3110faf71c8c7f54691fdce236)

## Integration rules

1. Pin and record the exact upstream revision.
2. Read the actual licence file; repository visibility is not permission.
3. Prefer external use before vendoring code.
4. Record copied or derived files in `THIRD_PARTY.md` and retain all required
   notices.
5. Procedural output begins as DRAFT and never becomes canon automatically.
