"""Apply the two reviewed owner fixes to derived copies, never source assets.

This does not invent Neck masks or certify the remaining annotation owners.
Full four-target scoring remains gated on a reviewed Face/Neck binding.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse
import copy
import json
import sys
import cv2
import numpy as np
from PIL import Image
from controlled_roi_core import atomic, read, sha

P=Path(__file__).resolve().parents[1];W=P.parent
LABELS={'hair':2,'face':13,'upper':5,'lower':9}


def raster(annotation):
    shape=(annotation['imageHeight'],annotation['imageWidth'])
    category=np.zeros(shape,np.uint8);human=np.zeros(shape,np.uint8)
    for part in annotation['shapes']:
        owner,target=part['label'].split('_')
        points=np.asarray(part['points']).astype(np.int32)
        cv2.fillPoly(category,[points],LABELS[target]);cv2.fillPoly(human,[points],int(owner[1:]))
    return category,human


def prepare(run):
    root=P/'outputs'/run;root.mkdir(parents=True,exist_ok=False)
    parent_path=P/'outputs/cctv-partial-20261031T1800Z/CONFIG.json';parent=read(parent_path)
    proposal_path=P/'outputs/sapiens-saved-measurement-review-20261101/GT_OWNER_ISSUES_PRIVATE.json';proposal=read(proposal_path)
    issues={r['image_id']:r for r in proposal['confirmed_issues']}
    dataset=W/parent['dataset_root'];bindings=[];corrections=[];counts=Counter()
    for member in parent['members']:
        iid=member['id'];catpath=dataset/'Category_ids'/(member['stem']+'.png');humanpath=dataset/'Human_ids'/(member['stem']+'.png')
        if sha(catpath)!=member['GT_sha256']['Category_ids'] or sha(humanpath)!=member['GT_sha256']['Human_ids']:
            raise ValueError('Source GT changed')
        category,human=np.asarray(Image.open(catpath)),np.asarray(Image.open(humanpath))
        if iid in issues:
            issue=issues[iid];path=dataset/'Annotations_canonical'/(member['stem']+'.json')
            if sha(path)!=issue['source_annotation_sha256']:raise ValueError('Reviewed source annotation drift')
            annotation=read(path);beforecat,beforehuman=raster(annotation)
            if not np.array_equal(category,beforecat) or not np.array_equal(human,beforehuman):
                raise ValueError('Source rasterization not reproduced; do not change GT boundaries')
            corrected=copy.deepcopy(annotation);shape=corrected['shapes'][issue['shape_index']]
            if shape['label']!=issue['source_label']:raise ValueError('Reviewed source polygon changed')
            shape['label']=issue['proposed_label'];aftercat,afterhuman=raster(corrected)
            if not np.array_equal(aftercat,category):raise ValueError('Owner correction changed semantic contours')
            annotation_path=root/'Annotations_derived'/(iid+'.json');atomic(annotation_path,corrected)
            newpath=root/'Human_ids'/(iid+'.png');newpath.parent.mkdir(exist_ok=True);Image.fromarray(afterhuman).save(newpath)
            corrections.append(dict(**issue,proposal_applied_to_derived=True,derived_annotation_sha256=sha(annotation_path),
                changed_owner_pixels=int((afterhuman!=human).sum()),semantic_pixels_changed=0))
            humanpath=newpath;human=afterhuman
        for person in np.unique(human):
            if person:
                for name,code in LABELS.items():
                    if ((human==person)&(category==code)).any():counts[name]+=1
        bindings.append(dict(image_id=iid,Category_ids=str(catpath.relative_to(W)),Category_sha256=sha(catpath),
            Human_ids=str(humanpath.relative_to(W)),Human_sha256=sha(humanpath),Neck=None,
            Neck_status='NOT_ANNOTATED_DO_NOT_ASSUME_BACKGROUND',remaining_owner_QA='NOT_CERTIFIED'))
    atomic(root/'GT_REVISION.json',dict(status='TWO_OWNER_CORRECTIONS_APPLIED_NECK_QA_PENDING',created_utc=datetime.now(timezone.utc).isoformat(),
        source_config_sha256=sha(parent_path),correction_proposal_sha256=sha(proposal_path),corrections=corrections,
        source_annotations_modified=False,source_masks_modified=False,semantic_contours_changed=False,
        native_grouped_part_counts_after_owner_correction=dict(counts),eligible_primary_counts=None,
        expert_certified=False,bindings=bindings,scoring_ready=False,primary=None))
    atomic(P/'reports/CONTROLLED_GT_REVISION.json',dict(status='TWO_OWNER_CORRECTIONS_APPLIED_NECK_QA_PENDING',
        derived_revision=run,confirmed_owner_corrections=len(corrections),
        changed_owner_pixels=sum(r['changed_owner_pixels'] for r in corrections),semantic_pixels_changed=0,
        native_grouped_part_counts_after_owner_correction=dict(counts),eligible_primary_counts=None,
        source_annotations_modified=False,source_masks_modified=False,Neck_annotations_available=False,
        scoring_ready=False,expert_certified=False,private_revision_sha256=sha(root/'GT_REVISION.json')))
    print(json.dumps(dict(derived_revision=run,owner_corrections=len(corrections),parts_after=dict(counts),scoring_ready=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True);args=parser.parse_args();prepare(args.run)
