import os
import uuid

from flask import Blueprint, request, jsonify, current_app, send_from_directory

from app.auth.decorators import login_required

upload_bp = Blueprint("upload", __name__, url_prefix="/api")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_dir():
    base = current_app.config.get(
        "UPLOAD_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads"),
    )
    base = os.path.abspath(base)
    os.makedirs(base, exist_ok=True)
    return base


@upload_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify(error="No file provided"), 400

    f = request.files["file"]
    if not f.filename or not _allowed(f.filename):
        return jsonify(error="Invalid file type (png/jpg/jpeg/webp/gif only)"), 400

    # Check size
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify(error="File too large (max 5MB)"), 400

    ext = f.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    save_path = os.path.join(_upload_dir(), filename)
    f.save(save_path)

    url = f"/api/uploads/{filename}"
    return jsonify(url=url, filename=filename), 201


@upload_bp.route("/uploads/<filename>", methods=["GET"])
def serve_upload(filename):
    return send_from_directory(_upload_dir(), filename)
