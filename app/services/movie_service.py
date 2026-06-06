from pymongo import ASCENDING, DESCENDING

from app.repositories.movie_repository import MovieRepository
from app.utils.errors import ApiError
from app.utils.responses import paginated

_SORT_FIELDS = {
    "release_date": "release_date",
    "rating": "vote_average",
    "ratings": "vote_average",
    "vote_average": "vote_average",
}

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class MovieService:
    def __init__(self, repository=None):
        self.repo = repository or MovieRepository()

    def list_movies(self, args):
        page = self._positive_int(args.get("page"), default=1, name="page")
        limit = self._positive_int(args.get("limit"), default=DEFAULT_LIMIT, name="limit")
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT

        sort_param = (args.get("sort") or "release_date").lower()
        if sort_param not in _SORT_FIELDS:
            raise ApiError(
                f"Invalid sort field '{sort_param}'. "
                f"Allowed: {sorted(set(_SORT_FIELDS))}"
            )
        sort_field = _SORT_FIELDS[sort_param]

        order = (args.get("order") or "desc").lower()
        if order not in ("asc", "desc"):
            raise ApiError("Invalid order. Allowed: asc, desc")
        sort_dir = ASCENDING if order == "asc" else DESCENDING

        query = self._build_filter(args)

        total = self.repo.count(query)
        skip = (page - 1) * limit
        items = self.repo.find(query, sort_field, sort_dir, skip, limit)
        return paginated(items, page, limit, total)

    def _build_filter(self, args):
        query = {}
        language = args.get("language") or args.get("original_language")
        if language:
            query["original_language"] = language.strip()

        year = args.get("year")
        if year:
            query["year"] = self._positive_int(year, default=None, name="year")
        return query

    @staticmethod
    def _positive_int(value, default, name):
        if value is None or value == "":
            return default
        try:
            parsed = int(value)
        except (ValueError, TypeError):
            raise ApiError(f"'{name}' must be an integer")
        if parsed < 1:
            raise ApiError(f"'{name}' must be >= 1")
        return parsed