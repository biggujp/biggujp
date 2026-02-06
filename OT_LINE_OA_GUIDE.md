# คู่มือสร้างใบแจ้งขอทำ OT (ภาษาไทย + ญี่ปุ่น) ผ่าน LINE OA

เอกสารนี้อธิบายวิธีใช้งานตัวอย่างโค้ด `main.py` สำหรับรับข้อความจาก LINE OA แล้วสร้าง PDF ใบแจ้งขอทำ OT แบบสองภาษา (ไทย + ญี่ปุ่น) อัตโนมัติ

## โครงสร้างข้อความที่ต้องส่ง
ส่งข้อความผ่าน LINE OA ตามรูปแบบนี้:

```
OT ชื่อ-นามสกุล|แผนก|ชื่อโครงการ|วันที่ทำ OT|เวลาเริ่ม-สิ้นสุด|ชั่วโมง|เหตุผล
```

ตัวอย่าง:

```
OT สมชาย ใจดี|Production|Project Sakura|2024-07-16|18:00-21:00|3|เร่งงานส่งลูกค้า
```

## การตั้งค่าเบื้องต้น
1. ติดตั้งแพ็กเกจ:
   ```bash
   pip install -r requirements.txt
   ```
2. สร้างไฟล์ `.env` และกำหนดค่าตาม `.env.example`
3. ตั้งค่า Webhook URL ใน LINE Developers ให้ชี้ไปที่:
   ```
   https://<your-domain>/callback
   ```
4. เรียกใช้งานเซิร์ฟเวอร์:
   ```bash
   python main.py
   ```

## การใช้งานผ่าน Docker (แนะนำสำหรับ OMV7)
1. สร้างไฟล์ `.env` ตาม `.env.example` (ตรวจสอบ `FONT_TTF_PATH` ให้ถูกต้อง)
2. สร้างและรันด้วย Docker Compose:
   ```bash
   docker compose up -d --build
   ```
3. ตั้งค่า Webhook URL ใน LINE Developers ให้ชี้ไปที่:
   ```
   https://<your-domain>/callback
   ```
4. ตรวจสอบ log หากมีปัญหา:
   ```bash
   docker compose logs -f
   ```

## การดาวน์โหลด PDF
ระบบจะบันทึก PDF ไว้ในโฟลเดอร์ `output/` และสามารถดาวน์โหลดผ่าน URL:

```
https://<your-domain>/pdf/<filename>
```

## หมายเหตุเรื่องฟอนต์
ควรใช้ฟอนต์ที่รองรับภาษาไทย + ญี่ปุ่น เช่น:
- Noto Sans Thai
- Noto Sans JP
- Noto Sans CJK

กำหนดตำแหน่งไฟล์ฟอนต์ผ่านตัวแปร `FONT_TTF_PATH` ใน `.env`

> หากใช้ Docker ตัวอย่างนี้ติดตั้ง Noto CJK ไว้แล้ว
> ค่าแนะนำคือ `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`
