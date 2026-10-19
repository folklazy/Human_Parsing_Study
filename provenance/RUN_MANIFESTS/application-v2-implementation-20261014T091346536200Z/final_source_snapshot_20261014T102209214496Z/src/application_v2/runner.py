"""Dependency-injected person/frame lifecycle, with no model import or download."""
from time import perf_counter
from .contracts import stage_rate


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
    except (ExternalInfrastructureFailure, UnresolvedFailure) as exc:
        return None, {'event_id': event_id, 'status': 'INVALID_ENV' if isinstance(exc, ExternalInfrastructureFailure)
                      else 'UNRESOLVED_EVENT', 'exception': str(exc)}, perf_counter() - start
    except Exception as exc:
        return None, {'event_id': event_id, 'status': 'MODEL_SYSTEM_FAILURE',
                      'exception_type': type(exc).__name__, 'exception': str(exc)}, perf_counter() - start


def _checked(function, argument, validator):
    result = function(argument)
    if result is not None and validator(result) is False:
        raise ValueError('Output contract rejected')
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
                raise ValueError('Finalizer must return a list of validated person outputs')
            for person in final:
                if validate_output(person) is False:
                    raise ValueError('Finalizer output contract rejected')
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
    def __init__(self, config_path, mode='CPU_FIXTURES'):
        from .policy import load_config
        self.config = load_config(config_path)
        if mode not in self.config['authorization']['allowed_modes']:
            raise ValueError('Execution mode has not been authorized')
        self.mode = mode

    def person_frame(self, frame_id, opportunities, worker, validator, finalizer=None):
        return run_person_jobs(frame_id, opportunities, worker, validate_output=validator,
                               failure_scope=self.config['routing']['person_failure_scope'], finalizer=finalizer)

    def native_frame(self, frame_id, opportunities, worker, validator):
        return run_native_frame(frame_id, opportunities, worker, validate_output=validator,
                                skip_if_no_opportunities=self.config['routing']['skip_native_if_no_opportunities'])
