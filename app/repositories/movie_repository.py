from pymongo.errors import BulkWriteError

from app.db import movies_collection


class MovieRepository:
    def __init__(self, collection=None):
        self.collection = collection or movies_collection()

    def insert_batch(self, docs):
        if not docs:
            return 0, 0
        try:
            # ordered=False so a duplicate in the batch doesn't abort the rest
            result = self.collection.insert_many(docs, ordered=False)
            return len(result.inserted_ids), 0
        except BulkWriteError as bwe:
            write_errors = bwe.details.get("writeErrors", [])
            duplicates = sum(1 for e in write_errors if e.get("code") == 11000)
            inserted = len(docs) - len(write_errors)
            return inserted, duplicates

    def find(self, query, sort_field, sort_dir, skip, limit):
        cursor = (
            self.collection.find(query)
            .sort(sort_field, sort_dir)
            .skip(skip)
            .limit(limit)
        )
        return [self._serialize(doc) for doc in cursor]

    def count(self, query):
        return self.collection.count_documents(query)

    @staticmethod
    def _serialize(doc):
        doc["id"] = str(doc.pop("_id"))
        rd = doc.get("release_date")
        if rd is not None:
            doc["release_date"] = rd.date().isoformat()
        return doc