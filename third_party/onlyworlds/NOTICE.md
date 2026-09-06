# OnlyWorlds attribution

- Upstream: <https://github.com/OnlyWorlds/OnlyWorlds>
- Revision: `ed84fa19c15c5bfb18019245faacdbdcb7cd9e0f`
- Licence: MIT (see `LICENSE` in this directory)
- Licence SHA-256:
  `ab9469f20388ba53771315ed7cb94461d5e3de6e0113bd8f0280f3364434fe18`
- Upstream files consulted: `schema/base_properties.yaml`,
  `schema/location.yaml`, `schema/event.yaml`, `schema/collective.yaml`,
  `schema/institution.yaml`, `schema/object.yaml`, `schema/narrative.yaml`,
  `schema/language.yaml`, `schema/species.yaml`, and `schema/relation.yaml`
- SERVATI derivative: `schemas/servati-dataset.schema.json`

SERVATI retains OnlyWorlds base names (`Id`, `Name`, `Description`,
`Supertype`, `Subtype`, `World`) and selected type-specific grouping patterns.
The upstream schemas also use `World` as a type-specific object, which collides
with the base UUID field; SERVATI omits those nested groups and uses explicit
Relation entries for cross-entity context. The derivative adds a separate
SERVATI metadata object for canon, provenance, relative chronology,
preservation problems, and science review.
