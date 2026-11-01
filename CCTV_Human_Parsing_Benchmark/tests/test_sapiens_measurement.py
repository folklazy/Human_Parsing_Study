"""Hand-counted checks of the independent measurement path, not model quality."""
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_saved_sapiens import confusion_counts


class MeasurementCases(unittest.TestCase):
    def test_full_grid_false_positives(self):
        gt=np.array([[1,1,0,0]],bool);pred=np.array([[1,0,1,1]],bool)
        self.assertEqual(confusion_counts(gt,pred),(1,2,1))

    def test_clipping_can_remove_both_correct_and_incorrect_pixels(self):
        gt=np.array([[1,1,0,0]],bool);raw=np.array([[0,1,1,1]],bool)
        keep=np.array([[0,1,0,0]],bool)
        self.assertEqual(confusion_counts(gt,raw),(1,2,1))
        self.assertEqual(confusion_counts(gt,raw&keep),(1,0,1))
        keep=np.array([[0,0,1,0]],bool)
        self.assertEqual(confusion_counts(gt,raw&keep),(0,1,2))

    def test_missing_prediction_retains_false_negatives(self):
        gt=np.array([[1,1,0]],bool)
        self.assertEqual(confusion_counts(gt,np.zeros_like(gt)),(0,0,2))


if __name__=='__main__':unittest.main()
