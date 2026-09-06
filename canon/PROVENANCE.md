# Provenance Policy

Every lore claim should make its evidence chain inspectable without confusing
an editorial source with an in-universe source.

## Source kinds

- `released-manuscript` — an identified public edition and page, section, or
  stable fragment.
- `repository-baseline` — a fact already asserted by a named repository commit.
- `recovered-record` — an in-universe record presented as surviving evidence.
- `archaeological-fragment` — material evidence inside the setting.
- `doctrinal-source` — a belief or teaching attributed to an in-universe group.
- `editorial-reconstruction` — an explicit synthesis by the project editor.
- `generated-candidate` — machine-assisted or procedural material; always
  DRAFT on entry.
- `research-source` — real-world science, history, language, or tooling input.
- `working-pack` — material received in a development pack but not independently
  verified against the source it claims.

## Minimum record

Structured entries record `source_kind`, `source_ref`, `source_location` when
available, `verification`, and a note describing exactly what the source
supports. A citation does not support adjacent details automatically.

## Authoritative Version 11 source

The released source is
[`SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md`](../SERVATI_V11_AUTHORITATIVE_MANUSCRIPT.md),
edition **Version 11 — Differentiation and Deep-Time Expansion Edition**,
SHA-256
`2f7d094389ee3c4ed9d5c3364ad1fb091e4d3634966a6674951672f26ef8079d`.
It is stored as Markdown because it is modest in size, diffable, and permits
stable section-level review. Publication-format exports may be attached to
GitHub Releases later without displacing this source text.

## Working-pack rule

The SHA-256 hash identifies the exact pack reviewed. Its V11-derived assertions
must cite the authoritative manuscript, not the pack, once directly compared.
Only the exact manuscript-supported basis becomes `VERIFIED`; new names and
particulars from the pack remain DRAFT even when that basis is verified.
