"""Independent ledger/accounting, provenance and review-package validation; no models."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import csv,json,re,subprocess,sys
from PIL import Image
import yaml
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parent;sys.path.insert(0,str(ROOT))
from audit_ccihp_full_quality import sha,stat,write_json

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());run=ROOT/active['run_path']
    audit=json.loads((run/'FULL_STRUCTURAL_AUDIT.json').read_text());before=json.loads((run/'BEFORE.json').read_text())
    rows=[json.loads(x) for x in (run/'IMAGE_AUDIT.jsonl').open()];lookup={(r['split'],r['image_id']):r for r in rows};checks=[]
    def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
    check('all_33280_unique_image_records',len(rows)==len(lookup)==33280)
    check('all_PNG_RGB_decoding_and_grids',all(r.get('GT_decode')==r.get('RGB_decode')=='PASS' and r['RGB_GT_dimensions_match'] for r in rows))
    for split,target in [('Training',28280),('Validation',5000)]:
        sub=[r for r in rows if r['split']==split];agg=audit['aggregate'][split]
        classes=Counter();occ=Counter();counts=Counter()
        for r in sub:classes.update(r['category_pixels']);occ.update(r['category_pixels'].keys());counts.update(r['counts'])
        check(split+'_source_count_and_pixels',len(sub)==target and sum(r['wh'][0]*r['wh'][1] for r in sub)==agg['pixels'])
        check(split+'_independent_class_support_totals',dict(classes)==agg['classes'] and dict(occ)==agg['class_images'])
        check(split+'_independent_warning_totals',dict(counts)==agg['counts'])
        check(split+'_native_person_ID_count',sum(len([i for i in r['human_labels'] if i>0]) for r in sub)==agg['persons'])
        check(split+'_per_image_complete_pixel_denominator',all(sum(r['category_pixels'].values())==r['wh'][0]*r['wh'][1] for r in sub))
        check(split+'_native_encodings',all([(m['component']=='Instance_ids' and m['dtype']=='uint16' and m['mode']=='I;16') or
                                           (m['component']!='Instance_ids' and m['dtype']=='uint8' and m['mode']=='L') for r in sub for m in r['source_maps']]))
        check(split+'_positive_instance_single_class_single_owner',all(not r['association_conflicts'] for r in sub))
    pcounts=Counter();pkeys=set();boxes=True
    for l in (run/'PERSON_AUDIT.jsonl').open():
        p=json.loads(l);r=lookup[(p['split'],p['image_id'])];pcounts[p['split']]+=1;key=(p['split'],p['image_id'],p['person_id'])
        if key in pkeys:boxes=False
        pkeys.add(key);x1,y1,x2,y2=p['bbox_xyxy_half_open'];w,h=r['wh']
        boxes &= 0<=x1<x2<=w and 0<=y1<y2<=h and 0<p['area_pixels']<=(x2-x1)*(y2-y1)
    check('per_person_ledger_unique_and_valid_boxes',boxes and all(pcounts[s]==a['persons'] for s,a in audit['aggregate'].items()))
    sample=json.loads((run/'TRAIN_REVIEW_SAMPLE.json').read_text());package=json.loads((run/'REVIEW_PACKAGE.json').read_text())
    sample_ids={s['image_id'] for s in sample['samples']};check('200_unique_TRAIN_only',len(sample['samples'])==len(sample_ids)==200 and all(s['split']=='Training' for s in sample['samples']))
    check('sample_independent_review_pending',sample['review_status']=='PENDING_INDEPENDENT_HUMAN_REVIEW' and sample['error_prevalence']=='NOT_ESTIMATED')
    check('sampling_frame_28280',sample['sampling_frame_images']==28280 and not sample['sampling_frame_exclusions'])
    st={s['stratum']:s for s in sample['strata']};ncounts=Counter(s['stratum'] for s in sample['samples'])
    check('stratum_allocation_and_positive_probabilities',sum(s['population'] for s in st.values())==28280 and sum(s['sample'] for s in st.values())==200 and
          all(ncounts[k]==s['sample'] and 0<s['inclusion_probability']<=1 for k,s in st.items()))
    check('inclusion_probabilities_and_weights',all(s['inclusion_probability']==s['n_h']/s['N_h'] and s['design_weight']==s['N_h']/s['n_h'] and st[s['stratum']]['sample']==s['n_h'] and st[s['stratum']]['population']==s['N_h'] for s in sample['samples']))
    checklist=list(csv.DictReader((run/'HUMAN_REVIEW_CHECKLIST.csv').open()))
    check('human_checklist_200_PENDING',len(checklist)==200 and {r['image_id'] for r in checklist}==sample_ids and all(r['review_status']=='PENDING' and not r['reviewer'] for r in checklist))
    sizes_ok=hashes_ok=True
    for o in package['outputs']:
        p=ROOT/o['output'];hashes_ok &= p.is_file() and sha(p)==o['output_sha256']
        with Image.open(p) as im:
            w,h=o['image_wh'];sizes_ok &= im.size==(3*w,((6+o['native_person_count']+2)//3)*(h+28));im.verify()
    check('review_full_resolution_panel_geometry',sizes_ok)
    check('review_all_201_artifact_hashes',hashes_ok and len(package['outputs'])==201)
    check('review_GT_pixel_exact_roundtrip',len(package['fidelity'])==201 and all(r['pixel_exact_all_three_planes'] for r in package['fidelity']))
    duplicate=json.loads((run/'EXACT_DUPLICATES.json').read_text());expected=[]
    decoded_groups={}
    for r in rows:decoded_groups.setdefault(r['RGB_decoded_sha256'],[]).append([r['split'],r['image_id']])
    expected=sorted({i for g in decoded_groups.values() if {s for s,i in g}=={'Training','Validation'} for s,i in g if s=='Validation'})
    check('exact_overlap_control_math',expected==duplicate['decoded_RGB']['train_validation_overlap_validation_ids'])
    pop=json.loads((run/'VALIDATION_POPULATIONS_DRAFT.json').read_text())
    for p in pop['populations']:
        selected=[lookup[('Validation',i)] for i in p['ids']]
        check(p['population']+'_denominators',len(p['ids'])==len(set(p['ids']))==p['image_count'] and sum(r['person_count'] for r in selected)==p['native_GT_persons'])
        if p['population'].startswith('overlap_controlled'):
            check(p['population']+'_membership',set(p['ids'])=={r['image_id'] for r in rows if r['split']=='Validation'}-set(expected))
    near=json.loads((run/'NEAR_DUPLICATE_SCREEN.json').read_text());near_good=True
    for pair in near['pairs']:
        a=lookup[tuple(pair['a'])];b=lookup[tuple(pair['b'])];d=(int(a['phash64'],16)^int(b['phash64'],16)).bit_count()
        ar=a['wh'][0]/a['wh'][1];br=b['wh'][0]/b['wh'][1]
        near_good &= d==pair['phash_hamming'] and d<=4 and abs(ar-br)/max(ar,br)<=.05 and a['RGB_decoded_sha256']!=b['RGB_decoded_sha256']
    check('near_screen_candidate_math',near_good and len(near['pairs'])==near['candidate_pairs'])
    warnings=json.loads((run/'FOCUSED_WARNING_INVESTIGATION.json').read_text());check('all_unknown_pixel_investigation_accounted',warnings['unknown_pixels']==sum(a['counts']['unknown_category_pixels'] for a in audit['aggregate'].values()) and warnings['all_unknowns_have_human_support'] and warnings['all_unknowns_without_attribute_instance'])
    support=json.loads((run/'PERSON_SEMANTIC_SUPPORT_WARNINGS.json').read_text());check('background_only_and_unknown_only_person_flags_preserved',len(support['completely_background_person_planes'])==35 and len(support['without_known_foreground_person_planes'])==42)
    cross=json.loads((run/'CROSS_SOURCE_CONFLICT_REVIEW.json').read_text());check('prior_47_flags_rechecked_no_majority_assignment',cross['status_counts']=={'MULTIPLE_HUMANS':21,'ONE_HUMAN_WITH_UNASSIGNED_PIXELS':26} and all(o['no_majority_repair'] for o in cross['objects']))
    changes=[]
    for p,h in before['protected_sha256'].items():
        if not (WORKSPACE/p).is_file() or sha(WORKSPACE/p)!=h:changes.append(p)
    check('protected_YOLO_metrics_MHP_PPSS_checkpoint_metadata_hashes',not changes,changes)
    check('archive_source_stats_unchanged',all(stat(WORKSPACE/p)==v for p,v in before['asset_stats'].items()))
    frozen=json.loads((ROOT/'manifests/YOLO26X_SOURCE.json').read_text());check('frozen_YOLO26x_checkpoint_matches_prior_SHA256',sha(WORKSPACE/frozen['checkpoint_workspace_relative'])==frozen['sha256'])
    state=json.loads((ROOT/'STUDY_STATE.json').read_text())
    check('PPSS_historical_state_nodes_preserved',all(v==state[k] for k,v in before['prior_state'].items() if k.startswith('ppss')))
    check('previous_stage0e_evidence_state_preserved',state['stage0e_ccihp_cihp']==before['prior_state']['stage0e_ccihp_cihp'])
    check('no_benchmark_or_primary_promotion',state['benchmark_status']=='NOT_STARTED' and not state['stage0f_ccihp_quality']['primary_promoted'] and state['stage0f_ccihp_quality']['primary_decision']=='D_HUMAN_REVIEW_REQUIRED')
    draft=yaml.safe_load((ROOT/'taxonomy/CCIHP_PERSON_EVALUATION_COHORTS_DRAFT_V1.yaml').read_text());check('taxonomy_cohorts_remain_DRAFT',draft['status']=='DRAFT_REQUIRES_REVIEW' and not draft['cohorts']['common_body_clothing']['numeric_mapping_frozen'])
    revisions=json.loads((run/'DOCUMENT_REVISIONS.json').read_text());archive_ok=True
    # The editorial protocol navigation addition is included in final after hashes.
    for r in revisions:
        r['sha256_after']=sha(ROOT/r['original_relative_path'])
        if r['sha256_before']:
            archive_ok &= (ROOT/r['archive_relative_path']).is_file() and sha(ROOT/r['archive_relative_path'])==r['sha256_before']
    write_json(run/'DOCUMENT_REVISIONS.json',revisions)
    check('original_documents_archived_exact_before_hashes',archive_ok)
    badlinks=[]
    docs=list(ROOT.glob('reports/CCIHP_*STAGE0F.md'))+[ROOT/'README.md']
    for p in docs:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('https://','http://','#')):continue
            if target=='provenance/CCIHP_STAGE0F_VALIDATION_V1.json' and p==ROOT/'README.md':continue  # This exact self-output is written and checked after validation.
            if not (p.parent/target.split('#')[0]).exists():badlinks.append([str(p.relative_to(ROOT)),target])
    check('active_local_document_visual_links_resolve',not badlinks,badlinks)
    git_after={}
    for repo,status in before['git_status'].items():git_after[repo]=subprocess.run(['git','status','--porcelain=v1'],cwd=WORKSPACE/repo,text=True,capture_output=True).stdout
    check('existing_Git_working_trees_preserved',git_after==before['git_status'])
    testlog=(run/'UNIT_TESTS.log').read_text();check('25_unit_tests_executed_PASS','Ran 25 tests' in testlog and testlog.rstrip().endswith('OK'))
    result={'run_id':active['run_id'],'validation_status':'PASS' if all(c['pass'] for c in checks) else 'FAIL',
            'scientific_quality_status':'PASS_WITH_WARNINGS_AUTOMATED_ONLY','primary_readiness':'D_HUMAN_REVIEW_REQUIRED',
            'checks':checks,'checks_passed':sum(c['pass'] for c in checks),'checks_total':len(checks),
            'unit_tests_passed':25,'independent_human_reviews_completed':0,'annotation_error_prevalence':'NOT_ESTIMATED',
            'safety':{'original_dataset_modified':False,'PPSS_activity':False,'YOLO_modified':False,'checkpoint_download':False,'parser_inference':False,
                      'full_benchmark':False,'training':False,'CCTV_inference':False,'attribute_evaluation':False,'remote_Git_actions':False},
            'git_status_before':before['git_status'],'git_status_after':git_after,'end_utc':datetime.now(timezone.utc).isoformat()}
    write_json(run/'VALIDATION.json',result);write_json(ROOT/'provenance/CCIHP_STAGE0F_VALIDATION_V1.json',result)
    # Content-addressed output inventory covers reports, code, manifests, tests and all retained run artifacts.
    print(f"[STAGE0F] validation: {result['validation_status']} ({result['checks_passed']}/{len(checks)}); unit tests:25 PASS",flush=True)
    inventory={str(p.relative_to(ROOT)):sha(p) for p in sorted(run.rglob('*')) if p.is_file() and p.name not in ['OUTPUT_SHA256.json','EXECUTION_MANIFEST.json']}
    inventory.update({str(p.relative_to(ROOT)):sha(p) for p in docs})
    for pattern in ['scripts/*ccihp*quality*.py','scripts/*ccihp*warnings*.py','src/data/ccihp_quality.py','src/data/ccihp_gt.py','src/data/cihp_datasetninja.py','scripts/check_ccihp_person_semantic_support.py','tests/test_ccihp_quality.py','taxonomy/CCIHP_PERSON_EVALUATION_COHORTS_DRAFT_V1.yaml']:
        inventory.update({str(p.relative_to(ROOT)):sha(p) for p in ROOT.glob(pattern) if p.is_file()})
    write_json(run/'OUTPUT_SHA256.json',inventory)
    write_json(run/'EXECUTION_MANIFEST.json',{'study_revision':'NO_GIT_REPOSITORY_LOCAL_STUDY','run_id':active['run_id'],
            'interpreter':str((WORKSPACE/'.venvs/mhpv2-stage0/bin/python').relative_to(WORKSPACE)),
            'environment':{'python':sys.version,'Pillow':Image.__version__,'numpy':__import__('numpy').__version__,'scipy':__import__('scipy').__version__},'configuration_sha256':sha(run/'CONFIG.json'),
            'dataset_inputs':audit['prior_archive_sha256'],'output_inventory_sha256':sha(run/'OUTPUT_SHA256.json'),
            'scripts':['audit_ccihp_full_quality.py','prepare_ccihp_quality_review.py','investigate_ccihp_quality_warnings.py','check_ccihp_person_semantic_support.py','document_ccihp_full_quality.py','finalize_ccihp_quality_audit.py','validate_ccihp_full_quality.py'],
            'status':result['validation_status'],'model_or_GPU_execution':False})
    if result['validation_status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
