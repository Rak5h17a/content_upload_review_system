from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, message, status_code=400, code="BAD_REQUEST"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _error_body(code, message):
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return _error_body(err.code, err.message), err.status_code

    @app.errorhandler(404)
    def handle_404(err):
        return _error_body("NOT_FOUND", "Resource not found"), 404

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return _error_body(err.name.upper().replace(" ", "_"), err.description), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Unhandled error")
        return _error_body("INTERNAL_ERROR", "Something went wrong"), 500