"""Source-derived, review-only taxonomy cohorts. No prediction evaluation."""
from pathlib import Path
from hashlib import sha256
import ast,csv,json,re
import yaml


def literal_assignment(path,name):
    tree=ast.parse(path.read_text())
    for node in tree.body:
        target=node.target if isinstance(node,ast.AnnAssign) else node.targets[0] if isinstance(node,ast.Assign) else None
        if isinstance(target,ast.Name) and target.id==name:return ast.literal_eval(node.value)
    raise ValueError(f'No literal taxonomy {name}')


def main():
    study=Path(__file__).resolve().parents[1];workspace=study.parent;third=workspace/'third_party/human_parsing'
    parsing=(workspace/'datasets/LV-MHP-v2/README.txt').read_text().split('III.')[0]
    mhp={int(k):v.strip() for k,v in re.findall(r'^\s*(\d+)\s*:\s*([^\r\n]+)',parsing,re.M)}
    fashn=literal_assignment(third/'fashn-human-parser/src/fashn_human_parser/labels.py','IDS_TO_LABELS')
    lip=literal_assignment(third/'SCHP/simple_extractor.py','dataset_settings')['lip']['label']
    lip=dict(enumerate(lip))
    d2fp_lip=dict(enumerate(literal_assignment(third/'D2FP/d2fp/data/datasets/register_lip_semseg.py','LIP_SEMSEG_CATEGORIES')))
    m2fp=literal_assignment(third/'M2FP/m2fp/data/datasets/register_mhpv2_parsing.py','MHPv2_PARSING_CATEGORIES')
    cihp=literal_assignment(third/'D2FP/d2fp/data/datasets/register_cihp_parsing.py','CIHP_PARSING_CATEGORIES')
    native=study/'taxonomy/native';native.mkdir(parents=True,exist_ok=True)
    for name,labels,ref in [('FASHN',fashn,'fashn-human-parser/src/fashn_human_parser/labels.py'),('SCHP_LIP',lip,'SCHP/simple_extractor.py'),
                            ('D2FP_LIP',d2fp_lip,'D2FP/d2fp/data/datasets/register_lip_semseg.py'),
                            ('D2FP_CIHP',{item['id']:item['name'] for item in cihp},'D2FP/d2fp/data/datasets/register_cihp_parsing.py'),
                            ('M2FP_MHPV2',{item['id']:item['name'] for item in m2fp},'M2FP/m2fp/data/datasets/register_mhpv2_parsing.py'),
                            ('CPI_MHPV2',mhp,'CPI-Parser/configs/COSParser/causal_parser_r50_inter_8_135k_mhp.py')]:
        path=native/(name+'.yaml');assert not path.exists()
        path.write_text(yaml.safe_dump({'status':'SOURCE_VERIFIED_CHECKPOINT_VALIDATION_SEPARATE','labels':labels,'source_workspace_relative':'third_party/human_parsing/'+ref,
                         'source_sha256':sha256((third/ref).read_bytes()).hexdigest(),'auxiliary_human_id':59 if name=='M2FP_MHPV2' else 20 if name=='D2FP_CIHP' else None},sort_keys=False))
    # Every native MHP foreground concept is represented in every candidate column.
    lip_map={1:(1,'COARSE_ONLY'),2:(1,'AMBIGUOUS'),3:(13,'EXACT'),4:(2,'EXACT'),5:(14,'EXACT'),6:(15,'EXACT'),
             7:(14,'AMBIGUOUS'),8:(15,'AMBIGUOUS'),11:(5,'COARSE_ONLY'),12:(5,'COARSE_ONLY'),13:(5,'COARSE_ONLY'),14:(5,'COARSE_ONLY'),15:(5,'COARSE_ONLY'),
             17:(9,'EXACT'),18:(9,'COARSE_ONLY'),19:(12,'EXACT'),20:(8,'AMBIGUOUS'),21:(8,'EXACT'),
             22:(18,'COARSE_ONLY'),23:(19,'COARSE_ONLY'),24:(18,'EXACT'),25:(19,'EXACT'),26:(18,'COARSE_ONLY'),27:(19,'COARSE_ONLY'),28:(18,'COARSE_ONLY'),29:(19,'COARSE_ONLY'),
             30:(16,'EXACT'),31:(17,'EXACT'),32:(18,'AMBIGUOUS'),33:(19,'AMBIGUOUS'),34:(7,'EXACT'),35:(6,'EXACT'),36:(6,'AMBIGUOUS'),37:(10,'EXACT'),38:(10,'AMBIGUOUS'),
             39:(1,'COARSE_ONLY'),47:(4,'EXACT'),48:(4,'AMBIGUOUS'),49:(3,'EXACT'),50:(11,'EXACT'),57:(5,'COARSE_ONLY'),58:(9,'AMBIGUOUS')}
    fashn_map={1:(9,'COARSE_ONLY'),2:(9,'AMBIGUOUS'),3:(1,'EXACT'),4:(2,'EXACT'),5:(12,'COARSE_ONLY'),6:(12,'COARSE_ONLY'),7:(13,'COARSE_ONLY'),8:(13,'COARSE_ONLY'),
                10:(3,'AMBIGUOUS'),11:(3,'COARSE_ONLY'),12:(3,'COARSE_ONLY'),13:(3,'COARSE_ONLY'),14:(3,'COARSE_ONLY'),15:(3,'COARSE_ONLY'),16:(16,'AMBIGUOUS'),
                17:(6,'EXACT'),18:(6,'COARSE_ONLY'),19:(5,'EXACT'),20:(14,'AMBIGUOUS'),21:(15,'AMBIGUOUS'),
                **{i:(15,'AMBIGUOUS') for i in range(22,30)},30:(14,'COARSE_ONLY'),31:(14,'COARSE_ONLY'),32:(15,'COARSE_ONLY'),33:(15,'COARSE_ONLY'),
                34:(3,'COARSE_ONLY'),35:(4,'EXACT'),36:(4,'AMBIGUOUS'),37:(4,'AMBIGUOUS'),38:(4,'AMBIGUOUS'),39:(9,'COARSE_ONLY'),40:(8,'COARSE_ONLY'),
                43:(7,'EXACT'),45:(8,'COARSE_ONLY'),46:(8,'AMBIGUOUS'),47:(11,'COARSE_ONLY'),48:(11,'COARSE_ONLY'),49:(13,'AMBIGUOUS'),50:(10,'EXACT'),
                52:(8,'AMBIGUOUS'),53:(17,'AMBIGUOUS'),54:(17,'AMBIGUOUS'),55:(3,'AMBIGUOUS'),56:(17,'AMBIGUOUS'),57:(3,'COARSE_ONLY'),58:(6,'AMBIGUOUS')}
    rows=[]
    for identifier,name in mhp.items():
        for model in ['M2FP_MHPV2','CPI_R50_MHPV2','CPI_CONVNEXT_MHPV2','FASHN','SCHP_LIP','D2FP_LIP','D2FP_CIHP','SAPIENS2_0_4B']:
            target=None;status='UNSUPPORTED';reason='Native source taxonomy lacks this semantic distinction'
            if model.startswith(('M2FP','CPI')):target=identifier;status='EXACT';reason='Source taxonomy is MHP-v2; exact loaded checkpoint compatibility still requires smoke evidence'
            elif model=='FASHN':
                if identifier in fashn_map:target,status=fashn_map[identifier]
                reason='Fine class/side distinctions may require shared projection; feet, torso, jewelry and full-body semantics remain ambiguous'
            elif model.startswith(('SCHP','D2FP')):
                mapping=dict(lip_map)
                if model=='D2FP_CIHP':mapping[16]=(10,'EXACT');mapping.pop(37,None);mapping.pop(38,None)
                if identifier in mapping:target,status=mapping[identifier]
                reason='LIP or CIHP variant must be distinguished; hands, bare feet, whole garments and clothing scope require review'
            else:status='UNKNOWN';reason='LICENSE_BLOCKED_PENDING_CLARIFICATION; outside executable/comparable cohort, no checkpoint/native outputs inspected'
            if identifier==0 and model!='SAPIENS2_0_4B':target=0;status='EXACT';reason='Native background ID source-verified; out-of-target ownership still requires an explicit evaluation domain'
            rows.append({'mhpv2_id':identifier,'mhpv2_concept':name,'model':model,'native_id':target if target is not None else '',
                         'representability':status,'evidence_level':'SOURCE_TAXONOMY_ONLY','mapping_frozen':False,'reason':reason})
    path=study/'taxonomy/TAXONOMY_REPRESENTABILITY_MATRIX.csv';assert not path.exists()
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    core={'schema_version':'1.0','status':'DRAFT_REQUIRES_USER_REVIEW','mapping_frozen':False,'evaluation_authorized':False,
          'purpose':'Candidate common concepts; no universal leaderboard authorized',
          'concepts':{'background':[0],'face':[3],'hair':[4],'arms_coarse':[5,6],'hands_coarse':[7,8],'legs_coarse':[30,31],
                      'upper_clothing_coarse':[11,12,13,14,15,34,57],'lower_clothing_coarse':[17,18,19], 'dress':[35]},
          'universal_concept_subset_provisionally_comparable':['face','hair'],
          'ambiguities':['Footwear is not FASHN feet by definition','Torso skin is not necessarily anatomic torso','LIP hands are not independently labeled','Full-body garments cannot be split by lookup table','Native same-name boundaries still need GT visual review'],
          'policy':{'unsupported_gt_to_background':'FORBIDDEN','valid_domain':'Shared across every member in a cohort, with retained foreground and class support disclosed',
                    'unsupported_predictions':'Explicit UNMAPPED; valid-domain GT support retained; report unmapped burden and background hallucinations separately',
                    'background_in_primary_miou':False,'empty_union':'UNDEFINED, never automatic perfect score','all_model_common_score':'NOT_FROZEN'}}
    extended={'schema_version':'1.0','status':'DRAFT_REQUIRES_USER_REVIEW','mapping_frozen':False,'evaluation_authorized':False,
              'cohorts':{'MHP_NATIVE':{'models':['M2FP_MHPV2','CPI_R50_MHPV2','CPI_CONVNEXT_MHPV2'],'gt_ids':list(range(59)),
                                     'coverage':'All native parsing support; includes associated/carried objects; checkpoints not yet smoke-verified'},
                         'MHP_LIP_STYLE':{'models':['SCHP_LIP','D2FP_LIP','M2FP_MHPV2','CPI_R50_MHPV2'],'mhp_projection_candidate':lip_map,'gate':'Ambiguous mappings require common-domain decision; source relations are not a frozen evaluator'},
                         'MHP_FASHN_COARSE':{'models':['FASHN','M2FP_MHPV2','CPI_R50_MHPV2'],'mhp_projection_candidate':fashn_map,'gate':'Fine native clothes/accessories cannot be scored universally'},
                         'FOOTWEAR_SUBSET':{'models':['M2FP_MHPV2','CPI_R50_MHPV2','SCHP_LIP','D2FP_LIP','D2FP_CIHP'],'FASHN':'EXCLUDED_UNTIL_FEET_SHOES_SCOPE_VERIFIED'}},
              'analysis_groups':{'body':[3,4,5,6,7,8,16,30,31,32,33],'clothing':[10,11,12,13,14,15,17,18,19,20,21,34,35,36,37,38,57,58],
                                 'footwear':list(range(22,30)),'accessories_and_carried':[1,2,9,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56]},
              'group_aggregation':'Mean of supported class IoU within each stated group; class support and common denominator required. Groups are semantic summaries, not predetermined model expert roles.'}
    for name,value in [('COMMON_HP_CORE_DRAFT.yaml',core),('COMMON_HP_EXTENDED_DRAFT.yaml',extended)]:
        path=study/'taxonomy'/name;assert not path.exists();path.write_text(yaml.safe_dump(value,sort_keys=False))
    print(f'[TAXONOMY] {len(rows)} source representability cells; core/extended remain DRAFT')


if __name__=='__main__':main()
