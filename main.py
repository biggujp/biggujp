import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, request, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise RuntimeError("Missing LINE credentials. Check LINE_CHANNEL_ACCESS_TOKEN/LINE_CHANNEL_SECRET.")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def register_fonts() -> None:
    font_path = os.getenv("FONT_TTF_PATH")
    if not font_path or not Path(font_path).exists():
        raise RuntimeError("FONT_TTF_PATH must point to a Japanese+Thai capable TTF file.")
    pdfmetrics.registerFont(TTFont("JPTH", font_path))


def draw_bilingual_label(pdf: canvas.Canvas, x: float, y: float, th: str, jp: str) -> None:
    pdf.setFont("JPTH", 11)
    pdf.drawString(x, y, th)
    pdf.setFont("JPTH", 10)
    pdf.setFillColor(colors.grey)
    pdf.drawString(x + 180, y, jp)
    pdf.setFillColor(colors.black)


def generate_ot_pdf(payload: dict, output_path: Path) -> Path:
    register_fonts()
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    margin_x = 20 * mm
    cursor_y = height - 25 * mm

    pdf.setFont("JPTH", 16)
    pdf.drawString(margin_x, cursor_y, "ใบแจ้งขอทำ OT / 残業申請書")
    cursor_y -= 12 * mm

    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x, cursor_y, f"วันที่ออกเอกสาร / 発行日: {payload['issue_date']}")
    cursor_y -= 12 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "ชื่อ-นามสกุล:", "氏名")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["name"])
    cursor_y -= 10 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "แผนก:", "部署")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["department"])
    cursor_y -= 10 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "ชื่อโครงการ:", "プロジェクト名")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["project_name"])
    cursor_y -= 10 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "วันที่ทำ OT:", "残業日")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["ot_date"])
    cursor_y -= 10 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "ช่วงเวลา:", "時間")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["ot_time"])
    cursor_y -= 10 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "จำนวนชั่วโมง:", "時間数")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["hours"])
    cursor_y -= 10 * mm

    draw_bilingual_label(pdf, margin_x, cursor_y, "เหตุผลการทำ OT:", "残業理由")
    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x + 240, cursor_y, payload["reason"])
    cursor_y -= 18 * mm

    pdf.setFont("JPTH", 12)
    pdf.drawString(margin_x, cursor_y, "ผู้ขอทำ OT / 申請者")
    pdf.drawString(margin_x + 230, cursor_y, "ผู้อนุมัติ / 承認者")
    cursor_y -= 25 * mm
    pdf.line(margin_x, cursor_y, margin_x + 160, cursor_y)
    pdf.line(margin_x + 230, cursor_y, margin_x + 390, cursor_y)

    pdf.showPage()
    pdf.save()
    return output_path


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent) -> None:
    text = event.message.text.strip()
    if not text.startswith("OT"):
        return
    parts = [item.strip() for item in text[2:].split("|")]
    if len(parts) != 7:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="รูปแบบไม่ถูกต้อง กรุณาส่ง:\n"
                "OT ชื่อ-นามสกุล|แผนก|ชื่อโครงการ|วันที่ทำ OT|เวลาเริ่ม-สิ้นสุด|ชั่วโมง|เหตุผล"
            ),
        )
        return
    payload = {
        "name": parts[0],
        "department": parts[1],
        "project_name": parts[2],
        "ot_date": parts[3],
        "ot_time": parts[4],
        "hours": parts[5],
        "reason": parts[6],
        "issue_date": "วันนี้",
    }
    output_path = OUTPUT_DIR / f"ot_{event.message.id}.pdf"
    generate_ot_pdf(payload, output_path)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="สร้าง PDF เรียบร้อยแล้ว กรุณาดาวน์โหลดจากเซิร์ฟเวอร์"),
    )


@app.route("/callback", methods=["POST"])
def callback() -> str:
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        abort(400)
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@app.route("/pdf/<filename>", methods=["GET"])
def download_pdf(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        abort(404)
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
