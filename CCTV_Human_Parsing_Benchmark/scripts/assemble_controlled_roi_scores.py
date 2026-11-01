"""Assemble accepted CPU diagnostic results without opening predictions again.

An explicitly accepted predecessor scorer may supply already completed systems.
Choose the first COMPLETE result in supplied attempt order, never by score.
Check frame identities, record hashes, scalar arithmetic and fixed GT bindings.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import json
import numpy as np
from controlled_roi_core import atomic, read, sha
from controlled_roi_evaluation import P, W, TARGETS, summarize


def assemble(evaluations, binding_path, predecessor_scorer_sha256, out):
    binding = read(binding_path)
    expected = [r['image_id'] for r in binding['frames']]
    sources, attempts = [], []
    current_sha = sha(P/'scripts/controlled_roi_evaluation.py')
    for location in evaluations:
        path = Path(location); frozen = read(path/'FROZEN_INPUTS.json')
        if frozen['GT_binding_sha256'] != sha(binding_path) or frozen['protocol_sha256'] != binding['protocol_sha256']:
            raise ValueError('Cannot mix different GT/protocol evaluations')
        if frozen['scorer_sha256'] not in {current_sha, predecessor_scorer_sha256}:
            raise ValueError('Unreviewed scorer compatibility')
        if sources and any(frozen[k] != sources[0][1][k] for k in ['source_index_sha256', 'helper_hashes']):
            raise ValueError('Different source cohort or scientific helper revisions')
        result = read(path/'RESULTS.json')
        if result['frozen_inputs'] != frozen:
            raise ValueError('Result/frozen-input identity differs')
        sources.append((path, frozen, result))
        attempts.append(dict(path=str(path.resolve().relative_to(W)), result_sha256=sha(path/'RESULTS.json'),
            source_sha256=frozen['scorer_sha256'], source_status=result['status'],
            completed_models=[mid for mid, m in result['models'].items() if m['completion']['strict_complete']]))
    index = read(W/sources[0][1]['source_index'])
    models, tables = {}, []
    for mid in index['models']:
        candidates = [(path, frozen, result['models'][mid]) for path, frozen, result in sources
                      if mid in result['models'] and result['models'][mid]['completion']['strict_complete']]
        if not candidates:
            raise ValueError('No complete diagnostic evaluation for '+mid)
        path, frozen, metrics = candidates[0]
        if read(path/mid/'METRICS.json') != metrics:
            raise ValueError('Model metrics differ from aggregate result')
        ledger = [json.loads(line) for line in (path/mid/'FRAMES.jsonl').read_text().splitlines()]
        if sorted(r['image_id'] for r in ledger) != sorted(expected) or len(ledger) != len(expected):
            raise ValueError('Frame ledger membership is not exact')
        all_rows = []
        for record in ledger:
            record_path = path/mid/(record['image_id']+'.json')
            if sha(record_path) != record['record_sha256']:
                raise ValueError('Scored record hash changed')
            frame = read(record_path)
            if frame['frozen_inputs_sha256'] != sha(path/'FROZEN_INPUTS.json'):
                raise ValueError('Frame scored against different bindings')
            all_rows.extend(frame['rows'])
        recomputed = summarize(all_rows, binding['expected_eligible_parts'], True, False)
        if recomputed['targets'] != metrics['targets'] or metrics['primary'] is not None:
            raise ValueError('Stored target aggregate arithmetic mismatch')
        keys = [(r['image_id'], r['person_id'], r['target']) for r in all_rows]
        expected_keys = [(r['image_id'], r['person_id'], r['target']) for r in binding['part_records'] if r['target'] != 'FaceDomain']
        if sorted(keys) != sorted(expected_keys):
            raise ValueError('Missing/duplicate/extra annotated part rows')
        models[mid] = dict(**metrics, accepted_metrics_path=str((path/mid/'METRICS.json').resolve().relative_to(W)),
            accepted_metrics_sha256=sha(path/mid/'METRICS.json'), evaluation_source_sha256=frozen['scorer_sha256'])
        with (path/'TARGET_METRICS.csv').open() as stream:
            tables.extend(r for r in csv.DictReader(stream) if r['model_id'] == mid)
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    report = dict(status='NON_FACE_DIAGNOSTICS_COMPLETE_9_OF_9_FACE_GT_PENDING',
        updated_utc=datetime.now(timezone.utc).isoformat(), model_calls=0, inference_complete_models=len(models),
        diagnostic_complete_models=len(models), final_four_target_evaluation_complete=False,
        primary=None, overall_winner=None, models=models, source_attempts=attempts,
        assembly_source_sha256=sha(__file__), GT_binding_sha256=sha(binding_path),
        protocol_sha256=binding['protocol_sha256'], source_index_sha256=sources[0][1]['source_index_sha256'],
        GT_summary=read(Path(binding_path).parent/'PUBLIC_GT_REVIEW.json'),
        scorer_correction='Continuation configs contain a model-ID list. Resolve checkpoint identities from their hash-bound parent. Previous complete six model calculations reused; only three failed-to-score systems recalculated. Projection/counts/aggregation unchanged.',
        result_scope='selected annotated non-Face parts; no full-scene IoU, final macro4, or deployment winner')
    atomic(out/'RESULT_INDEX.json', report)
    with (out/'TARGET_METRICS.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(tables[0])); writer.writeheader(); writer.writerows(tables)
    print(json.dumps(dict(status=report['status'], models=len(models), model_calls=0, primary=None)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluations', type=Path, nargs='+', required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--accepted-predecessor-scorer-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assemble(args.evaluations, args.binding, args.accepted_predecessor_scorer_sha256, args.out)
