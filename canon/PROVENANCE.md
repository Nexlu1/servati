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

## Working-pack rule

The SHA-256 hash identifies the exact pack reviewed. Pack assertions about
Version 11 remain `SOURCE-UNAVAILABLE` until the manuscript or an equivalent
stable source is present. New names and particulars from the pack remain DRAFT
even after their thematic basis is verified.
