# Schemas

`servati-dataset.schema.json` is a JSON Schema Draft 7 profile for SERVATI's
structured datasets. It reuses selected OnlyWorlds Base, Location, Event,
Collective, Institution, Object, Narrative, Language, Species, and Relation
vocabulary while adding SERVATI-specific canon, provenance, relative-sequence,
preservation-problem, and science-review controls.

OnlyWorlds uses `World` both for the base world UUID and for type-specific
context groups. The profile retains the base UUID and omits the colliding
groups; explicit Relation entries preserve cross-entity context without a
SERVATI-only replacement ontology.

The schema is an interoperability profile, not a fork of the complete
OnlyWorlds standard. Upstream attribution is recorded in
`../third_party/onlyworlds/NOTICE.md`.

The schema is distributed under the OnlyWorlds MIT terms reproduced in
`../third_party/onlyworlds/LICENSE`.
