# Research references — bounded decision-focused review

ตรวจ primary URLs วันที่ 21 ตุลาคม 2026 UTC อ่าน README/abstract และ source excerpts ที่เกี่ยวข้อง ไม่อ้างว่าอ่านทุก paper/source tree ครบ หยุดค้นเมื่อได้ข้อจำกัดที่ใช้ตัดสินแล้ว ไม่มีการเพิ่ม training method/model/dataset จาก references เหล่านี้

| Reference | สิ่งที่ตรวจและนำมาใช้ | สิ่งที่ไม่ยืม / ข้อจำกัด |
|---|---|---|
| [MSeg official API](https://github.com/mseg-dataset/mseg-api), [taxonomy converter source](https://github.com/mseg-dataset/mseg-api/blob/master/mseg/taxonomy/taxonomy_converter.py) | Explicit label correspondence และแยก probability transformation จาก hard-label lookup; source มี linear inference taxonomy mapping | ไม่ได้ใช้ MSeg taxonomy หรือการ relabel dataset ของเขา ไม่รับรอง project mapping/target count อัตโนมัติ Primary เราเลือก hard-output lookup เพราะ artifact/interface ของแต่ละ checkpoint ไม่เหมือนกัน; information ที่หายไป recover จาก lookup ไม่ได้ |
| [Graphonomy, Gong et al., CVPR 2019](https://arxiv.org/abs/1904.04536) | Abstract แสดงว่าความต่าง label granularity/domain เป็นปัญหาจริงและวิธีใช้ learned graph transfer | ไม่ใช้ learned graph transfer หรือฝึก universal model ในงานนี้ Post-hoc label mapping ของ pretrained outputs ไม่ได้ให้ความสามารถใหม่แบบวิธีที่ผ่าน training จึง split Dress/Apparel เป็นละเอียดกว่าเดิมไม่ได้ |
| [Parsing R-CNN, Yang et al., CVPR 2019 official repo](https://github.com/soeaver/Parsing-R-CNN) | Instance-level parsing architecture, model/evaluator format และความสำคัญของการเก็บ person hypotheses | ไม่ถือว่า RP-R-CNN ทุก fork/checkpoint/evaluator เป็น implementation เดียวกัน ไม่อ้าง bbox matching ของโครงการเป็น official parsing AP และไม่อ้างงานที่มี frozen YOLO plus native detector เป็น parsing-only cost |
| [Boundary IoU, Cheng et al., CVPR 2021](https://arxiv.org/abs/2103.16562), [official implementation](https://github.com/bowenc0221/boundary-iou-api) | Boundary-sensitive diagnostic ช่วยแยกความกระชับของ mask ที่ area IoU อาจไม่ชัด; implementation ใช้ dilation ratio จาก image diagonal | เสนอเฉพาะ study void-aware Boundary IoU บน matched masks ไม่ใช่ official Boundary AP/PQ; การจัดการ CCIHP void และ matching เป็น study-specific adaptation ที่ต้องทดสอบ ไม่ใช้ paper เป็นหลักฐานว่า target mapping ของเราถูกแล้ว |

## Local primary implementations ที่ใช้ยืนยัน operational facts

Pinned revisions/metadata อ้างใน [checkpoint matrix](../registry/CHECKPOINT_ROUTE_REVIEW.csv) และ review INPUT_EVIDENCE:

- M2FP/D2FP CIHP configs และ `instance_parsing_inference`/upstream parsing evaluator: semantic catalog 20 กับ auxiliary Human query; human ownership + semantic label composition; native TTA และ CUDA OOM wrappers
- QANet config และ `InstanceBox.convert`: external person proposals, H512×W384, aspect adjustment/expansion1.25; ไม่ใช่ native full-frame person detector ใน route ที่มี evidence
- RP-R-CNN config/worker: R50 Faster R-CNN/internal ROI parsing, native postprocessing และ scores
- [Sapiens2 pinned SEG documentation](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/docs/SEG.md): 29-label catalog ชื่อ Face_Neck, Torso, Apparel แต่ไม่มี annotation definition ที่พิสูจน์ exact CCIHP partition จึงคง residual semantic uncertainty แทนการค้นไม่สิ้นสุด

Published methods / official implementation facts / project-specific design proposals / unresolved hypotheses แยกจากกันในแผน ไม่มี citation ใดทำให้ proposed spec กลายเป็น accepted หรือพร้อม GPU execution
