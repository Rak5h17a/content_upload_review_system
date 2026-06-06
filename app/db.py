from pymongo import ASCENDING, DESCENDING, MongoClient

from config import Config

_client = None
_db = None


def init_db(uri=None, db_name=None):
    global _client, _db
    uri = uri or Config.MONGO_URI
    db_name = db_name or Config.MONGO_DB_NAME
    _client = MongoClient(uri)
    _db = _client[db_name]
    return _db


def get_db():
    global _db
    if _db is None:
        init_db()
    return _db


def movies_collection():
    return get_db()["movies"]


def jobs_collection():
    return get_db()["upload_jobs"]


def ensure_indexes():
    
    movies = movies_collection()

    movies.create_index(
        [("title", ASCENDING), ("release_date", ASCENDING)],
        unique=True,
        name="uniq_title_release_date",
    )

    movies.create_index([("original_language", ASCENDING), ("release_date", DESCENDING)],
                        name="lang_release_date")
    movies.create_index([("original_language", ASCENDING), ("vote_average", DESCENDING)],
                        name="lang_vote_average")

    movies.create_index([("year", ASCENDING), ("release_date", DESCENDING)],
                        name="year_release_date")
    movies.create_index([("year", ASCENDING), ("vote_average", DESCENDING)],
                        name="year_vote_average")

    movies.create_index([("release_date", DESCENDING)], name="release_date")
    movies.create_index([("vote_average", DESCENDING)], name="vote_average")

    jobs_collection().create_index([("job_id", ASCENDING)], unique=True, name="uniq_job_id")