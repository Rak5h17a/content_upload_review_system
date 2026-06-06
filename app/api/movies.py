from flask import Blueprint, jsonify, request

from app.services.movie_service import MovieService

movies_bp = Blueprint("movies", __name__, url_prefix="/api/v1/movies")


@movies_bp.get("")
def list_movies():
    """List movies.

    Query params:
      page      (int, default 1)
      limit     (int, default 20, max 100)
      language  (str)  -> filters on original_language, e.g. 'en'
      year      (int)  -> year of release
      sort      (str)  -> 'release_date' (default) or 'ratings'
      order     (str)  -> 'asc' or 'desc' (default)
    """
    service = MovieService()
    result = service.list_movies(request.args)
    return jsonify(result), 200