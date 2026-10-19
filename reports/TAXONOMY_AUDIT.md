# Native Taxonomy and Representability — Stage 0D

> Current update — 15 October 2026: the body below is the historical initial audit. Current acquisition/inference status is in [Model Compatibility](MODEL_COMPATIBILITY_REPORT.md), [current artifact index](../provenance/CURRENT_STUDY_ARTIFACTS.json), and [handoff validation](APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md). Old zero-checkpoint/zero-smoke statements are historical; scientific taxonomy acceptance remains pending.

## Historical initial-audit evidence

**Draft only.** No common projection, denominator or model ranking is frozen. The [matrix](../taxonomy/TAXONOMY_REPRESENTABILITY_MATRIX.csv) contains **472 cells: 59 MHP-native concepts × 8 candidate variants**, including background and the license-excluded Sapiens2 column explicitly marked UNKNOWN/outside the executable cohort.

Native label sources were parsed without importing model code. MHP-v2 is 59 semantic IDs including background; M2FP adds auxiliary Human 59 (60 training/output categories), which is not a 59th foreground semantic body/clothing class. CPI MHP configs declare 59 parsing labels. D2FP CIHP has 20 semantic labels plus auxiliary Human 20; its LIP variant has 20 semantic labels. SCHP-LIP has 20; FASHN has 18. These are **source-taxonomy findings**, not loaded-checkpoint output verification.

Individual source definitions and fingerprints are under [taxonomy/native](../taxonomy/native). D2FP-LIP labels come from its own registration source, not an assumed copy of SCHP. All MHP native pixels were checked against IDs 0–58; alpha is excluded.

## Semantic problems that cannot be solved by a name lookup

| Concept | Compatibility issue | Draft handling |
|---|---|---|
| Face/head | A head or face+neck label need not equal facial skin | Exact source Face label concepts still need boundary-scope review; no head→face shortcut |
| Torso | MHP torso-skin differs from generic anatomic torso; D2FP CIHP and LIP differ at ID 10 | FASHN torso is AMBIGUOUS; do not treat every same ID/name as the same class |
| Arms/hands | MHP has separate side-specific hands; LIP lacks independent hands | Preserve distinctions in rich cohorts; candidate coarse merges must be shared |
| Legs/stockings | Bare legs and dressed regions can have different annotation scope | Keep clothing/body groups separate until approved |
| Feet/footwear | FASHN Feet is not documented as identical to MHP Shoes | No automatic shoe mapping; use a footwear-capable subset |
| Upper clothes | Tee/polo/singlet/jacket/coat are merged by coarse parsers | Report retained fine-class coverage; do not invent subtype predictions |
| Dress/jumpsuit/robe | One whole-body label cannot become upper/lower clothes through a lookup | Retain/hold whole garments; no GT-guided split |
| Accessories/carried items | MHP includes umbrella, ball, bats, cases etc; LIP/FASHN capacity differs | Do not silently map unsupported GT to background or pretend jewelry covers all accessories |
| Background/ownership | Native semantic crop output can include neighboring people | Native background is not proof of target-person ownership; retain ambiguity and raw outputs |

## Core and extended drafts

[COMMON_HP_CORE_DRAFT.yaml](../taxonomy/COMMON_HP_CORE_DRAFT.yaml) lists candidate coarse face, hair, arms/hands/legs, clothing and dress concepts. The provisional universal subset is only face/hair; it is too narrow to select a useful complete body/clothing parser alone. This is an explicit limitation, not a universal leaderboard.

[COMMON_HP_EXTENDED_DRAFT.yaml](../taxonomy/COMMON_HP_EXTENDED_DRAFT.yaml) proposes separate MHP-native, LIP-style, FASHN-coarse and footwear cohorts. Each cohort requires the same GT projection and valid-domain denominator for all members. The matrix's EXACT means a source concept is available; it does not prove identical annotation practice or checkpoint correctness. COARSE_ONLY is not a fine-label score authorization. AMBIGUOUS/UNKNOWN entries remain unresolved.

Support/coverage can be calculated from the audited GT [class-support table](../metrics/DATASET_NATIVE_CLASS_SUPPORT.csv). Final retained-foreground fractions are **not published as approved coverage**, because the class/domain projection remains open. Future projection must emit each cohort's retained native labels, GT pixel/person/image support, excluded semantics and unmapped-prediction burden. Do not choose different favorable valid domains per model.

Analysis groups are body, clothing, footwear and accessories/carried objects. No parser is preassigned as a body or clothing expert. Hybrid routing is a future hypothesis requiring real individual predictions and separate approval.

## Validation and limits

Every MHP concept/candidate cell has an allowed representability state; every background-capable variant explicitly records background ID 0. Taxonomy YAML remains DRAFT, `mapping_frozen=false`, `evaluation_authorized=false`. Synthetic unsupported-GT rejection and explicit unsupported-prediction accounting passed. Source labels/limited conceptual proposals do not resolve dataset ownership errors, weight exposure or clinical/deployment semantics.
