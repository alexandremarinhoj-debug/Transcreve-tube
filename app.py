import re
import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")

TRANSCRIPT_API = "https://yt-transcript.net"


@app.get("/")
def home():
    return send_from_directory(".", "index.html")


@app.post("/api/transcribe")
def transcribe():
    data = request.get_json(silent=True) or {}
    video_id = (data.get("videoId") or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return jsonify(error="Link ou ID de vídeo inválido."), 400

    try:
        response = requests.get(
            f"{TRANSCRIPT_API}/{video_id}",
            params={"fmt": "json"},
            timeout=35,
            headers={"User-Agent": "TranscreveTube/1.0"}
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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
