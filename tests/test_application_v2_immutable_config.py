"""Benchmark metadata sealing preserves values and supports isolated secondary views."""
import copy
import unittest
from src.application_v2.immutable_config import seal
from src.application_v2.policy import digest


class ImmutableConfigTests(unittest.TestCase):
    def test_nested_mutations_rejected_without_changing_digest(self):
        original={'contexts':{'system':{'image':{'threshold':.5,'labels':[0,1,2]}}}}
        frozen=seal(original)
        self.assertEqual(digest(frozen),digest(original))
        with self.assertRaises(TypeError):frozen['contexts']['system']['image']['threshold']=.75
        with self.assertRaises(TypeError):frozen['contexts']['system']['image']['labels'].append(3)
        with self.assertRaises(TypeError):frozen.update(extra=True)
        self.assertEqual(digest(frozen),digest(original))

    def test_deepcopy_can_form_secondary_view_without_mutating_sealed_context(self):
        frozen=seal({'threshold':.5,'labels':[0,1,2]})
        secondary=copy.deepcopy(frozen);secondary['threshold']=.75;secondary['labels'].append(3)
        self.assertEqual(frozen['threshold'],.5);self.assertEqual(frozen['labels'],[0,1,2])
        self.assertEqual(secondary['threshold'],.75)
