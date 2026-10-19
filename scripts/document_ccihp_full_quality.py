"""Evidence-only Stage0F reports, immutable archives, draft protocol, validation."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import csv, hashlib, json, subprocess, sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parent;sys.path.insert(0,str(ROOT))
from audit_ccihp_full_quality import sha, stat, write_json

NAMES=['Background','Hat','Hair','Glove','Sunglasses/Glasses','UpperClothes','FaceMask','Coat','Socks','Pants','Torso-skin','Scarf','Skirt','Face','Left-arm','Right-arm','Left-leg','Right-leg','Left-shoe','Right-shoe','Bag','Others','UNKNOWN_UNDOCUMENTED_22']

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());run=ROOT/active['run_path'];rid=active['run_id']
    full=json.loads((run/'FULL_STRUCTURAL_AUDIT.json').read_text());agg=full['aggregate'];sample=json.loads((run/'TRAIN_REVIEW_SAMPLE.json').read_text())
    package=json.loads((run/'REVIEW_PACKAGE.json').read_text());near=json.loads((run/'NEAR_DUPLICATE_SCREEN.json').read_text())
    dup=json.loads((run/'EXACT_DUPLICATES.json').read_text());pop=json.loads((run/'VALIDATION_POPULATIONS_DRAFT.json').read_text())
    cross=json.loads((run/'CROSS_SOURCE_CONFLICT_REVIEW.json').read_text());before=json.loads((run/'BEFORE.json').read_text())
    rows=[json.loads(x) for x in (run/'IMAGE_AUDIT.jsonl').open()];lookup={(r['split'],r['image_id']):r for r in rows}
    revisions=[];stamp=datetime.now(timezone.utc).isoformat()
    def publish(rel,content,reason):
        p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);old=sha(p) if p.exists() else None;arch=None
        if p.exists():
            arch=Path('reports/archive')/rid/rel;q=ROOT/arch;q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(p.read_bytes())
            assert sha(q)==old
        p.write_text(content.rstrip()+'\n')
        revisions.append({'original_relative_path':rel,'archive_relative_path':str(arch) if arch else None,'sha256_before':old,'sha256_after':sha(p),'timestamp_utc':stamp,'reason':reason})
    totals=Counter()
    for v in agg.values():totals.update(v['counts'])
    classfile=run/'CLASS_DISTRIBUTIONS.csv'
    with classfile.open('x',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=['split','class_id','name','pixels','image_occurrences','pixel_denominator','pixel_share_pct','semantic_status']);wr.writeheader()
        for s,v in agg.items():
            labels=sorted(set(range(23))|{int(k) for k in v['classes']})
            for k in labels:
                wr.writerow({'split':s,'class_id':k,'name':NAMES[k] if k<len(NAMES) else 'UNKNOWN','pixels':v['classes'].get(str(k),0),
                             'image_occurrences':v['class_images'].get(str(k),0),'pixel_denominator':v['pixels'],
                             'pixel_share_pct':100*v['classes'].get(str(k),0)/v['pixels'],'semantic_status':'UNRESOLVED' if k>21 else 'README_DECLARED'})
    stats={}
    for split in agg:
        rr=[r for r in rows if r['split']==split]
        pp=[]
        for line in (run/'PERSON_AUDIT.jsonl').open():
            x=json.loads(line)
            if x['split']==split:pp.append(x)
        def quant(vals):
            return {name:float(v) for name,v in zip(['min','p5','p25','median','p75','p95','max'],np.percentile(vals,[0,5,25,50,75,95,100]))} if vals else {}
        stats[split]={'images':len(rr),'native_GT_persons':len(pp),'width':quant([r['wh'][0] for r in rr]),'height':quant([r['wh'][1] for r in rr]),
                      'persons_per_image':quant([r['person_count'] for r in rr]),'person_mask_area':quant([p['area_pixels'] for p in pp]),
                      'bbox_width':quant([p['bbox_width'] for p in pp]),'bbox_height':quant([p['bbox_height'] for p in pp]),
                      'bbox_occupancy':quant([p['occupancy_ratio'] for p in pp]),'aspect_ratio':quant([p['bbox_width']/p['bbox_height'] for p in pp]),
                      'small_mask_below_1pct_persons':sum(p['area_fraction']<.01 for p in pp),
                      'bbox_intersection_image_count':sum(r['bbox_intersection_pairs']>0 for r in rr),
                      'bbox_proxy_not_occlusion':True,'human_max_ID':max(max(r['human_labels']) for r in rr),
                      'attribute_instance_max_ID':max(r['instance_max'] for r in rr)}
    write_json(run/'DESCRIPTIVE_STATISTICS.json',stats)
    unknown=[r for r in rows if r['counts']['unknown_category_pixels']];gaps=[r for r in rows if r['counts']['human_without_category']]
    warning_summary={'unknown_category':{'pixels':totals['unknown_category_pixels'],'images':len(unknown),'labels':sorted({k for r in unknown for k in r['unknown_ids']}),
                        'by_split':{s:{'images':sum(r['split']==s for r in unknown),'pixels':agg[s]['counts']['unknown_category_pixels']} for s in agg}},
                     'human_without_category':{'pixels':totals['human_without_category'],'images':len(gaps),
                        'by_split':{s:{'images':sum(r['split']==s for r in gaps),'pixels':agg[s]['counts']['human_without_category']} for s in agg}},
                     'known_train_0033810':lookup[('Training','0033810')],
                     'all_anomalies':'ANOMALIES.jsonl','confirmed_physical_person_errors':'NOT_ESTIMATED_NOT_HUMAN_REVIEWED'}
    write_json(run/'ANNOTATION_WARNINGS.json',warning_summary)
    # Source PNG identity differences for exact RGB reuses; byte equality is not ID-invariant semantic equivalence.
    comparisons=[]
    for group in dup['decoded_RGB']['duplicate_groups']:
        sets={s for s,i in group['members']}
        if sets!={'Training','Validation'}:continue
        anchor=next(lookup[(s,i)] for s,i in group['members'] if s=='Training')
        for s,i in group['members']:
            if s!='Validation':continue
            val=lookup[(s,i)]
            comparisons.append({'train_id':anchor['image_id'],'validation_id':i,'RGB_decoded_sha256':group['sha256'],
                                 'same_person_count':anchor['person_count']==val['person_count'],
                                 'PNG_byte_identity_by_component':{a['component']:a['sha256']==b['sha256'] for a,b in zip(anchor['source_maps'],val['source_maps'])},
                                 'not_person_id_invariant_semantic_equality_test':True})
    write_json(run/'DUPLICATE_GT_IDENTITY_DIAGNOSTICS.json',{'comparisons':comparisons,'native_maps_repaired':False,'no_memorization_claim':True})
    path=str(run.relative_to(ROOT));prefix='../'+path
    table='\n'.join(f"| {s} | {v['images']:,} | {v['persons']:,} | {v['instances']:,} | {v['pixels']:,} |" for s,v in agg.items())
    count_table='\n'.join(f"| {k} | {agg['Training']['counts'].get(k,0):,} | {agg['Validation']['counts'].get(k,0):,} |" for k in sorted(totals))
    class_table='\n'.join(f"| {k}: {name} | {agg['Training']['classes'].get(str(k),0):,} | {agg['Validation']['classes'].get(str(k),0):,} | {agg['Training']['class_images'].get(str(k),0):,} | {agg['Validation']['class_images'].get(str(k),0):,} |" for k,name in enumerate(NAMES))
    integrity=f'''# CCIHP — Full Quality Audit Stage 0F

**Structural audit: {full['status']}; physical-person annotation quality: HUMAN REVIEW PENDING.** Run `{rid}`. งานที่อนุมัติคือการตรวจ dataset และเตรียม review ไม่ใช่ parser benchmark

## ขอบเขตและ provenance

ใช้ `datasets/CCIHP_icip.zip` สำหรับ GT และ `datasets/cihp-DatasetNinja.tar` สำหรับ RGB ที่ผู้เขียนระบุว่าใช้ร่วมกับ CIHP อ่านจาก archive โดยตรง ไม่แตก/เปลี่ยน source ไม่ตรวจ Color/Pattern/Size pixels

SHA256 archive เดิม: CCIHP `{full['prior_archive_sha256']['CCIHP']}`; DatasetNinja `{full['prior_archive_sha256']['CIHP_DatasetNinja']}` ใช้ CRC/SHA ledger ที่ตรวจครบใน Stage 0E/preflight และตรวจ ledger hash + archive stat ก่อน/หลัง ไม่ทำ complete ZIP CRC/TAR integrity ซ้ำ Required PNG และ RGB ที่อ่านรอบนี้เทียบ member SHA กับ ledger จริง

## Image-level และ person-level denominators

| Split | Images | Native Human IDs (image-local) | Attribute instances | Source pixels |
|---|---:|---:|---:|---:|
{table}

ตรวจ required PNG **{full['required_PNGs']:,} ไฟล์**: verify PNG stream แล้ว load pixels, dtype, label inventory, dims และ association อ่านครั้งละภาพ ไม่โหลด masks ทั้งชุดพร้อมกัน RGB strict full load {sum(r.get('RGB_decode')=='PASS' for r in rows):,}/{len(rows):,}; dimensions match {sum(r.get('RGB_GT_dimensions_match',False) for r in rows):,}/{len(rows):,}. Decode/dimension errors **{len(full['errors'])}**

**จำนวน native Human IDs ไม่ใช่จำนวน physical persons ที่มนุษย์รับรองแล้ว** คนเดียวอาจถูกแบ่ง ID หรือคนหลายคนอาจแชร์ ID ต้องใช้ review แยก Instance_ids เป็น attribute instances ไม่ใช่ person IDs

[Full per-image ledger]({prefix}/IMAGE_AUDIT.jsonl), [person areas/boxes]({prefix}/PERSON_AUDIT.jsonl), [statistics/quantiles]({prefix}/DESCRIPTIVE_STATISTICS.json), [aggregate evidence]({prefix}/FULL_STRUCTURAL_AUDIT.json)

## Cross-map support

| Pixel condition | TRAIN | VALIDATION |
|---|---:|---:|
{count_table}

Association conflicts: TRAIN {agg['Training']['association_conflict_instances']:,} instances/{agg['Training']['association_conflict_images']:,} images; VAL {agg['Validation']['association_conflict_instances']:,}/{agg['Validation']['association_conflict_images']:,}. ตรวจแต่ละ positive Instance ID ว่ามี Human ID และ Category ID เดียวหรือไม่ ไม่ majority-assign หรือ relabel

## Undocumented labels และ background gaps

พบ labels นอก README **{warning_summary['unknown_category']['labels']}**, {len(unknown):,} images/{totals['unknown_category_pixels']:,} pixels. TRAIN0033810 ยังคง Category22 ที่ 2 pixels ตามต้นฉบับ แต่ไม่ได้เป็นกรณีเดียว ห้ามอ้างว่าทั้ง dataset มี unknown เพียง 2 pixels

Human>0 แต่ Category0 **{len(gaps):,} images/{totals['human_without_category']:,} pixels** ขยายผลจาก 12 pixels ใน 30-image sample เดิม ไม่เปลี่ยน observation เดิมให้เป็น dataset-wide count เก็บทุกพิกเซลไว้ รวมบริเวณที่ Instance0

ความต่าง support เป็น **automated structural flags** ไม่ยืนยัน missing person/wrong body class ไม่ตีความ Category0 ใน Human mask เป็น corrupted RGB, occlusion หรือ void ที่ทราบนิยามแล้ว [Warning ledger]({prefix}/ANNOTATION_WARNINGS.json), [all affected images/coordinates]({prefix}/ANOMALIES.jsonl)

**Policy proposal — ยังไม่ freeze:** ขอคำอธิบาย Category22 จาก release author; เก็บ raw22 แยกจาก background. ถ้าจะประเมิน known-label subset ใช้ explicit UNKNOWN/VOID domain เดียวกันทุก model ใน cohort และรายงาน retained pixels/persons ไม่ทำ unknown→BG. Human-with-category0 ต้องเสนอ human-mask denominator sensitivity เทียบ semantic-FG denominator โดยตั้งชื่อคนละ metric ไม่ซ่อนให้เป็น policy เดียว

## Native taxonomy และ distribution

README archive ระบุ BG0 + 21foreground (1..21), ไม่ได้กำหนด22 บทความรุ่น publication ใช้19semantic labels และ20 **characteristic** classes; 20ดังกล่าวไม่ใช่หลักฐานว่า Category_ids มี20foregroundเสมอ Author datacard header/countและรายการปัจจุบันไม่สอดคล้องครบ Generator default class_num21/loop1..20 และ evaluator remap gt>=num_classes→0 ต้องไม่คัดลอกเป็น unknown policy ของ study

| ID/name | TRAIN pixels | VAL pixels | TRAIN images with label | VAL images with label |
|---|---:|---:|---:|---:|
{class_table}

[CSV with fixed all-pixel denominators]({prefix}/CLASS_DISTRIBUTIONS.csv). Pixel support/image occurrenceไม่ใช่ class accuracy หรือ physical ownership reliability Rare classes ต้องรายงาน support พร้อมคะแนนในอนาคต

## Visible/occluded และ overlap semantics

**Verified:** Human_ids เป็น single-valued raster per image; Category/Human/Instance มี gridเดียวกับRGB; paper §2 ระบุ human masks/category definitions ถูกเปลี่ยนจาก CIHP; native person identity อยู่ใน Human IDs ไม่ใช่ part objectsในDatasetNinja

**Unresolved:** ไม่มี authoritative per-class amodal completion/hidden-pixel rules หรือวิธี annotate visible background personsทุกคนครบ Human IDsสองค่าทับพิกเซลเดียวกันไม่ได้ใน rasterนี้ จึงไม่ใช้ bbox intersection เป็น occlusion count หรือพิสูจน์ไม่มีคนซ้อน physical alignment/completeness ต้องตรวจภาพและ adjudicate ห้ามอ้าง CCTV/occlusion robustnessจาก dataset statistics

## Quality gate

เตรียม independent stratified TRAIN sample **200ภาพ**, ทุกภาพมี full-resolution RGB/Human/Category/Instance/per-personGT/warningpanels; additional0033810เป็น purposive warning case ไม่รวม prevalence sample [Review package](CCIHP_HUMAN_REVIEW_STAGE0F.md)

ยังไม่มี independent human review/adjudication จึง **NOT ESTIMATED** annotation-error prevalence และไม่ promote primary หลังผ่าน structural testsเพียงอย่างเดียว Decision Stage0F **D — Insufficient evidence for primary readiness; human review required** ส่วน Stage0E DecisionB compatibilityที่ผู้ใช้ยอมรับคงเดิม

## Rights และ references

ใช้ Decision5A student academic scopeเดิม CCIHP annotations CC-BY-NC4 และ evaluation codeMITตาม includedLICENSE/README; originalCIHP image-rightsยังไม่ชัด DatasetNinja conversionlicenseไม่แทนสิทธิ์ต้นฉบับ ไม่แจกจ่ายรูปโดยอ้าง blanketpermission

[Author paper](https://arxiv.org/abs/2201.09594), [DOI](https://doi.org/10.1109/ICIP42928.2021.9506509), [included README](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/archive_documents/README.md). Source snapshots/prior license evidence retained. No source GT changes, model inference, checkpoint download, PPSS activity, attributes or CCTV execution
'''
    publish('reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md',integrity,'Full exhaustive read-only structural evidence; human-quality gate separate')
    populations_table='\n'.join(f"| {p['population']} | {p['image_count']:,} | {p['native_GT_persons']:,} |" for p in pop['populations'])
    duplicate_report=f'''# CCIHP — Split leakage Stage 0F

## Exact evidence

JPEG-byte train–VAL groups: {sum({s for s,i in g['members']}=={'Training','Validation'} for g in dup['byte']['duplicate_groups'])}; corresponding VAL IDs: {len(dup['byte']['train_validation_overlap_validation_ids'])}. This reuses prior39group evidence and cross-checks source-byte hashes while reading RGB

Decoded-RGB train–VAL groups: {sum({s for s,i in g['members']}=={'Training','Validation'} for g in dup['decoded_RGB']['duplicate_groups'])}; VAL IDs: **{len(dup['decoded_RGB']['train_validation_overlap_validation_ids'])}**. Within-VAL decoded groups: **{len(dup['decoded_RGB']['within_validation_groups'])}**, VAL IDs in these groups: **{sum(sum(s=='Validation' for s,i in g['members']) for g in dup['decoded_RGB']['within_validation_groups'])}**. Pixel hashes include width/height plus exactRGBbytes; strictPillow decoding/noEXIF transform is pinned

[Exact groups]({prefix}/EXACT_DUPLICATES.json); [GT source-map byte-identity comparison]({prefix}/DUPLICATE_GT_IDENTITY_DIAGNOSTICS.json). SameRGB≠samepersonlabels; differingPNGhashes alone do not prove different decodedGT or wrong annotation. No claim public checkpoints memorized anysample

## Proposed populations — original preserved

| Population | Images | Native GT persons |
|---|---:|---:|
{populations_table}

[Exact IDs/denominators]({prefix}/VALIDATION_POPULATIONS_DRAFT.json). Primary original-source score and overlap-controlled sensitivity stay separate tables; latter removes only exact decoded TRAIN reuse, not all near reuse, VAL repetitions or unknown pretraining. No source split edits, exclusionsactivated or benchmark scores. Additional withinVAL de-duplication needs separate policy approval

## Near-duplicate risk screen

Prespecified64bit DCT pHash on32×32LANCZOSgrayscale, top8×8median includingDC; Hamming≤4 and aspect-relative difference≤5%. Five disjoint bit-block index finds all candidates within the specified hash radius without quadratic image comparisons. Screening all decoded TRAIN+VAL metadata: **{near['candidate_pairs']:,} non-exact candidate pairs** involvingVAL. Exact decoded matches excluded fromnearcount to avoid duplication

[Candidate evidence]({prefix}/NEAR_DUPLICATE_SCREEN.json). This is a reproducible risk screen, not proof of common scene or leakage; visually similar differentpeople can collide and resized/cropped/changed images may be missed. Candidates need independent inspection before any new sensitivity exclusion. No threshold/taxonomy/model selection used VAL performance
'''
    publish('reports/CCIHP_SPLIT_LEAKAGE_STAGE0F.md',duplicate_report,'Exact decoded and near duplicate risk evidence, separate proposed populations')
    review_report=f'''# CCIHP — Independent TRAIN annotation review

**PENDING_INDEPENDENT_HUMAN_REVIEW**, not dataset-clean certification. Error prevalence **NOT ESTIMATED**

## Sampling design

Frame: {sample['sampling_frame_images']:,} TRAIN images with verified GT/RGB grids. Seed20261012, stratified simple random sampling without replacement. Strata: nativepersoncount(0/1/2–3/4–7/8+), sourcepixels≤250000/>250000, minpersonmaskarea<1%/≥1%, humanoccupancy<25%/≥25%, bboxintersectionproxy/nointersection. All {len(sample['strata'])} populated strata have positive inclusion probability; allocateatleastoneeach then proportional remainder to200. Proximity/occupancy are measured proxies, notverifiedocclusion/camera-causes

Withinstratum inclusionπ_i=n_h/N_h; designweight=N_h/n_h. Selection fromall reviewableTRAIN was made without preferring knownanomalies and without excluding previoussampleIDs. [Frozen sample/strata/π]({prefix}/TRAIN_REVIEW_SAMPLE.json), [structured checklist]({prefix}/HUMAN_REVIEW_CHECKLIST.csv)

## Full-resolution diagnostic package

[Gallery](../outputs/visualizations/{rid}/index.html), [output/sourcehashes and exact fidelity]({prefix}/REVIEW_PACKAGE.json). **200random images +1purposive0033810**, noGT/RGB resampling. EachRGB/Human/Category/Instance/per-personpanelhasoriginalW×H; nativepersonIDs and semanticvalues preserved. Yellowlinesmark boundaries, noterrors; magenta marks unknown/coverageflags. Everypersongets individualfull-frameGTpanel, neighboringGT overlayshidden butRGBunchanged

Image grids/bytefingerprintschecked; allthreeGTplanes roundtrip {sum(x['pixel_exact_all_three_planes'] for x in package['fidelity'])}/{len(package['fidelity'])} exact on package. This proves fidelity, not annotationtruth

## Review checklist and adjudication

For eachimage, reviewerrecords: missingphysicalpersons; duplicatepersonIDs; multiplephysicalpersonssharingID; wrongsemanticcategory; person/partownership; boundaryerror; ambiguous/occludedregion. Use PASS(noissueobserved)/CONFIRMED/SUSPECTED/UNASSESSABLE, severityminor/major/critical/uncertain, personID/class/ROIandreason. Do not convert an automatedflag toCONFIRMED without reviewingRGBandGT. Tinybackgroundpeople may be outside annotationpolicy; markuncertainuntilpolicyknown

Two independenthumanreviewsrecommended; secondreview/adjudicationrequiredforcritical/suspectedownershipandboundaryambiguity. Reviewers should not know future modelrankings. Recordreviewer/date/adjudication; keepimmutableautomatedoutputs and use newreviewversion. Assistant spotchecks ofrendering do not substitute forhuman qualityreviews

**No prevalence estimate yet.** Future estimates must use stratificationweights and image-clustered uncertainty; imageinclusionprobability doesnot mean personsareindependently sampled. Reportimage/persondenominatorsseparately; purposiveunknowncase mustnot be included inrandomsampleestimates
'''
    publish('reports/CCIHP_HUMAN_REVIEW_STAGE0F.md',review_report,'Reproducible human review package; review pending without prevalence fabrication')
    cross_report=f'''# CCIHP / DatasetNinja CIHP — Cross-source ownership review

Reuse Stage0E30pairedimages, 741 DatasetNinja-converted CIHP semantic part objects: 694singlehumanfullsupport,21multi-human,26partlyunassigned. Reexamined actualobjectbitmaps and CCIHPHuman/Categorygrids for **{len(cross['objects'])} flaggedobjects**; [per-object evidence]({prefix}/CROSS_SOURCE_CONFLICT_REVIEW.json)

Verified: CIHPDress6 and CCIHPFaceMask6 are differentconcepts; dress is annotated asupper5/skirt12 inCCIHP. CCIHP addsBag20/Others21 and broadenseyewear/hat/scarfdefinitions. Authorpaper§2 explicitlychangeshumanmasks. All affectedobjects listCC-categorypixel support andhumanowner support, includingzeroownerpixels

These facts support multiple possible causes: definitionchanges, changedboundaries or ownershippolicy, conversionpartgrouping, and possibleannotationerrors. **Cannot attribute everymixed object toonecause without nativeCIHPhumanreference and physicalreview.** A nativepartobject crossing twoCCIHPHumanIDs is a cross-source discrepancy, not proven erroneousCCIHPownership; zero-ownerpixels need RGBboundaryreview, not automaticdiscard

เก็บ DatasetNinja object ID (ไม่ใช่ original CIHP person/part-instance ID) กับ CCIHP Human ID แยกกัน. No majorityassignment, speculative grouping, nativeCIHP reconstructionclaim, or GTrepair. Currentpairedimages do not establish dataset-widefrequency. Some flags are inVAL: usedonlyannotationintegrity/compatibility, nevermodel/taxonomytuning
'''
    publish('reports/CCIHP_CROSS_SOURCE_WARNINGS_STAGE0F.md',cross_report,'47 previous cross-source flags rechecked without majority reassignment')
    protocol='''# CCIHP person-level evaluation — DRAFT, Stage 0F

Status: DRAFT_REQUIRES_EVIDENCE_REVIEW. No inference/evaluation thresholds frozen; not official CIHPbenchmark results

## Targets and cohorts

1. **Native CCIHP known-category track:** preserve0BG,1..21 categories and unknown22. Only compatible prediction semantics can be interpreted under this native target; pretrained CIHP/ MHP outputs do not becomeCCIHPnative by renamingnumericIDs. Full21classcomparativeleaderboard is not valid whencheckpoints cannotexpressFaceMask/Bag/Others anddresssplits
2. **Common body/clothing cohort:** checkpoint-specific representabilityaudit, sameGTprojection/classes/domain for allcohortmembers. Draftconcepts: exposedface/skin/bodyparts, hair, coarsegarmentregions, footwear; eligibleleft/rightdetailsonlywhereexpressible. Face≠head; glove≠hand; shoe≠barefoot; wholeDresscannot becomeupper/lowerusingGTcoordinates. Entiregarmentmerge may be possible butreducesapplicationdetail
3. **Extended subset:** detailedbody/clothing/accessories onlywithin comparable expressibility. Bag/FaceMask/Othersoftenunsupported orheterogeneous, reportnativeGTsupport/semanticcoverage independently. No arbitraryuniversalweightedscore

Mappings remainproposals in existingmatrix; complete numericalGTpixel/personretention must be computed after mappingapproval, beforeVALevaluation. UnsupportedGT mustnot becomeBG or a favorablemodel-specificdenominator. If excludedfromcohortdomain, identicalsharedvoidprojectionandretainedsupport mustbedisclosed for allmodels. Native outputs remainlossless and separate

## Unknown/background policy proposals

Preserveraw Category22 and requestauthorclarification. Proposedknown-domain metricusesexplicitunknownvoidmask sharedacrossmodels, plusunknownregioncounts/unassignedpredictionbehavior diagnostic; this iscustom known-subsetscore, notunqualifiednativeresult. Untilmeaningagreed no complete-nativecategoryscoreclaimed. Neverreuse upstream gt>=num_classes→0 assemanticpolicy

BG0outsideHuman is documentedbackground. Human>0/Category0 meaningunresolved: propose two separatelynamed sensitivitydomains (rawCategorybackground versusunclassifiedinsideHumanvoid), with fixedwhole-cohortdenominators andsupportcounts. No silentGT repair. Changes mustbe decidedonTRAINreview anddocumented beforefinalVALinference

## Person association and ownership

Source identity=(split,imageID,positiveHumanID), sourcegridRGBdimensions. RawHuman support is provisional GTpersongeometry includingassignedaccessorypixels, notpureanatomicalsilhouette. Deterministic one-to-one maxweight mask-IoU assignment, explicitthreshold and tiepolicy selectedfromTRAINprotocoldevelopmentthenfrozen. Matchingbboxonly or anatomy-only wouldbe separate justifiedablation, notsilentMOTS20copypolicy

KeepunmatchedGT/missedpersons, unmatchedpredictions/duplicates andmatchedpersons separately. CCIHPrastercanonlyrepresentoneownerperpixel; do notflattenoverlapsfromnativeparserpredictions irreversibly. Document ambiguoussourceownership as reviewflags withoutautoexclusion. Cropmargins/TRAINthresholds remainpending

Semanticcropmaycontainneighbors: store rawsemanticcrop andownermappedpredictionseparately. Candidateownershippolicy usesonlyfrozenYOLOmask/geometricassociation andexplicitambiguityflag, neverGTlabels atdeployment. A hardpostparsingmask canloseclothing/accessories outsideYOLOsilhouette, so no defaultclaimedcorrect; comparepolicyonTRAIN afterapproval. GToraclegeometryprovidescrop only, not GT-guidedpixelownership

## Metrics and aggregation

For eachfixedcohortdomain andclassk, IoU_k=TP_k/(TP_k+FP_k+FN_k), accumulateconfusionmatrices on the sameGTprojection. GlobalmIoU=mean validunionclasses withsupportcounts; absentclasswithzeroGTandzeropredunion isundefined/omitted, not1. Predicted-onlyclasswithpositiveunion hasIoU0. ReportBGinclusionexplicitly; foregroundmIoUdoesnot silentlyincludeBG

Person-macro mIoU: computeclassIoUs on a fixedoriginal-coordinate per-personcomparison domain (includingpredictions outsideassignedGT wherepolicyallows), averageclasseswithpositiveunion, thenaveragepersons. ThisdiffersfromglobalconfusionmIoU andmustbenamedseparately. Classabsence/noGTsupport cases undefinedandreported. Dice_k=2TP/(2TP+FP+FN), sameaggregation/supportpolicy. Body/clothing/accessorygroupmeanonlyoverpredeclaredexpressibleclasses, notarbitrarymodel-specificmeans

Matched-person quality Q_matched isconditional, accompaniedbyGTcoverage=matchedGT/allGT andpredictionprecision=matchedpred/allpred. Coverage-awarepersonmacro Q_allGT=mean over allGTpersonslots ofmatchedquality orzeroformissedGT; labelthiscustommetric. Unmatchedpredictions stillneedseparate FP/personprecision andfalsepositivesemanticareareport, becauseQ_allGTalone doesnotpenalizeallspuriousinstances. Do nothide detector missesor claimconditionalquality is end-to-endquality

Person-sizeanalysis uses fixedTRAIN-derived bins ofGTmaskarea/bboxheight andrecordsGTcounts/matchedcounts, nobinselectionbyVALscores. Boundarymetric requires agreed categoricalmapback/native-resolutionpolicy andTRAIN-fixedtolerance; no bilinearGT interpolation

CCIHPnativecharacterized-region AP evaluator isnot automaticallythe personparsing AP^p/PCP evaluator andattributecharacterizationisoutofscope. MHPcompatibilitywrapper tests remainMHP-reference tests, not proof ofCCIHP/CIHPofficialparity. No officialscoreclaimswithoutmatchingnativeprotocol

## Operational tracks and resources

OracleTRAIN/VALGTgeometry → compatiblecropsemanticparser separatesupstreamlocalization. FrozenYOLO26x → crop → parser → source-coordinate ownership isapplicationtrack. Nativefull-frameM2FP/CPI/D2FP retainsinternaldetection andinstancebehavior asreference. Optionalfull-frameparser+YOLOassociation is a separatecompleteconfiguration, not crop-parser-equivalence or hybridfusion

Futuretimingseparate ms/person, native ms/image, end-to-end ms/framewithpersoncount. FixedsourceRGB/nativepreprocess, FP32, warmups/CUDAsync/cleanrounds, crop/preprocess/forward/postprocess/association/mapback separately; residentpipeline allocated/reservedVRAM andNpersons recorded. Do notinferFPSfromparserforward oromit internaldetection. No timingdoneinStage0F

## Leakage and governance

OfficialCCIHPVAL5000 retained; proposedexactTRAIN-overlap-controlledview is sensitivityonly andhasindependentdenominators. Do not merge populationscores. VALintegrityscreen is allowed; no modelthreshold/taxonomy/hyperparameter tuning onVAL. NativeCIHP/MHPcheckpoints mayhave training/selectionexposuretocorrespondingimages; declareYES/NO/UNKNOWN withoutassumingmemorization. This isoff-the-shelfconfigurationcomparison, not controlledarchitecturecausality

Prebenchmarkgate: independenthumanreviews/adjudication, unknownlabelandHumanBGpolicy, originalimagepermissions, checkpointlicenses/readiness, representability/retainedsupport, evaluatorfixturevalidation forapprovedCCIHPdomains andownership, frozenTRAINprotocol. No fullbenchmark untiluserapproval
'''
    publish('reports/CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md',protocol,'CCIHP-specific draft, no threshold/taxonomy freeze')
    decision=f'''# CCIHP vs MHP-v2 — Primary dataset decision Stage 0F

**Selected D — Insufficient evidence; human review still required.** This isprimary-readinessdecision, not a reversal ofacceptedStage0E **B PARTIALLY_COMPATIBLE**. CCIHPusablecustompersonGT isreal; itsidentitytooriginalCIHP remainsunverified

| Criterion | CCIHP current evidence | MHP-v2 existing evidence | Implication |
|---|---|---|---|
| Input integrity | {len(rows):,} RGB/GTsets, {len(full['errors'])} decode/dimensionerrors; fullstreamingGTaudit | 4sourceJPEGsunreadable; approvedreadableviews | Integrityalonecannotchooseprimary |
| Person ownership | TRAIN{agg['Training']['persons']:,}/VAL{agg['Validation']['persons']:,} nativeIDs; 200randomTRAIN reviewpending | perpersonplanes54316; knownownershipflags;30randomTRAIN reviewpending | Neitherhasindependentlyverifiedphysical-qualityprevalence |
| Taxonomy | README21foreground + unknown22({totals['unknown_category_pixels']:,} pixels); alteredDress/FaceMask/Bag/Others | 58foregroundfinegrainedbody/clothing/accessorylabels | CCIHPcoarsebody/clothingpotential; classsupportandexpressibilitymustbechecked |
| Leakage | {len(dup['decoded_RGB']['train_validation_overlap_validation_ids'])} VALIDsexactTRAINreuse; nearflags{near['candidate_pairs']:,}; withinVALrepeatseparate | 652VALIDsexactTRAINreuse;106withinVALgroups | Differentrisks/denominators, notproofmemorization; sensitivityseparate |
| Native checkpoints | CIHP-nativeweightsdo notpredictmodifiedCCIHPsemanticsunmodified; customcohortsneeded | M2FP/CPI MHPnativeweights metadata verified, actualsmokes0 | Roster/exposureandtaxonomyfairnessareseparategates |
| Reproducibility | RawZIP/TAR preserved; fullpixel/sourceledger, sampleπ, statisticsandproposedpopulations | Originalhashes/readablepopulations/leakageledger available | Bothcanbereproducible despite qualitylimitations |
| Rights | CCIHPannotationCCBYNCcompatiblewithacademic scope; originalCIHPRGBpermission unresolved | Priorprojectresearchtermsassessment reused | Imagepermissionstillneedsclarification beforepublication/useclaims |
| CCTV application | Potentialexternalpublichumanparsingtarget; noCCTVtested | MOTS/MHPpublicdata do notverifycompanyCCTVrobustness | Fieldtestseparate, notprimaryselectionargument |

## Recommendation

ContinueCCIHPbody/clothingcandidateprimary preparation with **explicit limitations**, but do notpromote/freeze untilreviewandpolicygatespass. Complete200TRAINhumanreviews includingadjudication andwarninginterpretation; MHPsecondaryfine-grainedrole remainsprovisional. Do notcompare rawdatasetmIoUs acrossdifferentclasses orforceone overlycoarse universalranking

Recordunknown22support andhuman/categorygaps insteadofautomaticrepair. Approve anysharedvoid/sensitivitypolicyonlyafterreview. ExactreusecontrolledVALmanifestisproposed, sourcepopulationunchanged. No newdatasetdownload needed to finishthisreview; originalnativeCIHPwould be needed onlyifnativeCIHPpersonGT/equivalence becomesa requiredobjective

[Full audit](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md), [human review](CCIHP_HUMAN_REVIEW_STAGE0F.md), [leakage](CCIHP_SPLIT_LEAKAGE_STAGE0F.md), [draft evaluation](CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md), [MHP risks](MHPV2_QUALITY_RISK_REVIEW.md)
'''
    publish('reports/CCIHP_PRIMARY_DATASET_DECISION_STAGE0F.md',decision,'Evidence-based primary decision D, without reversing Stage0E compatibility B')
    # Active navigation includes current status first; historical body is retained byte-for-byte in archive.
    for rel in ['reports/CIHP_QUALITY_AUDIT.md','reports/PRIMARY_DATASET_DECISION.md','reports/STAGE0_NEXT_ACTIONS.md']:
        old=(ROOT/rel).read_text()
        current=f'''# Current Stage 0F — CCIHP Full Quality Audit

UserauthorizedfullCCIHPstructural auditcompleted; **{len(rows):,} images/{full['required_PNGs']:,} PNG**, sourceunchanged. **200TRAINhumanreviews PENDING**, unknown22across{len(unknown):,}images/{totals['unknown_category_pixels']:,}pixels, exactTRAINreuse{len(dup['decoded_RGB']['train_validation_overlap_validation_ids'])}VALIDs. Primarydecision **D: humanreviewrequired**, notprimarypromotion. PriorStage0EcompatibilityBaccepted

[Full evidence](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md), [review package](CCIHP_HUMAN_REVIEW_STAGE0F.md), [primary decision](CCIHP_PRIMARY_DATASET_DECISION_STAGE0F.md), [protocol](CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md), [split leakage](CCIHP_SPLIT_LEAKAGE_STAGE0F.md)

**Next:** completeindependenthumanreview/adjudication, clarifylabel22andHumanBGmeaning/CIHPRGBrights, reviewsharedtaxonomy/domainsandpopulationpolicy, thenrequestprotocolfreezeapproval. No newCIHP acquisition, parsercheckpointsmoke, Stage1orCCTVauthorizedbythisaudit

---

## Previous evidence — historical context (authorization statements below are superseded for CCIHP Full Quality Audit only)

'''+old
        publish(rel,current,'Expose completed Stage0F audit and pending human-review gate; historical context retained')
    old=(ROOT/'README.md').read_text()
    publish('README.md',f'''# Human Parsing study — Current Stage 0F

CCIHPautomatedfullqualityaudit **PASS_WITH_WARNINGS**; primaryselectionandhumanannotationreviewpending. AcceptedStage0EcompatibilityBretained; Stage0FprimarydecisionD. No parserbenchmark/inference or primarypromotion

- [Full CCIHP audit](reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md)
- [200TRAIN review package/checklist](reports/CCIHP_HUMAN_REVIEW_STAGE0F.md)
- [Full-resolution local gallery](outputs/visualizations/{rid}/index.html)
- [Split leakage](reports/CCIHP_SPLIT_LEAKAGE_STAGE0F.md)
- [Cross-source flags](reports/CCIHP_CROSS_SOURCE_WARNINGS_STAGE0F.md)
- [CCIHP draft evaluation](reports/CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md)
- [Primary-readiness decision](reports/CCIHP_PRIMARY_DATASET_DECISION_STAGE0F.md)
- [Versioned run evidence]({path}/FULL_STRUCTURAL_AUDIT.json)

## Prior Stage 0 navigation — historical context

'''+old,'Current Stage0F navigation without erasing historical study evidence')
    state=json.loads((ROOT/'STUDY_STATE.json').read_text());state['last_updated_utc']=stamp
    state['dataset_roles_draft']['CCIHP']='CANDIDATE_PRIMARY_BODY_CLOTHING_HUMAN_REVIEW_PENDING'
    state['stage0f_ccihp_quality']={'run_id':rid,'automated_audit_status':full['status'],'status':'WAITING_FOR_HUMAN_REVIEW_AND_USER_APPROVAL',
              'full_quality_audit_authorized':True,'primary_promoted':False,'primary_decision':'D_HUMAN_REVIEW_REQUIRED',
              'train_images':agg['Training']['images'],'validation_images':agg['Validation']['images'],'native_persons':{s:v['persons'] for s,v in agg.items()},
              'unknown_category_pixels':totals['unknown_category_pixels'],'unknown_category_images':len(unknown),
              'review_sample_images':200,'independent_human_review':'PENDING','error_prevalence':'NOT_ESTIMATED',
              'exact_train_overlap_validation_ids':len(dup['decoded_RGB']['train_validation_overlap_validation_ids']),
              'taxonomy_frozen':False,'protocol_frozen':False,'benchmark_started':False,
              'evidence':str((run/'FULL_STRUCTURAL_AUDIT.json').relative_to(ROOT)),
              'report':'reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md','validation':'provenance/CCIHP_STAGE0F_VALIDATION_V1.json'}
    publish('STUDY_STATE.json',json.dumps(state,ensure_ascii=False,indent=2),'Add Stage0F independently; prior/PPSS state preserved')
    write_json(run/'DOCUMENT_REVISIONS.json',revisions)
    write_json(ROOT/'manifests/CCIHP_TRAIN_REVIEW_STAGE0F_V1.json',sample)
    write_json(ROOT/'manifests/CCIHP_VALIDATION_POPULATIONS_STAGE0F_DRAFT_V1.json',pop)
    write_json(ROOT/'provenance/CCIHP_FULL_QUALITY_AUDIT_V1.json',{'run_id':rid,'run_path':path,'full_audit':str((run/'FULL_STRUCTURAL_AUDIT.json').relative_to(ROOT)),
               'sample':str((run/'TRAIN_REVIEW_SAMPLE.json').relative_to(ROOT)),'decision':'D','physical_review':'PENDING','warnings':warning_summary['unknown_category'],
               'input_sha256':full['prior_archive_sha256'],'source_modification':False,'model_inference':False,'primary_promoted':False})
    print('[STAGE0F] reports and draft manifests written',flush=True)

if __name__=='__main__':main()
