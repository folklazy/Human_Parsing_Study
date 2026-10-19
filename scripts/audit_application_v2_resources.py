"""Index existing pilot resource evidence; no inference or timing evaluation."""
from pathlib import Path
import csv
import json
import sys

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.artifacts import file_hash
from src.application_v2.policy import load_config


def main():
    config = load_config(STUDY / 'configs/application_v2.yaml')
    registry = (STUDY / config['systems']['registry']).resolve(); pilot = registry.parents[1]
    rows = []
    for model in csv.DictReader(registry.open()):
        source = pilot / model['run_manifest']
        if not source.is_file(): raise ValueError('Pilot resource source unavailable')
        record = json.loads(source.read_text()); cases = record.get('cases', [])
        values = [c['peak_allocated_vram_mib'] for c in cases if c.get('peak_allocated_vram_mib') is not None]
        reserved = [c['peak_reserved_vram_mib'] for c in cases if c.get('peak_reserved_vram_mib') is not None]
        rows.append({'model_id': model['model_id'], 'pilot_status': model['status'],
                     'track': model['source_track'], 'run_manifest_workspace_relative': str(source.relative_to(STUDY.parent)),
                     'run_manifest_sha256': file_hash(source), 'precision': record.get('precision'),
                     'GPU': record.get('gpu'), 'recorded_cases': len(cases), 'resource_supported_cases': len(values),
                     'observed_max_allocated_MiB': max(values) if values else None,
                     'observed_max_reserved_MiB': max(reserved) if reserved else None,
                     'resource_adaptation': record.get('resource_adaptation', model['reason']),
                     'new_application_runner_profile_validated': False,
                     'joint_YOLO_parser_residency_validated': False,
                     'license_clearance_inferred_from_execution': False})
    if len(rows) != config['systems']['variants']: raise ValueError('Unexpected pilot registry size')
    result = {'status': 'EXISTING_PILOT_RESOURCE_REFERENCES_ONLY', 'registry_sha256': file_hash(registry),
              'new_inference': False, 'new_timing_or_memory_benchmark': False, 'variants': rows,
              'limitations': ['Smoke workload differs by native operating mode and image/person count',
                              'Recorded allocator peaks are not deployment memory or final performance rankings',
                              'Native residency and new application integration require separate freeze evidence',
                              'Technical execution does not establish intended-use license permission']}
    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    target = STUDY / active['run_path'] / 'EXISTING_PILOT_RESOURCE_REFERENCES.json'
    with target.open('x') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps({'variants': len(rows), 'resource_reference': str(target.relative_to(STUDY)), 'new_inference': False}))


if __name__ == '__main__': main()
