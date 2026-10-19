# Dataset Details and Evaluation Populations

## Current cohort and other dataset roles

The first cohort uses **CCIHP-derived custom person-level body/clothing GT** with corresponding CIHP DatasetNinja RGB. It is not an original native CIHP benchmark. MHP-v2 remains a provisional secondary fine-grained resource; a universally clean/primary dataset or application-wide taxonomy is not declared. PPSS is paused. No company CCTV is included or processed here.

| Asset | Local workspace-relative path | Content / public status |
|---|---|---|
| CCIHP annotation ZIP | datasets/CCIHP_icip.zip | 28,280 TRAIN and 5,000 VAL Category/Human/Instance annotation sets; RGB absent; external |
| DatasetNinja CIHP TAR | datasets/cihp-DatasetNinja.tar | Corresponding RGB/converted parts; it alone lacks native person ownership GT; external |
| MHP-v2 | datasets/LV-MHP-v2/ | Per-person parsing planes; original dataset/splits untouched; external |

Archive sizes/SHA256 and access limitations are in [ARTIFACTS.md](ARTIFACTS.md). The CCIHP conversion is PARTIALLY_COMPATIBLE with CIHP, not VERIFIED_NATIVE_COMPATIBLE. Automated label/dimension/ownership-association checks do not prove that every physical person/class boundary is annotated correctly. Human-review and assistant-review evidence are distinguished in the historical reports.

## Frozen first-cohort populations

| Population | Images | G_loc | G_sem | Role |
|---|---:|---:|---:|---|
| main | 4,961 | 17,434 | 17,390 | Exact source-overlap-controlled membership |
| reference | 5,000 | 17,548 | 17,504 | Original released validation population |

The main excludes the predeclared 39 train/validation JPEG-byte overlap members, not failures discovered after inference. Controlled membership is not proof of no near duplicates or checkpoint training exposure. The two populations overlap and are not independent samples. Image IDs and denominators remain traceable through [population metadata](cohorts/first_cpi_t3b/POPULATIONS.json) and the original bound config/manifests. GT pixel arrays and detailed person-binding artifacts remain external.

## Semantic and ownership policy

CCIHP Category0/Human0 is outside the annotated person foreground; domain rules come from accepted released annotations, not from predictions. Known semantic target with Human0 is globally usable but per-person VOID_OWNER_UNKNOWN. Human-positive/category0 is unresolved semantic support and is void semantically under the accepted recipe. Unknown22 and unsupported target concepts are explicitly void, never silently background. All original values and identities are preserved.

The native CCIHP taxonomy differs from CIHP: for example CIHP ID6 is Dress while CCIHP ID6 is Face Mask. CIHP/LIP ID10 also differs (torso skin versus jumpsuit). The explicit [accepted mapping](taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json) produces BG0 and Face region1, Exposed torso2, Exposed arms3, Exposed legs4, Coarse garments5 and Footwear6. Display name Face region does not change numeric ID1. Accessories outside this cohort are unsupported, not evaluated as if predicted by all models.

G_loc and G_sem are declared GT eligibility sets; G_sem is a subset of G_loc. GT masks may overlap and keep instance identity. Localization boxes are GT-body support under the frozen policy, not arbitrary anatomical silhouettes from all carried-object classes. FP/FN are relative to released annotations; FP does not prove that a physical person is absent.

## Earlier MHP-v2 limitations

The four original defective JPEGs remain immutable. Approved readable views contain 15,400 TRAIN, 4,999 VAL/13,257 GT persons, and exact-overlap-controlled readable VAL 4,347/11,408 persons. These are not an unqualified official 5,000-image result. Exact RGB duplication and uncertain GT ownership remain separate limitations; this cohort computes no MHP-v2 validation score.
