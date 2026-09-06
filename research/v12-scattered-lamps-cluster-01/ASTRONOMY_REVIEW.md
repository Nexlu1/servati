# DRAFT — Astronomy Review for Scattered Lamps Cluster 01

**Editorial status:** DRAFT research layer. Nothing here is canon.

## GitHub-first audit

The repository's [existing FOSS register](../../docs/FOSS_TOOLING_REGISTER.md)
was checked before any system detail was proposed. Live GitHub metadata was
rechecked on 2026-09-06. The previously recorded default-branch revisions still
matched:

- [Astropy `462ee8b8`](https://github.com/astropy/astropy/tree/462ee8b84c2a1677e26987626dd9dfa6554581ac)
  — BSD-3-Clause; maintained and preferred for units, coordinates, constants,
  and later quantitative checks;
- [REBOUND `bdfda4bd`](https://github.com/hannorein/rebound/tree/bdfda4bda4c0a4b6b0c707afae5a86d3341cbc93)
  — GPL-3.0; maintained external N-body validator when an orbital architecture
  actually exists;
- [accrete-starform-stargen `f029fbf0`](https://github.com/zakski/accrete-starform-stargen/tree/f029fbf06bbedb6dbedbaee43c3686a8a1d3745d)
  — Apache-2.0; useful algorithm history, but its old formation and climate
  assumptions cannot establish scientific truth; and
- [Starmap `f5a8b1a8`](https://github.com/yudhanjaya/Starmap/tree/f5a8b1a8af61b83dc2656f31164e4210e06852db)
  — MIT; useful story scaffolding, not a scientific system validator.

The fresh search also evaluated:

- [FrunkQ/star-system-generator `813eb19b`](https://github.com/FrunkQ/star-system-generator/tree/813eb19b0f1cab8be40b4cc5a737f993440c5c8e)
  — GPL-3.0 and actively maintained, but self-described as “close enough” for
  role-playing use rather than research-grade validation; and
- [Sphinkie/StarGen-II `6ad71da2`](https://github.com/Sphinkie/StarGen-II/tree/6ad71da251acb46f2623a0c700d1069faf15950a)
  — MIT, but a 2006 StarGen fork at an observed 2023 revision.

No source or generated output from these projects is committed. No generator
was run. A plausible random output would add false precision before SERVATI has
settled transport physics, stellar context, or even whether every Lamp is tied
to a conventional star system.

## Review boundary

The cluster is relational, not yet spatial. Names such as “Cluster K-6” and
“Pelagic Seven” are DRAFT registry descendants, not catalogue coordinates. No
absolute date, duration, distance, star class, planet mass, orbit, atmosphere,
or travel speed is asserted.

The machine-readable entries separate broad physical plausibility from claims
that still require review. `plausible` means only that the qualitative concept
does not immediately contradict ordinary physics. It does not promote the
setting, measurement, or mechanism to canon.

## Candidate settings and open work

| DRAFT setting | Constrained proposal | Scientific uncertainty blocking detail |
|---|---|---|
| Relay Twelve Primary System | A vacuum archive habitat with exposed heat rejection and a clear thermal view | Heat load, radiator area and temperature, stellar spectrum, orbit, radiation dose, station-keeping |
| Transfer Cluster K-6 Debris System | A dusty, excavated airless minor body in a debris-bearing environment | Size, cohesion, spin, composition, seismic response, excavation stability, orbit and impact regime |
| Pelagic Seven Planet-Moon System | An ocean-bearing moon with an elevated Lamp and submerged vault access | Surface versus subsurface ocean, pressure, chemistry, gravity, tides, radiation, energy and access engineering |
| Seed Reserve Thirty-One Cold-Body System | A buried or shielded reserve using a cold exterior for thermal margin | Power, waste heat, radiation shielding, repair ecology, storage modes, sample viability and inspection cost |
| No-Arrival Interstellar Reach | A distributed beacon chain between unidentified route anchors | Transport model, distance, reference frame, clock synchronisation, power, navigation and endpoint motion |
| Transfer Site Nine Junction Environment | An engineered junction with damaged frames and comparison infrastructure | Planetary/orbital/free-space category, debris dynamics, shielding, traffic control and artificial-gravity assumptions |

## Required future audit

Before any numerical system record is proposed:

1. identify the minimum scene or preservation question that needs a number;
2. record the transport and energy assumptions separately from V11 canon;
3. use Astropy quantities and constants for dimensional work;
4. use REBOUND externally if multi-body stability or debris dynamics matter;
5. retain inputs, tool revision, licence, seed where relevant, and output as
   DRAFT research provenance; and
6. have a scientifically qualified reviewer assess the claim before promotion.

The absence of numbers in this tranche is deliberate uncertainty control, not
a claim that the systems can never be specified.
