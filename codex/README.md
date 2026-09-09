# SERVATI Codex

The Codex is a generated Quartz v5 encyclopedia. Version 11 prose is released
canon; every Version 12 record remains visibly `V12 DRAFT`. Do not edit generated
Markdown or HTML as source.

## Fast local loop

Requirements: Git and Python 3.12. The pinned V12 revision is on a separate
branch and must be present in the object database.

```sh
git fetch --no-tags origin v12-faiths-choirs-custody-wars-20260907
git cat-file -e "21b72ea0bbdaa4c8f9372270bb06b9501c5b9965:SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md"
git cat-file -e "5bd417299c4e99163404f655e569dcc2fc03789b:drafts/v12/tranche-03/choirs-custody-wars.md"
python -B -m py_compile codex/servati_codex.py codex/verify_servati_site.py
python -B codex/build_servati_content.py --repo . --out /tmp/servati-content
```

Generation succeeds only when `codex/servati_codex.py` matches committed
`HEAD`. Inspect `/tmp/servati-content/SERVATI_GENERATION_RESULT.json` and
`SERVATI_DEPTH_REPORT.json` before an integration checkpoint.

## Full local build

Use Linux or WSL with Git, Node 24, npm 10.9.2 or later, and Python 3.12. Start
from a committed approved Codex head with no tracked differences in build
inputs:

```sh
git rev-parse HEAD
git diff --exit-code HEAD -- codex .github/workflows/servati-codex-build.yml
git clone --filter=blob:none https://github.com/jackyzha0/quartz.git quartz-work
git -C quartz-work checkout --detach f1fba3fc55cbf60a60a5d09c95a49c042cdab63a
npm --prefix quartz-work ci
cp codex/quartz.config.yaml quartz-work/quartz.config.yaml
cp codex/custom.scss quartz-work/quartz/styles/custom.scss
cp codex/codex-random-modes.js quartz-work/quartz/static/codex-random-modes.js
python codex/build_servati_content.py --repo . --out quartz-work/content
python codex/manage_quartz_plugins.py acquire --manifest codex/SERVATI_CODEX_BUILD_MANIFEST.json --config codex/quartz.config.yaml --source-root quartz-work/plugin-sources --result quartz-work/SERVATI_PLUGIN_ACQUISITION_RESULT.json
(cd quartz-work && npm_config_package_lock=false npx quartz plugin install --from-config --concurrency 1)
(cd quartz-work && python ../codex/manage_quartz_plugins.py verify --manifest ../codex/SERVATI_CODEX_BUILD_MANIFEST.json --config quartz.config.yaml --source-root plugin-sources --installed-root .quartz/plugins --result SERVATI_PLUGIN_VERIFICATION_RESULT.json)
(cd quartz-work && npx quartz build --concurrency 2)
python codex/verify_servati_site.py --repo . --content quartz-work/content --output quartz-work/public --plugin-result quartz-work/SERVATI_PLUGIN_VERIFICATION_RESULT.json --result quartz-work/SERVATI_CODEX_BUILD_RESULT.json
```

Retain the generation, depth, plugin-verification, and final build-result JSON
files together. Native Windows plugin junctions do not satisfy the authoritative
symlink identity check; use Linux/WSL or the existing Actions workflow for that
gate.

## Maintenance

- Authority revisions: `servati_codex.py`, `verify_servati_site.py`, and the
  Phase 2 FOSS register.
- Quartz and plugin revisions: `SERVATI_CODEX_BUILD_MANIFEST.json`, the complete
  dependency inventory.
- Presentation: `quartz.config.yaml`, `custom.scss`, and
  `codex-random-modes.js`.
- Acceptance contract: `verify_servati_site.py`.

Update coupled pins and tests in one coherent change. Build locally, self-audit,
then use one meaningful GitHub checkpoint rather than one push per small edit.
