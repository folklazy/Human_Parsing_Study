"""Exercise the actual generated guard; no GPU/model execution."""
import ast
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

H=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'scripts'),str(H/'src'),str(H.parent/'CCTV_Human_Parsing_Benchmark/scripts')]
import finish_controlled_cihp_sapiens1b as runner
import continue_controlled_cihp_resources as parent


def actual_guard(enabled=False, free_disk=100, stream=0, free_vram=4*2**30):
    source,_=runner.generated_worker()
    tree=ast.parse(source)
    worker=tree.body[0]
    node=next(n for n in worker.body if isinstance(n,ast.FunctionDef) and n.name=='guard')
    module=ast.Module(body=[node],type_ignores=[])
    ns=dict(config=dict(minimum_free_gib=50,max_stream_gib=80,max_hours=24,
                       execution_time_limit_enabled=enabled,
                       prior_execution_seconds={'Sapiens2_1b':86402.74},prior_stream_bytes={},
                       min_forward_free_MiB=1024),
            shutil=SimpleNamespace(disk_usage=lambda _:SimpleNamespace(free=free_disk*2**30)),
            root=None,output=None,state={'completed':0},measured_storage=[stream*2**30,0],
            bytes_written=stream*2**30,mid='Sapiens2_1b',
            time=SimpleNamespace(monotonic=lambda:100),started=0,
            torch=SimpleNamespace(cuda=SimpleNamespace(mem_get_info=lambda:(free_vram,16*2**30),
                memory_allocated=lambda:0,memory_reserved=lambda:0)))
    exec(compile(ast.fix_missing_locations(module),'<actual-worker-guard>','exec'),ns)
    return ns['guard']


class TimeWaiver(unittest.TestCase):
    def test_only_time_condition_differs(self):
        old,_=parent.generated_worker();new,changes=runner.generated_worker()
        self.assertEqual(new.replace(runner.AMENDED_TIME_CONDITION,runner.TIME_CONDITION),old)
        self.assertEqual(len(changes),13)

    def test_authorized_elapsed_over_24h_proceeds(self):
        actual_guard()()

    def test_original_enabled_cap_still_stops(self):
        with self.assertRaisesRegex(RuntimeError,'RESOURCE_TIME_GUARD'):actual_guard(enabled=True)()

    def test_free_space_guard_retained(self):
        with self.assertRaisesRegex(RuntimeError,'RESOURCE_DISK_FREE_GUARD'):actual_guard(free_disk=49)()

    def test_cumulative_stream_guard_retained(self):
        with self.assertRaisesRegex(RuntimeError,'RESOURCE_STREAM_DISK_GUARD'):actual_guard(stream=81)()

    def test_vram_guard_retained(self):
        with self.assertRaisesRegex(RuntimeError,'RESOURCE_VRAM_HEADROOM_GUARD'):actual_guard(free_vram=1023*2**20)()


if __name__=='__main__':unittest.main()
