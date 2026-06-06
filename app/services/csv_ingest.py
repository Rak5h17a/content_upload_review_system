import csv
import os

from config import Config
from app.models.movie import EXPECTED_COLUMNS, transform_row
from app.repositories.job_repository import JobRepository
from app.repositories.movie_repository import MovieRepository

# overview text can be very long
csv.field_size_limit(10 * 1024 * 1024)


def process_csv_file(file_path, job_id, batch_size=None):
    batch_size = batch_size or Config.INGEST_BATCH_SIZE
    movies = MovieRepository()
    jobs = JobRepository()

    inserted = skipped = failed = 0
    errors_sample = []
    batch = []

    jobs.update(job_id, status="PROCESSING")
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)

            header = set(reader.fieldnames or [])
            missing = EXPECTED_COLUMNS - header
            if missing:
                raise ValueError(f"CSV missing expected columns: {sorted(missing)}")

            for line_no, raw in enumerate(reader, start=2):
                doc, error = transform_row(raw)
                if error:
                    failed += 1
                    if len(errors_sample) < 50:
                        errors_sample.append({"row": line_no, "error": error})
                    continue

                batch.append(doc)
                if len(batch) >= batch_size:
                    ins, dup = movies.insert_batch(batch)
                    inserted += ins
                    skipped += dup
                    batch = []
                    jobs.update(job_id, processed=inserted, skipped=skipped, failed=failed)

            if batch:
                ins, dup = movies.insert_batch(batch)
                inserted += ins
                skipped += dup

        jobs.update(
            job_id,
            status="COMPLETED",
            processed=inserted,
            skipped=skipped,
            failed=failed,
            errors_sample=errors_sample,
        )
    except Exception as exc:
        jobs.update(job_id, status="FAILED", error=str(exc))
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass