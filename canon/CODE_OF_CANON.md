# Code of Canon

SERVATI deliberately contains incomplete records and incompatible
interpretations. Canon status records what kind of claim an entry is; source
verification separately records whether editors can inspect the evidence.

## Canon statuses

- **CORE** — a locked setting fact inherited from an authoritative released
  baseline or deliberately promoted by review.
- **RECORDED** — an in-universe primary record survives; the record may still
  be incomplete or biased.
- **RECONSTRUCTED** — the best current reconstruction from multiple fragments.
- **DISPUTED** — two or more materially credible accounts conflict.
- **DOCTRINAL** — a faith, culture, institution, or civilisation teaches the
  claim; this does not make it objective history.
- **APOCRYPHAL** — legend, doubtful tradition, corrupted transmission, or
  deliberately uncertain account.
- **DRAFT** — workshop material with no canon authority.

## Source-verification states

- **VERIFIED** — the cited source and location were inspected.
- **SOURCE-UNAVAILABLE** — a source is claimed but is not presently reviewable.
- **PENDING-REVIEW** — the source is available but the claim has not completed
  editorial comparison.
- **NOT-APPLICABLE** — the item is an editorial rule or administrative record,
  not a lore claim.

## Rules

1. New lore may not silently overwrite CORE material.
2. Generated or newly particularised lore begins as DRAFT.
3. `SOURCE-UNAVAILABLE` material cannot be promoted to CORE.
4. A contradiction is recorded, not erased, when both sides have evidential
   value.
5. Real-world scientific claims must be separated from speculative
   assumptions.
6. A later civilisation's belief about humanity is not automatically a fact
   about humanity.
7. Provenance must identify a stable source, source location where possible,
   and the nature of the claim's dependence on it.
8. Third-party material must pass licence and attribution review before use.
9. Retcons require an explicit rationale and visible change record.

## Promotion gate

A DRAFT may change status only in a reviewed pull request that:

- identifies the authoritative evidence;
- records source verification as VERIFIED;
- explains compatibility with Version 11;
- resolves or records contradictions;
- completes relevant science and licence checks; and
- names the approving editor in the pull-request record.
