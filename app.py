import io
import re
import requests

from flask import Flask, jsonify, request, send_from_directory, send_file

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from xml.sax.saxutils import escape


app = Flask(__name__)

TRANSCRIPT_API = "https://yt-transcript.net"


def valid_transcript_payload(data):
    text = (data.get("text") or "").strip()

    if not text:
        return None

    if len(text) > 2_000_000:
        return None

    return text


@app.get("/")
def home():
    try:
        return send_from_directory(".", "index.html")
    except Exception:
        return send_from_directory("static", "index.html")


@app.post("/api/transcribe")
def transcribe():

    data = request.get_json(silent=True) or {}

    video_id = (data.get("videoId") or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return jsonify(
            error="Link ou ID de vídeo inválido."
        ), 400

    try:
        response = requests.get(
            f"{TRANSCRIPT_API}/{video_id}",
            params={"fmt": "json"},
            timeout=35,
            headers={
                "User-Agent": "TranscreveTube/1.0"
            }
        )

        if response.status_code == 404:
            return jsonify(
                error="Não encontramos legendas acessíveis para este vídeo."
            ), 404

        response.raise_for_status()

        payload = response.json()

        if isinstance(payload, list):
            segments = payload

        elif isinstance(payload, dict):
            segments = (
                payload.get("transcript")
                or payload.get("segments")
                or payload.get("data")
                or []
            )

            if isinstance(segments, dict):
                segments = segments.get("segments") or []

        else:
            segments = []

        lines = []

        for item in segments:
            if isinstance(item, dict) and item.get("text"):
                lines.append(str(item["text"]).strip())

        transcript_text = "\n".join(
            line for line in lines if line
        )

        if not transcript_text:
            return jsonify(
                error="O serviço não retornou uma transcrição utilizável. Tente novamente mais tarde."
            ), 502

        language = (
            payload.get("language", "")
            if isinstance(payload, dict)
            else ""
        )

        return jsonify(
            text=transcript_text,
            language=language
        )

    except requests.Timeout:
        return jsonify(
            error="A consulta demorou demais. Tente novamente."
        ), 504

    except requests.RequestException:
        return jsonify(
            error="Não foi possível consultar o serviço de legendas agora."
        ), 502

    except ValueError:
        return jsonify(
            error="O serviço retornou uma resposta inesperada."
        ), 502


@app.post("/api/download/pdf")
def download_pdf():

    data = request.get_json(silent=True) or {}

    transcript = valid_transcript_payload(data)

    if not transcript:
        return jsonify(
            error="Não há transcrição para baixar ou o texto é muito grande."
        ), 400

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Transcrição do YouTube"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TranscriptTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#18324b"),
        alignment=TA_LEFT,
        spaceAfter=14
    )

    body_style = ParagraphStyle(
        "TranscriptBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        spaceAfter=7,
        textColor=colors.HexColor("#202833")
    )

    story = [
        Paragraph("Transcrição do YouTube", title_style)
    ]

    for paragraph in transcript.splitlines():

        paragraph = paragraph.strip()

        if paragraph:
            story.append(
                Paragraph(escape(paragraph), body_style)
            )
        else:
            story.append(Spacer(1, 6))

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="transcricao-youtube.pdf"
    )


@app.post("/api/download/docx")
def download_docx():

    data = request.get_json(silent=True) or {}

    transcript = valid_transcript_payload(data)

    if not transcript:
        return jsonify(
            error="Não há transcrição para baixar ou o texto é muito grande."
        ), 400

    document = Document()

    section = document.sections[0]

    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    heading = document.add_heading(
        "Transcrição do YouTube",
        level=1
    )

    heading.style.font.name = "Arial"
    heading.style.font.color.rgb = RGBColor(24, 50, 75)

    for paragraph in transcript.splitlines():

        p = document.add_paragraph(paragraph)

        p.paragraph_format.space_after = Pt(6)

        for run in p.runs:
            run.font.name = "Arial"
            run.font.size = Pt(11)

    buffer = io.BytesIO()

    document.save(buffer)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name="transcricao-youtube.docx"
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
