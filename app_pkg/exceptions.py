"""Custom application exceptions for structured error handling."""


class AppError(Exception):
    """Base application error."""
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


class ScheduleGenerationError(AppError):
    """Error during schedule generation."""
    status_code = 500


class ValidationError(AppError):
    """Input validation error."""
    status_code = 400


class AuthorizationError(AppError):
    """Insufficient permissions."""
    status_code = 403


class ResourceNotFoundError(AppError):
    """Requested resource not found."""
    status_code = 404
