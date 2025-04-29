import structlog
from functools import wraps
from django.conf import settings

logger = structlog.get_logger()

def log_view(logger=logger):
    """
    Decorator to log view execution with structured logging.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            log = logger.bind(
                view_name=view_func.__name__,
                request_method=request.method,
                request_path=request.path,
                user_id=getattr(request.user, 'id', None),
            )

            try:
                log.info("view_started")
                response = view_func(request, *args, **kwargs)
                log.info(
                    "view_completed",
                    status_code=response.status_code,
                )
                return response
            except Exception as e:
                log.error(
                    "view_error",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        return wrapped_view
    return decorator

def log_model_operation(logger=logger):
    """
    Decorator to log model operations with structured logging.
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            model_name = args[0].__class__.__name__
            operation = func.__name__

            log = logger.bind(
                model=model_name,
                operation=operation,
            )

            try:
                log.info("operation_started")
                result = func(*args, **kwargs)
                log.info("operation_completed")
                return result
            except Exception as e:
                log.error(
                    "operation_error",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        return wrapped_func
    return decorator

def log_api_call(logger=logger):
    """
    Decorator to log API calls with structured logging.
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            log = logger.bind(
                api_endpoint=func.__name__,
            )

            try:
                log.info("api_call_started")
                result = func(*args, **kwargs)
                log.info("api_call_completed")
                return result
            except Exception as e:
                log.error(
                    "api_call_error",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        return wrapped_func
    return decorator 