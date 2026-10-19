"""Dependency-injected person/frame lifecycle, with no model import or download."""
from time import perf_counter
from .contracts import stage_rate


class ContractFailure(RuntimeError):
    pass


class ModelSystemFailure(RuntimeError):
    pass


class ExternalInfrastructureFailure(RuntimeError):
    pass


class UnresolvedFailure(RuntimeError):
    pass


def _invoke(function, argument, event_id):
    start = perf_counter()
    try:
        output = function(argument)
        return output, None, perf_counter() - start
    except ContractFailure as exc:
        return None, {'event_id': event_id, 'status': 'CONTRACT_FAILURE',
                      'exception': str(exc)}, perf_counter() - start
    except (ExternalInfrastructureFailure, UnresolvedFailure) as exc:
        return None, {'event_id': event_id, 'status': 'INVALID_ENV' if isinstance(exc, ExternalInfrastructureFailure)
                      else 'UNRESOLVED_EVENT', 'exception': str(exc)}, perf_counter() - start
    except Exception as exc:
        return None, {'event_id': event_id, 'status': 'MODEL_SYSTEM_FAILURE',
                      'exception_type': type(exc).__name__, 'exception': str(exc)}, perf_counter() - start


def _checked(function, argument, validator):
    result = function(argument)
    if result is not None:
        try:
            if validator(result) is False:
                raise ValueError('Output contract rejected')
        except Exception as exc:
            raise ContractFailure(str(exc)) from exc
    return result


def run_person_jobs(frame_id, opportunities, worker, *, failure_scope, validate_output, finalizer=None):
    if failure_scope not in {'PERSON', 'FRAME'}:
        raise ValueError('Declared failure scope required')
    ids = [o['id'] for o in opportunities]
    if len(ids) != len(set(ids)):
        raise ValueError('Opportunity IDs must be immutable and unique')
    events, outputs, failures = [], [], []
    invalid = False
    global_seconds = 0.0
    for index, opportunity in enumerate(opportunities):
        if invalid:
            events.append({'unit_id': opportunity['id'], 'eligible': True, 'status': 'NOT_ATTEMPTED'})
            continue
        result, failure, seconds = _invoke(lambda op: _checked(worker, op, validate_output),
                                          opportunity, f'{frame_id}:person:{opportunity["id"]}')
        events.append({'unit_id': opportunity['id'], 'eligible': True,
                       'status': 'FAILED' if failure else 'COMPLETED', 'seconds': seconds})
        if failure:
            failures.append({**failure, 'affected_unit_ids': [opportunity['id']]})
            if failure['status'] != 'MODEL_SYSTEM_FAILURE':
                invalid = True
            if failure_scope == 'FRAME':
                outputs = []
                for remaining in opportunities[index + 1:]:
                    events.append({'unit_id': remaining['id'], 'eligible': True, 'status': 'NOT_ATTEMPTED'})
                break
        elif result is not None:
            outputs.append(result)
    if not invalid and finalizer is not None and outputs:
        def checked_finalizer(provisional):
            final = finalizer(provisional)
            if not isinstance(final, list):
                raise ContractFailure('Finalizer must return a list of validated person outputs')
            for person in final:
                try:
                    if validate_output(person) is False:
                        raise ValueError('Finalizer output contract rejected')
                except Exception as exc:
                    raise ContractFailure(str(exc)) from exc
            return final
        final, failure, seconds = _invoke(checked_finalizer, outputs, f'{frame_id}:global_finalizer')
        global_seconds = seconds
        if failure:
            failures.append({**failure, 'affected_unit_ids': ids, 'seconds': seconds})
            outputs = []  # Provisional output never bypasses required global postprocessing.
            invalid = failure['status'] != 'MODEL_SYSTEM_FAILURE'
        else:
            outputs = final
    if invalid:
        outputs = []
    return {'frame_id': frame_id, 'trial_status': 'INCOMPLETE_INVALID_TRIAL' if invalid else 'VALID_OPERATIONAL_TRIAL',
            'outputs': outputs, 'opportunities': events, 'failure_events': failures,
            'opportunity_completion_rate': stage_rate('parser_opportunity', 'person', events),
            'frame_cost_seconds': sum(e.get('seconds', 0) for e in events) + global_seconds,
            'model_failure_retry_count': 0}


def run_native_frame(frame_id, opportunities, worker, *, skip_if_no_opportunities, validate_output):
    eligible = not skip_if_no_opportunities or bool(opportunities)
    if not eligible:
        event = {'unit_id': frame_id, 'eligible': False, 'status': 'SKIPPED_BY_ROUTING'}
        return {'frame_id': frame_id, 'trial_status': 'VALID_OPERATIONAL_TRIAL', 'native_output': None,
                'failure_events': [], 'native_frame_completion_rate': stage_rate('native_parser', 'frame', [event]),
                'frame_cost_seconds': 0.0}
    output, failure, seconds = _invoke(lambda frame: _checked(worker, frame, validate_output),
                                      frame_id, f'{frame_id}:native_frame')
    event = {'unit_id': frame_id, 'eligible': True, 'status': 'FAILED' if failure else 'COMPLETED'}
    return {'frame_id': frame_id,
            'trial_status': 'INCOMPLETE_INVALID_TRIAL' if failure and failure['status'] != 'MODEL_SYSTEM_FAILURE'
                            else 'VALID_OPERATIONAL_TRIAL',
            'native_output': output, 'failure_events': [{**failure, 'affected_unit_ids': [frame_id]}] if failure else [],
            'native_frame_completion_rate': stage_rate('native_parser', 'frame', [event]),
            'frame_cost_seconds': seconds}


class ConfiguredRunner:
    """The orchestration entry point reads only executable config, never prose."""
    def __init__(self, config_path, mode='CPU_FIXTURES', *, benchmark=False, population_role=None):
        from .policy import load_config
        self.config = load_config(config_path, benchmark=benchmark)
        if mode not in self.config['authorization']['allowed_modes']:
            raise ValueError('Execution mode has not been authorized')
        self.mode = mode
        from pathlib import Path
        self.study_root = Path(config_path).resolve().parents[1]
        if population_role is not None:
            from .validation_launch import require_validation_authorization, package_data, population_view
            if mode != 'VALIDATION_BENCHMARK' or not benchmark:
                raise ValueError('Population execution requires authorized validation benchmark mode')
            require_validation_authorization(self.config, self.study_root)
            images, templates = package_data(self.config, self.study_root)
            self.config = population_view(self.config, images, templates, population_role)
        from .policy import digest
        self._sealed_config = None
        if benchmark:
            from .immutable_config import seal
            self.config = seal(self.config)
            self._sealed_config = self.config
        self._loaded_config_digest = digest(self.config)

    def _check_config(self):
        if self._sealed_config is not None:
            if self.config is not self._sealed_config:
                raise ValueError('Loaded executable configuration replaced; create a new validated runner')
            return
        from .policy import digest
        if digest(self.config) != self._loaded_config_digest:
            raise ValueError('Loaded executable configuration mutated; create a new validated runner')

    def person_frame(self, frame_id, opportunities, worker, validator, finalizer=None):
        self._check_config()
        return run_person_jobs(frame_id, opportunities, worker, validate_output=validator,
                               failure_scope=self.config['routing']['person_failure_scope'], finalizer=finalizer)

    def native_frame(self, frame_id, opportunities, worker, validator):
        self._check_config()
        return run_native_frame(frame_id, opportunities, worker, validate_output=validator,
                                skip_if_no_opportunities=self.config['routing']['skip_native_if_no_opportunities'])

    def score_frame(self, mapping, model_binding, trusted_input, gt, predictions, *, lifecycle,
                    system_id=None, image_id=None, matching_view='primary'):
        self._check_config()
        from .scoring import score_frame
        if self.config.get('first_cohort', {}).get('channel_order_evidence', {}).get('required'):
            from .cohorts import require_config_channel_order
            require_config_channel_order(self.config, model_binding, study_root=self.study_root)
        from .contexts import select_context
        context = select_context(self.config, system_id, image_id, matching_view=matching_view)
        if self.config.get('first_cohort', {}).get('channel_order_evidence', {}).get('required') and not (context.get('require_verified_channel_order') or context.get('require_channel_order_evidence')):
            raise ValueError('Checkpoint channel-order evidence is required for semantic scoring')
        if self.config.get('first_cohort', {}).get('execution_spec', {}).get('semantic_scoring_enabled') is False:
            raise ValueError('Semantic scoring is disabled in this preparation-only execution profile')
        if self.config.get('cohort_policy', {}).get('support_binding_required') and context.get('require_checkpoint_specific_support') is not True:
            raise ValueError('Accepted cohort policy requires checkpoint-specific support evidence')
        result = score_frame(context, mapping, model_binding, trusted_input, gt, predictions, lifecycle=lifecycle)
        if self.config.get('scoring_contexts') is not None:
            result.update(system_id=system_id, image_id=image_id)
        return result

    def score_person_result(self, mapping, model_binding, trusted_input, gt, result, *, system_id=None, image_id=None):
        self._check_config()
        from .scoring import lifecycle_from_person_result
        lifecycle = lifecycle_from_person_result(result, self.config['routing']['person_failure_scope'])
        return self.score_frame(mapping, model_binding, trusted_input, gt, result['outputs'], lifecycle=lifecycle,
                                system_id=system_id, image_id=image_id)

    def comparison_report(self, population, frame_results, *, matching_view='primary'):
        self._check_config()
        from .comparison import summarize_comparison
        from .policy import digest
        definition = self.config['first_cohort']
        from .contexts import check_report_binding
        check_report_binding(self.config, population, frame_results, matching_view=matching_view)
        context = self.config.get('scoring_contexts', self.config.get('scoring_context'))
        binding = {'cohort_definition': definition, 'population_sha256': digest(population),
                   'mapping_sha256': self.config['cohort']['mapping_sha256'],
                   'scoring_context': context,
                   'primary_reporting_policy': self.config['primary_reporting_policy']}
        if matching_view != 'primary':
            if matching_view != 'secondary':
                raise ValueError('Unknown matching view')
            binding['matching_view'] = matching_view
            binding['threshold'] = self.config['evaluation']['secondary_threshold']
        revision = digest(binding)
        comparison = {'comparison_id': definition['comparison_id'] + ':' + revision[:12],
                      'definition_sha256': revision}
        return summarize_comparison(comparison, population, definition['models'], frame_results,
                                    self.config['primary_reporting_policy'])
