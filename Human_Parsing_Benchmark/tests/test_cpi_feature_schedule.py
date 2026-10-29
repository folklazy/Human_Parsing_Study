"""Reuse native numeric/immutability oracles for serial branch scheduling."""
from unittest.mock import patch
import test_cpi_feature_memory as native_reference
from cihp_benchmark.cpi_feature_schedule import install


class FeatureScheduleAcceptance(native_reference.FeatureBufferAcceptance):
    def setUp(self):
        self.installer = patch.object(native_reference, 'install', install)
        self.installer.start()

    def tearDown(self):
        self.installer.stop()
