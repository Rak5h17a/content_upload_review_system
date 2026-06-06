import os

from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "imdb_content")

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    INGEST_BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "2000"))

    # 2 GB default so a 1 GB CSV is comfortably allowed.
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024 * 1024)))


class TestConfig(Config):
    """Used by the pytest suite -- points at an in-memory Mongo (mongomock)."""
    TESTING = True
    MONGO_DB_NAME = "imdb_content_test"