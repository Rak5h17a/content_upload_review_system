from datetime import datetime, timezone

from app.db import jobs_collection


class JobRepository:
    def __init__(self, collection=None):
        self.collection = collection or jobs_collection()

    def create(self, job_id, filename):
        self.collection.insert_one({
            "job_id": job_id,
            "filename": filename,
            "status": "PENDING",
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "errors_sample": [],
            "error": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

    def update(self, job_id, **fields):
        fields["updated_at"] = datetime.now(timezone.utc)
        self.collection.update_one({"job_id": job_id}, {"$set": fields})

    def get(self, job_id):
        doc = self.collection.find_one({"job_id": job_id}, {"_id": 0})
        if doc:
            for key in ("created_at", "updated_at"):
                if doc.get(key):
                    doc[key] = doc[key].isoformat()
        return doc