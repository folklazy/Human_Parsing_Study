"""Model-independent, read-only CCIHP structural diagnostics (not quality scores)."""
from collections import defaultdict
import numpy as np
from scipy.ndimage import find_objects


def audit_planes(category, human, instance):
    arrays = (category, human, instance)
    if any(a.ndim != 2 or a.dtype.kind not in 'ui' for a in arrays):
        raise ValueError('Expected integer single-channel categorical planes')
    if len({a.shape for a in arrays}) != 1:
        raise ValueError('Mismatched categorical coordinate grids')
    if category.max(initial=0) > 255 or human.max(initial=0) > 255:
        raise ValueError('Unexpected >8bit category or human encoding')
    cats = np.bincount(category.ravel().astype(np.int64), minlength=256)
    areas = np.bincount(human.ravel().astype(np.int64), minlength=256)
    pids = np.flatnonzero(areas[1:]) + 1
    boxes = find_objects(human)
    persons = []
    h, w = human.shape
    for pid in pids:
        sy, sx = boxes[int(pid)-1]
        bw, bh = sx.stop-sx.start, sy.stop-sy.start
        persons.append({'person_id': int(pid), 'area_pixels': int(areas[pid]),
                        'area_fraction': float(areas[pid]/(w*h)),
                        'bbox_xyxy_half_open': [sx.start, sy.start, sx.stop, sy.stop],
                        'bbox_width': bw, 'bbox_height': bh,
                        'occupancy_ratio': float(areas[pid]/(bw*bh))})
    pos = instance > 0
    inst = instance[pos].astype(np.int64)
    owners = defaultdict(set)
    classes = defaultdict(set)
    for encoded in np.unique(inst*256 + human[pos]):
        owners[int(encoded)//256].add(int(encoded)%256)
    for encoded in np.unique(inst*256 + category[pos]):
        classes[int(encoded)//256].add(int(encoded)%256)
    conflicts = []
    for iid in sorted(owners):
        hs, cs = sorted(owners[iid]), sorted(classes[iid])
        if len(hs) != 1 or hs == [0] or len(cs) != 1 or cs == [0]:
            conflicts.append({'instance_id': iid, 'human_labels': hs, 'category_labels': cs})
    counters = {
        'category_without_human': int(np.count_nonzero((category>0)&(human==0))),
        'human_without_category': int(np.count_nonzero((human>0)&(category==0))),
        'instance_without_human': int(np.count_nonzero(pos&(human==0))),
        'instance_without_category': int(np.count_nonzero(pos&(category==0))),
        'human_category_without_instance': int(np.count_nonzero((human>0)&(category>0)&~pos)),
        'unknown_category_pixels': int(np.count_nonzero(category>21)),
    }
    # Bbox intersection is only a proximity proxy, not proof of mask overlap/occlusion.
    bbox_intersections = 0
    for i, p in enumerate(persons):
        a=p['bbox_xyxy_half_open']
        for q in persons[i+1:]:
            b=q['bbox_xyxy_half_open']
            bbox_intersections += int(min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1]))
    unknown_ids = [int(i) for i in np.flatnonzero(cats[22:])+22]
    return {'person_count':len(persons), 'persons':persons,
            'instance_count':len(owners), 'association_conflicts':conflicts,
            'counts':counters, 'category_pixels':{str(i):int(v) for i,v in enumerate(cats) if v},
            'category_labels':np.flatnonzero(cats).tolist(),
            'human_labels':np.flatnonzero(areas).tolist(),
            'instance_max':int(instance.max(initial=0)),
            'unknown_ids':unknown_ids, 'bbox_intersection_pairs':bbox_intersections,
            'human_occupancy':float(np.count_nonzero(human)/(w*h)),
            'min_person_area_fraction':min((p['area_fraction'] for p in persons),default=0)}


def allocate_strata(sizes, target):
    """Positive inclusion probability in every stratum; fixed size, proportional remainder."""
    if target < len(sizes) or target > sum(sizes.values()):
        raise ValueError('Target cannot cover every stratum or exceeds population')
    allocation={k:1 for k in sorted(sizes)}
    while sum(allocation.values()) < target:
        k=max((k for k in sorted(sizes) if allocation[k]<sizes[k]),
              key=lambda k:sizes[k]/(allocation[k]+1))
        allocation[k]+=1
    return allocation
