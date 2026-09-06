# Version 12 Foundation

## Status and purpose

Version 12 is under development. Its proposed direction is particularisation:
to add concrete places, cultures, lineages, institutions, events, artefacts,
languages, ecologies, and records without replacing Version 11's authority or
turning SERVATI into generic space opera.

Every new lore item remains DRAFT until it passes the canon promotion gate.

## Repository architecture

```text
canon/          authority, promotion, and provenance controls
data/           machine-readable indexes and DRAFT datasets
docs/           editorial and technical foundation documents
drafts/v12/     human-readable V12 workshop material
research/       non-canon research and source-review quarantine
schemas/        SERVATI data profiles
templates/      controlled authoring templates
third_party/    required upstream licences and notices
```

Directories should be created only when real material exists.

## Quality gate for new lore

A proposed item must answer:

1. What verified SERVATI fact does it descend from?
2. Where and when does it exist, and how certain is that placement?
3. What custodial problem or environmental pressure shaped it?
4. What distinguishes it from nearby entries?
5. What does it preserve, neglect, or misunderstand?
6. What evidence supports its assigned canon status?
7. What scientific assumptions require checking?
8. Does it drift toward unsupported conquest, heroic-quest, alien-monster, or
   other generic space-opera conventions?

If those questions cannot be answered, the item remains DRAFT or is removed.

## Working-pack reconciliation

The source pack
`SERVATI_V12_GITHUB_FIRST_WORKING_PACK_R1.zip` (SHA-256
`e1fff0cf6231c2916b48f5f7f44c17d0b04336303ac5a34687c32685543b34ef`)
was inspected before repository changes.

Accepted and adapted:

- canon-status and provenance controls;
- the GitHub-first donor research, after independent repository and licence
  verification;
- an OnlyWorlds-derived structured-data direction;
- templates for entities and recovered records;
- the twelve-entry particularisation tranche, retained as DRAFT with
  source-unavailable grounding.

Quarantined or corrected:

- detailed V11 terms, chronology, lineages, and environments whose cited
  manuscript is not available for comparison;
- mismatched schema/data field names and status values;
- the undeclared root-world UUID, now explicitly marked as a DRAFT placeholder;
- operational status, blocker, next-action, and package-manifest files that do
  not belong in the lasting repository structure.
