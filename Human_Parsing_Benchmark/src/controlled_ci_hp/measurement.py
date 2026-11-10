"""Synchronized spans around existing adapters, preserving their return values."""
from contextlib import contextmanager, ExitStack
from time import perf_counter


class Measurements:
    def __init__(self, sync=lambda: None):
        self.sync = sync
        self.records = []

    @contextmanager
    def span(self, name, parent=None):
        self.sync()
        start = perf_counter()
        status = 'FAILED'
        try:
            yield
            status = 'COMPLETE'
        finally:
            self.sync()
            self.records.append(dict(stage=name, parent=parent, seconds=perf_counter()-start,
                                     inclusive=True, status=status))

    @contextmanager
    def wrap(self, owner, attribute, stage):
        original = getattr(owner, attribute)
        def measured(*args, **kwargs):
            with self.span(stage, 'adapter_total'):
                return original(*args, **kwargs)
        setattr(owner, attribute, measured)
        try:
            yield
        finally:
            setattr(owner, attribute, original)

    def infer(self, adapter, rgb, path, box):
        import controlled_roi_models as shared
        with ExitStack() as stack:
            if adapter.family == 'Sapiens2':
                import sapiens_input_variants as variants
                stack.enter_context(self.wrap(variants, 'letterbox', 'parser_preprocess'))
                stack.enter_context(self.wrap(variants, 'restore_letterbox', 'parser_mapback'))
                stack.enter_context(self.wrap(adapter.model, 'forward', 'native_model_call'))
            elif adapter.family == 'QANet':
                stack.enter_context(self.wrap(shared, 'prepare_qanet_rgb', 'parser_preprocess'))
                stack.enter_context(self.wrap(shared, 'restore_qanet_probabilities', 'parser_mapback'))
                stack.enter_context(self.wrap(adapter.model, 'conv_body_net', 'parser_backbone'))
                stack.enter_context(self.wrap(adapter.model, 'parsing_net', 'parser_head'))
            else:
                # Internal detector/decoder/file I/O may be inside this call.
                # Label the span inclusive rather than calling it pure forward.
                stack.enter_context(self.wrap(adapter.model, 'forward', 'native_model_call_inclusive'))
            with self.span('adapter_total'):
                return adapter.infer(rgb, path, box)

    def report(self):
        return dict(spans=self.records, synchronization='CUDA synchronize at span boundaries',
                    missing_substages={'parser_transfer': 'Not isolated from native API',
                                       'internal_file_IO': 'CPI native call includes file exporter'},
                    summation='Nested spans overlap; use measured frame wall for pipeline total',
                    speed_ranking_allowed=False)
