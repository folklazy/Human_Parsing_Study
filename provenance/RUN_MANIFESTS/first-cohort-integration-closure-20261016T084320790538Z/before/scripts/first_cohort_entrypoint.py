"""Explicit config: dry-run or bounded saved TRAIN replay; no model inference."""
from pathlib import Path
import argparse
import json
import sys

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config, digest
from src.application_v2.plan import first_cohort_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true')
    action.add_argument('--saved-train-replay', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.saved_train_replay:
        if args.output is None:
            parser.error('--saved-train-replay requires a fresh --output directory')
        from src.application_v2.first_cohort_replay import replay_saved_train
        result = replay_saved_train(args.config, args.output)
        print(json.dumps(dict(status=result['status'], saved_TRAIN_cases=len(result['frames']),
                              new_inference=False, semantic_scores_computed=False, full_benchmark=False)))
        return
    config = load_config(args.config)
    value = first_cohort_plan(config, args.config.resolve().parents[1])
    value.update(config_path=str(args.config.resolve().relative_to(S)), config_content_sha256=digest(config),
                 heavyweight_frameworks_imported=[name for name in ['torch', 'ultralytics', 'mmcv', 'mmdet'] if name in sys.modules])
    text = json.dumps(value, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            stream.write(text)
        print(json.dumps(dict(status=value['status'], models=[p['system_id'] for p in value['parser_systems']],
                              model_loading=False, full_benchmark=False)))
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
