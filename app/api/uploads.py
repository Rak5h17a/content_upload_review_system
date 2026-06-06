import os
import threading
import uuid

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app.repositories.job_repository import JobRepository
from app.services.csv_ingest import process_csv_file
from app.utils.errors import ApiError

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/v1/uploads")


@uploads_bp.post("")
def upload_csv():
    if "file" not in request.files:
        raise ApiError("No file part in request (expected form field 'file')")

    file = request.files["file"]
    if not file.filename:
        raise ApiError("No file selected")
    if not file.filename.lower().endswith(".csv"):
        raise ApiError("Only .csv files are accepted")

    job_id = uuid.uuid4().hex
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = secure_filename(file.filename)
    stored_path = os.path.join(upload_dir, f"{job_id}_{safe_name}")
    file.save(stored_path)  # streams to disk in chunks

    JobRepository().create(job_id, safe_name)

    # Pass the app object so the thread can push an app context for config/logging.
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=_run_ingest, args=(app, stored_path, job_id), daemon=True
    )
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "PENDING",
        "status_url": f"/api/v1/uploads/{job_id}",
    }), 202


@uploads_bp.get("/<job_id>")
def get_status(job_id):
    job = JobRepository().get(job_id)
    if not job:
        raise ApiError("Upload job not found", status_code=404, code="NOT_FOUND")
    return jsonify(job), 200


def _run_ingest(app, stored_path, job_id):
    with app.app_context():
        process_csv_file(stored_path, job_id)