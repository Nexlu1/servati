# Third-Party Material

SERVATI creative content and third-party material are kept under separate
licences.

## Included derivative material

The field vocabulary and entity structure in
`schemas/servati-dataset.schema.json` are derived in part from the base,
Location, and Event schemas in
[`OnlyWorlds/OnlyWorlds`](https://github.com/OnlyWorlds/OnlyWorlds/tree/ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f),
observed at commit `ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f`.

OnlyWorlds is licensed under the MIT Licence. Its required copyright and
permission notice is reproduced at `third_party/onlyworlds/LICENSE` and the
scope of the adaptation is documented at `third_party/onlyworlds/NOTICE.md`.
The derivative schema is distributed under those MIT terms.

## Referenced CI dependencies

The validation workflow invokes pinned releases of `actions/checkout`,
`actions/setup-python`, `check-jsonschema`, `PyYAML`, `yamllint`, and
`lychee-action`. Their source is not copied into this repository. Exact
revisions, licence links, adoption boundaries, and the rejected YAML action
wrapper are recorded in `docs/FOSS_TOOLING_REGISTER.md`.

## Referenced Codex dependencies

The Codex build acquires Quartz v5 and its configured plugins directly from
GitHub at exact commits. Their source is not committed to this repository. The
complete revision, licence, and role inventory is recorded in
`codex/SERVATI_CODEX_BUILD_MANIFEST.json`; Phase 2 adoption decisions are
documented in `docs/CODEX_PHASE2_FOSS_REGISTER.md`.

## Evaluated but not included

The projects in `docs/FOSS_TOOLING_REGISTER.md` are research candidates, not
bundled dependencies. Listing a project does not copy, endorse, or relicense
its code. Any future integration must add the exact upstream revision,
licence, attribution, and copied-file inventory here before release.
