# OnlyWorlds attribution

- Upstream: <https://github.com/OnlyWorlds/OnlyWorlds>
- Revision: `ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f`
- Licence: MIT (see `LICENSE` in this directory)
- Upstream files consulted: `schema/base_properties.yaml`,
  `schema/location.yaml`, and `schema/event.yaml`
- SERVATI derivative: `schemas/servati-dataset.schema.json`

SERVATI retains OnlyWorlds base names (`Id`, `Name`, `Description`,
`Supertype`, `Subtype`, `World`) and the relevant Location/Event grouping
patterns. The derivative uses ordinary JSON Schema types and adds a separate
SERVATI metadata object for canon, provenance, chronology, and science review.
