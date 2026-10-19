# CDGNet — ดาวน์โหลด checkpoint สำเร็จ 15 ตุลาคม 2026

**สถานะ: DOWNLOADED + CPU STRUCTURAL INSPECTION PASS; model inference ยัง NOT_TESTED**

ลิงก์ Google Drive `1rzLU-wK6rEorCNJfwrmIu5hY2wRMyKTK` ที่ README ผู้พัฒนาให้เป็นโฟลเดอร์ ไม่ใช่ไฟล์ backbone เพียงตัวเดียว ภายในมีทั้ง trained parser และ ImageNet initializer การตรวจรอบก่อนหยุดที่ Baidu และไม่ได้ไล่โฟลเดอร์นี้ครบ จึงเป็นข้อจำกัดของการตรวจครั้งก่อน ไม่ใช่ checkpoint หายหรือจำเป็นต้องล็อกอิน Baidu

| ไฟล์จาก author-linked Drive | ขนาด | บทบาท | การดำเนินการ |
|---|---:|---|---|
| LIP_epoch_149.pth | 267,470,799 bytes | CDGNet ResNet101 ที่ฝึก human parsing บน LIP; 20 classes รวม background | ดาวน์โหลดแล้ว |
| resnet101-imagenet.pth | 179,190,439 bytes | ImageNet initialization สำหรับ backbone ตอนฝึก | ไม่ดาวน์โหลด: official evaluation โหลด trained parser ตัวเดียว |

ชื่อไฟล์จริงคือ `resnet101-imagenet.pth` ตาม folder listing โค้ด `run_evaluate.sh` ใช้ `--restore-from ./snapshots/LIP_epoch_149.pth`; `evaluate.py` อ่าน checkpoint นี้ลง model โดยไม่โหลด ImageNet initializer อีกครั้ง

## ไฟล์บน server และ provenance

- Workspace-relative path: `models/human_parsing/cdgnet/CDGNet_R101_LIP/LIP_epoch_149.pth`
- Bytes: 267,470,799
- SHA256: `26003d4cd38ff63b3bc54e3e8840d873a5be09e3924f9a3eb741b101fb4c8df8`
- Official source commit: `9daf7ddee6045c151c90a2e300946ea5f5717591`
- Source repository: https://github.com/tjpulkl/CDGNet
- Author-linked folder: https://drive.google.com/drive/folders/1rzLU-wK6rEorCNJfwrmIu5hY2wRMyKTK
- Parser file: https://drive.google.com/file/d/1X9dWbu1jI8tYEX8T88luP_nI3myoxes-/view

ตรวจขนาดกับ metadata ของ Drive และคำนวณ SHA256 หลังดาวน์โหลด SHA256 เป็น local content fingerprint; ผู้พัฒนาไม่ได้ให้ expected SHA256 แยก จึงไม่เรียกว่า independently authenticated checksum

## การตรวจที่รันจริง

อ่านด้วย PyTorch `torch.load(..., map_location='cpu', weights_only=True)` ไม่สร้าง model และไม่รัน inference:

- 603 tensor entries; ทุก tensor เป็น FP32 และ finite
- tensor elements รวม buffers 66,838,456; ค่านี้ไม่ใช่จำนวน trainable parameters ที่ตรวจจาก model
- decoder `module.layer6.conv4.weight` มี shape `[20, 256, 1, 1]` และ bias `[20]` สอดคล้องกับ parsing head 20 classes
- ไฟล์เป็น legacy PyTorch serialization ไม่ใช่ ZIP; weights-only decoding ผ่าน ไม่อ้าง ZIP CRC สำหรับไฟล์นี้

สิ่งที่ยังไม่ทดสอบ: strict architecture load, GPU FP32 inference, peak memory และ canonical parser adapter สถานะ license ของ code/checkpoint คงอ้าง prior review ซึ่งยังไม่ยืนยัน grant; การดาวน์โหลดครั้งนี้ไม่ใช่การรับรองสิทธิ์หรืออนุญาต benchmark

[Acquisition evidence](../provenance/RUN_MANIFESTS/cdgnet-acquisition-20261015T082226739949Z/ACQUISITION.json) · [CPU inspection](../provenance/RUN_MANIFESTS/cdgnet-acquisition-20261015T082226739949Z/WEIGHTS_INSPECTION.json) · [Checkpoint manifest](../provenance/CDGNET_CHECKPOINT_MANIFEST_V1.json) · [Registry V5](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V5.csv)

รอบนี้ไม่ติดตั้ง package ไม่แก้ environments/datasets/YOLO ไม่รัน parser หรือ full benchmark หลักฐาน handoff รุ่นก่อนคงไว้เป็นประวัติ; สถานะ acquisition ล่าสุดให้อ้างเอกสารนี้และ registry V5
