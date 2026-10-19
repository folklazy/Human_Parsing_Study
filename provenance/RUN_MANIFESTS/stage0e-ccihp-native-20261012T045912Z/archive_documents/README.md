# Characterized Crowd Instance-level Human Parsing (CCIHP) dataset


CCIHP dataset provides pixelwise image annotations for:

- human segmentation, 
- semantic attribute segmentation and 
- semantic attribute characterization.


## Dataset description

- Images:       
The image data are the same as [CIHP dataset](https://www.sysuhcp.com/lip/index.php) (see Section Related work) proposed at the [LIP (Look Into Person) challenge](https://competitions.codalab.org/competitions/23431). They are available at [google drive](https://drive.google.com/drive/folders/0BzvH3bSnp3E9ZW9paE9kdkJtM3M?usp=sharing) and [baidu drive](http://pan.baidu.com/s/1nvqmZBN).


- Annotations:  
Please download and unzip the [CCIHP_icip.zip file](). 
The CCIHP annotations can be found in the `Training` and `Validation` sub-folders of `CCIHP_icip/dataset/` folder. They correspond to, respectively, 28,280 training images and 5,000 validation images.
Annotations consist of:
      - **Human_ids**: person instance labels
      - **Instance_ids**: attribute instance labels
      - **Category_ids**: attribute category labels
      - **Size_ids**: size category labels
      - **Pattern_ids**: pattern category labels
      - **Color_ids**: color category labels
      

  Label meaning for semantic **attribute/body parts**:
    
  1. Hat: Hat, helmet, cap, hood, veil, headscarf, part covering the skull and hair of a hood/balaclava, crown...
  2. Hair
  3. Glove
  4. Sunglasses/Glasses: Sunglasses, eyewear, protective glasses...
  5. UpperClothes: T-shirt, shirt, tank top, sweater under a coat, top of a dress...
  6. Face Mask: Protective mask, surgical mask, carnival mask, facial part of a balaclava, visor of a helmet...
  7. Coat: Coat, jacket worn without anything on it, vest with nothing on it, a sweater with nothing on it...
  8. Socks
  9. Pants: Pants, shorts, tights, leggings, swimsuit bottoms... (clothing with 2 legs)
  10. Torso-skin
  11. Scarf: Scarf, bow tie, tie...
  12. Skirt: Skirt, kilt, bottom of a dress...
  13. Face
  14. Left-arm (naked part)
  15. Right-arm (naked part)
  16. Left-leg (naked part)
  17. Right-leg (naked part)
  18. Left-shoe
  19. Right-shoe
  20. Bag: Backpack, shoulder bag, fanny pack... (bag carried on oneself)
  21. Others: Jewelry, tags, bibs, belts, ribbons, pins, head decorations, headphones...


  Label meaning for **size characterization**:

  1. Short: Small, short, narrow
  2. Long: Long, large, big
  3. Undetermined: If the attribute is partially hidden
  4. Sparse/bald: For hair attribute only

  Label meaning for **pattern characterization**:
  
  1. Solid
  2. Geometrical: Stripes, Checks, Dots...
  3. Fancy: Flowers, Military...
  4. Letters: Letters, numbers, symbols...

  Label meaning for **color characterization**:
  
  1. Dark: No dominant color, includes black, navy blue
  2. Medium: No dominant color, including gray
  3. Light: No dominant color, including white
  4. Brown
  5. Red
  6. Pink
  7. Yellow
  8. Orange
  9. Green
  10. Blue
  11. Purple
  12. Multicolor: When there is a pattern with several colors


## Related work
Our work is based on CIHP image dataset from: 
Ke Gong, Xiaodan Liang, Yicheng Li, Yimin Chen, Ming Yang and Liang Lin, "Instance-level Human Parsing via Part Grouping Network", *ECCV* 2018.

## Evaluation

To evaluate the predictions given by a Human Parsing with Characteristics model, you can run the python scripts in `CCIHP_icip/evaluation/` folder.

### Requirements
- python==3.6+
- opencv-python
- pillow

### Evaluation steps

1. Run `generate_characteristic_instance_part_ccihp.py` 
2. Run `eval_test_characteristic_inst_part_ap_ccihp.py` for mean Average Precision based on characterized region (AP^(cr)_(vol)). It evaluates the prediction of characteristic (class & score) relative to each instanced and characterized attribute mask, independently of the attribute class prediction. 
3. Run `metric_ccihp_miou_evaluation.py` for a mIoU performance evaluation of semantic predictions (attribute or characteristics).


## License

Data annotations are under Creative Commons Attribution Non Commercial 4.0 license (see LICENSE file).

Evaluation codes are under MIT license.

## Citation
A. Loesch and R. Audigier, "Describe Me If You Can! Characterized Instance-Level Human Parsing," *2021 IEEE International Conference on Image Processing (ICIP)*, 2021, pp. 2528-2532, doi: [10.1109/ICIP42928.2021.9506509](https://doi.org/10.1109/ICIP42928.2021.9506509).

```BibTeX
@INPROCEEDINGS{ccihp_dataset_2021,
  author={Loesch, Angelique and Audigier, Romaric},
  booktitle={2021 IEEE International Conference on Image Processing (ICIP)}, 
  title={Describe Me If You Can! Characterized Instance-Level Human Parsing}, 
  year={2021},
  volume={},
  number={},
  pages={2528-2532},
  doi={10.1109/ICIP42928.2021.9506509}},
```


## Contact
If you have any question about this dataset, you can contact us by email at:
ccihp@cea.fr
