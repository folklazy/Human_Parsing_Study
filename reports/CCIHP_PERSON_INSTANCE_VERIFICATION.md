# CCIHP Person Instance Verification — Stage 0E Continuation

**Sample structural/lossless fidelity: PASS_WITH_WARNINGS. Dataset-wide physical correctness: NOT_VERIFIED. Native CIHP target equivalence: BLOCKED.** Source is actual `datasets/CCIHP_icip.zip`; previous missing-source report archived

## What ran

30 frames: 25 TRAIN + 5 VAL integrity-only; native maps90 decode/CRC/dimensions PASS; **96 image-local human IDs / 840 attribute instances**, every sampled attribute instance has exactly one human and semantic class. Per-person canonical view preserves full source human support, semantic categories (including unknown22), uint16 attribute IDs, original dimensions, source hashes and unassigned regions; reconstruct all three original maps **30/30 exact**

Human labels identify source-defined people inside each image; no temporal identity claim or automatic guarantee one physical person per ID across the dataset. Source map can store only one owner at each pixel; no recovered hidden/amodal masks or inferred neighboring person identity

## Case 1 — Nearby people control: 0002190

![CCIHP same-frame human/category comparison](../outputs/visualizations/stage0e-ccihp-native-20261012T045912Z/case_0002190.png)

Observation: foregroundสองคนถูกแยก Human IDs1/2, boundaries align with visible image regions; CIHP/CCIHP semantic panelsใกล้กัน แต่ raw categoriesต่าง361pixelsและ FG/BGต่าง7pixels

Interpretation: demonstrates useful local person ownership even where global semantics look similar; equality of visual appearance is not native-human equivalence Original native Human_ids unavailable, so cannot certify original person mask/order/completeness

## Case 2 — Crowded foreground: 0005008

![CCIHP group comparison](../outputs/visualizations/stage0e-ccihp-native-20261012T045912Z/case_0005008.png)

Observation: Human IDs1–7 separate the seven dominant foreground people. Source DatasetNinjaมี53part objects;52อยู่ในหนึ่ง humanครบsupportและ1ทับหลาย human IDs มองเห็น background peopleด้วยแต่ source completeness policyยังไม่verified

Interpretation: physical alignmentของforegroundตัวอย่างนี้ช่วยสนับสนุนcustom GT usefulness แต่ mixed-source native CIHP object-to-person associationยังไม่lossless/unambiguous ห้ามแก้เป็น majority ownerแล้วเรียก original native GT

## Case 3 — Clothing/accessory boundary changes: 0012008

![CCIHP garment comparison](../outputs/visualizations/stage0e-ccihp-native-20261012T045912Z/case_0012008.png)

Observation: Human IDs1–3 separate dominant foreground people; originalRGB panelregionเดียวกัน Category panels visibly differ over upper garments/accessory regions. Raw differences46,665pixels; FG/BGdifferences4,905pixels. Of30 CIHP part objects,29have one complete owner and1covers multiple CCIHP human IDs

Interpretation: annotation definitions/region edits change evaluation target despite same source image ไม่ตีความว่า parserแม่นขึ้น/แย่ลง เพราะไม่มี parser inference หรือ independent truth adjudication

## Coverage and unresolved conventions

Sampled category-foreground outside humans0pixels; attribute-instance outside humans0; human support without category12pixelsใน3images ไม่เติมlabelsหรือเรียกerrorอัตโนมัติ TRAIN0033810มี2pixelsค่า22นอกdocumented inventory; retain values/hash/coordinates

Visible-person completeness, actual occlusion/overlap policyและannotation-error prevalence **NOT_VERIFIED** Shared clothes/adjacent peopleไม่เป็นproof annotation error Two single-valued maps cannot provide amodal overlap ground truth; no GT masks reconstructed with YOLO or grouping heuristics

[Full evidence](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/BOUNDED_CROSS_DATASET_COMPARISON.json), [fidelity](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/CCIHP_GT_FIDELITY.json), [main audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md)
