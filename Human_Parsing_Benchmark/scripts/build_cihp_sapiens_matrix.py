"""Read pinned taxonomy metadata only. Emit non-executable, post-results proposal."""
from pathlib import Path
from datetime import datetime,timezone
import ast,csv,hashlib,json,re,struct,subprocess,sys
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import LABELS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savecsv(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def assignments(p):
    return {n.targets[0].id:n.value for n in ast.parse(p.read_text()).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}

def build():
    cfg=json.loads((P/'configs/cihp_native_six.json').read_text());base=W/'third_party/human_parsing/sapiens2';rev=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip();src=base/'sapiens/dense/src/datasets/seg/seg_utils.py';a=assignments(src)
    labels={int(i):v['name'] for i,v in ast.literal_eval(a['DOME_CLASSES_29'].args[0])};assert set(labels)==set(range(29))
    doc=base/'docs/SEG.md';doclabels={int(i):n for i,n in re.findall(r'(\d+):\s+([A-Za-z_]+)',doc.read_text())};assert doclabels==labels
    maps={name:ast.literal_eval(a[name]) for name in ['DOME_MAPPING_52_to_29','DOME_MAPPING_34_to_29','INTERNAL_MAPPING_32_to_29']}
    evidence=[]
    def record(p,role,commit=None,url=None):
        evidence.append(dict(path=str(p.relative_to(W)),sha256=sha(p),role=role,source_commit=commit,URL=url))
    record(src,'DOME29 named IDs and source-to-target mappings',rev,f'https://github.com/facebookresearch/sapiens2/blob/{rev}/sapiens/dense/src/datasets/seg/seg_utils.py');record(doc,'Official29-class declaration and checkpoint zoo',rev,f'https://github.com/facebookresearch/sapiens2/blob/{rev}/docs/SEG.md');record(W/'datasets/CIHP/README.md','NativeCIHP named ID order, not an annotation boundary manual')
    for fname in ['seg_shutterstock_dataset.py','seg_dome_dataset.py','seg_internal_dataset.py','seg_base_dataset.py']:
        p=src.parent/fname;record(p,'29-class dataset mapping and dropped-source-ID ->255 behavior',rev)
    bindings=[];headers=[]
    for mid,spec in cfg['models'].items():
        config=W/spec['native_config'];assert sha(config)==spec['native_config_sha256'];head=subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'],text=True).strip();assert head==spec['source_commit'];record(config,'Bound checkpoint native config',head)
        is_sapiens=mid.startswith('Sapiens2_');row=dict(model_id=mid,native_taxonomy='SAPIENS2_DOME29' if is_sapiens else 'CIHP20',semantic_label_count=29 if is_sapiens else 20,background_id=0,source_ignore_value=255,checkpoint=spec['checkpoint'],checkpoint_sha256_from_frozen_registry=spec['checkpoint_sha256'],checkpoint_payload_rehashed_this_work_unit=False,native_config=spec['native_config'],native_config_sha256=sha(config),source_commit=head,channel_name_evidence='',instance_note='')
        if is_sapiens:
            size=mid.split('_',1)[1];hf=W/'models/human_parsing/sapiens2'/size/'config.json';h=json.loads(hf.read_text());assert set(h['id2label'])=={str(i) for i in range(29)} and h['semantic_loss_ignore_index']==255;assert ast.literal_eval(assignments(config)['num_classes'])==29
            record(hf,'Downloaded per-size config:29generic LABEL_n; names supplied by pinned docs/source, not this config',head);row.update(channel_name_evidence='DOC_SEG_MD + DOME_CLASSES_29 + three29class dataset paths; per-sizeHFconfigs have generic LABEL_n, no independent training header',instance_note='Semantic outputs only; no native person-instance ID supplied by these labels')
            with (W/spec['checkpoint']).open('rb') as stream:
                n=struct.unpack('<Q',stream.read(8))[0];assert 0<n<20*1024**2;raw=stream.read(n);header=json.loads(raw)
            tensors=[{'key':k,'shape':v['shape'],'dtype':v['dtype']} for k,v in header.items() if k!='__metadata__' and isinstance(v,dict) and v.get('shape') and v['shape'][0]==29 and 'decode_head.conv_seg' in k];assert len(tensors)==2
            headers.append({'model_id':mid,'checkpoint':spec['checkpoint'],'header_bytes':n,'header_sha256':hashlib.sha256(raw).hexdigest(),'semantic_head_tensors':tensors,'full_weight_hash_repeated':False})
        elif mid.startswith(('M2FP','D2FP')):
            family=spec['family'].lower();catalog=W/spec['source']/family/'data/datasets/register_cihp_parsing.py';cats=ast.literal_eval(assignments(catalog)['CIHP_PARSING_CATEGORIES']);assert [r['id'] for r in cats]==list(range(21));assert cats[20]['name']=='Human'
            for i in range(20):assert cats[i]['name'].replace('Gloves','Glove')==LABELS[i]
            record(catalog,'Explicit nativeCIHP categories0..19;20Human structured branch, not semantic class',head);row.update(channel_name_evidence='EXPLICIT_PINNED_CATEGORY_REGISTRY; Glove/Gloves spelling synonym',instance_note='Registry21categories includesHuman20; exported semantic masks restricted0..19')
        else:
            row.update(channel_name_evidence='ACCEPTED_PROJECT_STANDARD_CIHP_ORDER: pinnedCIHPconfig/numericroute/nativecatalog; no new direct training-header verification',instance_note='QANet final IDs fromYOLO; other native instances retained thenYOLO-associated' if mid.startswith('QANet') else 'Native person entries plus frozenYOLO association; labels are not person IDs')
        bindings.append(row)
    assert len(bindings)==9 and sum(r['semantic_label_count']==29 for r in bindings)==3
    # Relationship is semantic concept evidence, NOT proof of pixel partition equivalence.
    cross_specs=[
        ('0','EXACT','Background concept; foreground annotation/occluder policy may differ'),
        ('1','UNKNOWN','No dedicatedHat output; Apparel containsHairnet in52->29 but does not establish all hats'),
        ('4','EXACT','Hair named concept one-to-one; boundary/occlusion equivalence not independently verified'),
        ('6;15','INCOMPATIBLE','Hand is not a separable Glove category; no dedicatedGlove label'),
        ('2','PARTIAL_OVERLAP','Sunglasses is narrower than Eyeglass, which merges frames/lenses'),
        ('23','PARTIAL_OVERLAP','Upper_Clothing broad category; cannot recoverUpperClothes vsCoat subtype'),
        ('1','UNKNOWN','Apparel is not verifiedDress: source mapping includesHairnet; no losslessupper/lowerDress split'),
        ('23','PARTIAL_OVERLAP','Coat subtype not separately representable byUpper_Clothing'),
        ('10;19','UNION','Left/Right_Sock union matches namedSocks concept; extent convention unverified'),
        ('13','PARTIAL_OVERLAP','Lower_Clothing includes at leastLower_Clothing/Lower_Spandex in34->29; Pants subtype not recoverable'),
        ('22','PARTIAL_OVERLAP','Torso vsTorso-skin exposure/neck/clothing boundary not established'),
        ('1','UNKNOWN','NoScarf output; fullApparel definition not available'),
        ('13','PARTIAL_OVERLAP','Lower_Clothing does not distinguishSkirt fromPants'),
        ('3;24;25;26;27;28','PARTIAL_OVERLAP','Union recovers facial subparts but retainsFace_Neck; neck boundary vsCIHPFace unknown'),
        ('6;7;11','PARTIAL_OVERLAP','Arm subparts/hand candidate union; exactCIHParm wrist/hand partition unverified'),
        ('15;16;20','PARTIAL_OVERLAP','Arm subparts/hand candidate union; exactCIHParm wrist/hand partition unverified'),
        ('5;8;12','PARTIAL_OVERLAP','Leg subparts/bareFoot candidate union; exactCIHPankle/foot partition unverified'),
        ('14;17;21','PARTIAL_OVERLAP','Leg subparts/bareFoot candidate union; exactCIHPankle/foot partition unverified'),
        ('9','EXACT','NamedLeft-shoe concept one-to-one; extent not independently verified'),
        ('18','EXACT','NamedRight-shoe concept one-to-one; extent not independently verified')]
    cross=[dict(CIHP_id=i,CIHP_name=LABELS[i],Sapiens_candidate_ids=ids,Sapiens_candidate_names=';'.join(labels[int(k)] for k in ids.split(';')),relationship=rel,rationale=why,pixel_extent_equivalence='NOT_INDEPENDENTLY_VERIFIED',status='PROPOSAL_NOT_ACCEPTED') for i,(ids,rel,why) in enumerate(cross_specs)]
    target={0:'BACKGROUND',1:'FACE',2:'HAIR',3:'UPPER',4:'LOWER',5:'OTHER'};gt={i:({0:0,13:1,2:2,5:3,7:3,9:4,12:4}.get(i,5)) for i in range(20)};sp={i:({0:0,3:1,24:1,25:1,26:1,27:1,28:1,4:2,23:3,13:4}.get(i,5)) for i in range(29)}
    rows=[]
    for space,names,mapping in [('CIHP_GT_AND_NATIVE_PRED',dict(enumerate(LABELS)),gt),('SAPIENS2_DOME29_PRED',labels,sp)]:
        for i,name in names.items():
            t=mapping[i];relation=cross[i]['relationship'] if space.startswith('CIHP') else ('EXACT' if i in [0,4,9,18] else 'PARTIAL_OVERLAP' if t in [1,3,4] else 'UNKNOWN' if i==1 else 'OUTSIDE_MINIMUM_VIEW')
            rows.append(dict(native_space=space,native_id=i,native_name=name,proposed_target_id=t,proposed_target=target[t],projection_operation='UNION' if (space.startswith('CIHP') and t in [3,4]) or (space.startswith('SAPIENS') and t==1) else 'ONE_TO_ONE' if t<5 else 'CONTEXT_REJECTION',cross_taxonomy_relationship=relation,role='TARGET' if t in [1,2,3,4] else 'BACKGROUND' if t==0 else 'VALID_OTHER_NOT_IGNORE',evidence_scope='Named concepts/source remapping; no pixel-extent equivalence guarantee',status='POST_RESULTS_REVIEWED_PROPOSAL_NOT_EXECUTABLE'))
    savecsv(P/'protocol/CIHP_SAPIENS_MAPPING_PROPOSAL.csv',rows);savecsv(P/'registry/CIHP_SAPIENS_CLASS_COMPATIBILITY.csv',cross);savecsv(P/'registry/CIHP_SAPIENS_CHECKPOINT_LABEL_BINDINGS.csv',bindings)
    important={name:{str(t):[{'source_id':i,'source_name':v['name']} for i,v in mapping.items() if v['target_class_idx']==t] for t in [1,3,13,23]} for name,mapping in maps.items()}
    proposal={'status':'PROPOSAL_NOT_ACCEPTED_NOT_EXECUTABLE','created_utc':datetime.now(timezone.utc).isoformat(),'prepared_after_partial_model_results':True,'rationale':'Class definitions and source mappings, not numerical score optimization','scores_computed':False,'Sapiens_inference_started':False,'native20_benchmark_unchanged':True,'minimum_requested_targets':['FACE','HAIR','UPPER','LOWER'],'target_ids':target,'CIHP_GT_and_native_predictions':gt,'Sapiens29_predictions':sp,'global_valid_domain':'All fixedCIHPGT pixels0..19. Only sourceGT255 VOID for all models; no model/prediction-dependentGTignore. OTHER stays valid negative evidence for targetIoUs.','background':'GT0valid and separate fromOTHER. KnownDress6/Apparel1 goOTHER, neverVOID/invalid execution.','prediction_contract':'Unknown/out-of-range IDs are contractfailure. Known unsupported classes becomeOTHER; wrongtargetprediction onOTHERGT countsFP, OTHERprediction onvalidtargetGT countsFN.','person_domain':'If proposedview retains existing personmetrics: G_loc allnativeHumanIDs; G_sem must be regenerated perimage/person for this new target set, never inherit17520 semanticeligibility automatically. Sharedownerunknownsemanticpolicy remains fixed across models.','hard_label_order':'Compose native planes using frozen confidence/ownership first, then project hard labels; do not removeOTHER before overlap resolution. No probability aggregation available from canonicalhardmasks.','blocking_semantics':['Face_Neck and CIHPFace neck/face boundary is not established; the four-target sharedview is diagnostic/provisional, not a verified common taxonomy.','Upper/lower relation toCoat/Dress/Apparel not exhaustively defined. PreserveDress asOTHER; no heuristic splitting.','A three-targethair/upper/lower supplementaryview would not satisfy/remove the four-target requirement; no new score computed.'],'non_claims':['EXACT meansnamedconceptcorrespondence, not pixelpartitionequivalence','Mapping agreement is projected-task agreement, not officialnativeCIHP accuracy','Apparel is not defined asDress/allclothes/background','No per-modelGTvoid or model-specific targetdomain'],'Sapiens_source_remappings':important,'source_evidence':evidence,'checkpoint_bindings':'registry/CIHP_SAPIENS_CHECKPOINT_LABEL_BINDINGS.csv','class_matrix':'registry/CIHP_SAPIENS_CLASS_COMPATIBILITY.csv','projection_table':'protocol/CIHP_SAPIENS_MAPPING_PROPOSAL.csv','remaining_questions':['ExactCIHPFace neck convention vsDOMEFace_Neck, includingocclusion/eyewear','Which garments fall inDOMEApparel beyondexplicitHairnet andoriginalApparel; relation toDress/Coat','WhetherCIHPArm/Leg includehand/barefoot regions andmatchingDOMEextents','Evidence-backedfixedcommonview/personsemanticeligible counts mustbe reviewed beforeexecution']}
    (P/'protocol/CIHP_SAPIENS_MAPPING_PROPOSAL.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'native_rows':len(rows),'CIHP_class_relationships':len(cross),'checkpoint_bindings':len(bindings),'source_files':len(evidence),'Sapiens_config_names':'generic LABEL_n; actual names verified againstDOME29/docs per checkpointconfig','Apparel_known_members':important['DOME_MAPPING_52_to_29']['1']}))
    (P/'protocol/SAPIENS_SEGMENTATION_HEADER_EVIDENCE.json').write_text(json.dumps(headers,indent=2)+'\n')

if __name__=='__main__':build()
