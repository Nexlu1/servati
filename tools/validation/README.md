# Repository Validation

The GitHub Actions workflow reuses maintained FOSS for general validation:

- `check-jsonschema` validates JSON data and the workflow definition;
- `yamllint` parses and lints tracked YAML;
- `lychee-action` checks Markdown links and fragments; and
- `validate_servati.py` contains only project-specific canon, provenance,
  reference, chronology, and licence invariants.

Direct Python tools are pinned in `requirements.txt`. GitHub Actions are pinned
to immutable commit SHAs in `.github/workflows/validate.yml`; readable release
tags and licence decisions are recorded in `docs/FOSS_TOOLING_REGISTER.md`.

## Local checks

From the repository root, install the validation requirements into an isolated
environment, then run:

```sh
check-jsonschema --check-metaschema schemas/servati-dataset.schema.json
check-jsonschema --schemafile schemas/servati-dataset.schema.json data/drafts/*.json
yamllint --strict --config-file tools/validation/yamllint.yml .github data tools/validation
check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/*.yml
python tools/validation/validate_servati.py
```

Run lychee v0.24.2 separately for the same link check used in CI:

```sh
lychee --no-progress --include-fragments --max-concurrency 8 './**/*.md'
```
