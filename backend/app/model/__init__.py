"""Model interfaces and availability errors."""


class ModelNotReadyError(RuntimeError):
    """Raised when an inference model has not been configured."""
