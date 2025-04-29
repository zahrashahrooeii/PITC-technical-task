import time
import logging
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger('execution')

class RequestLoggingMiddleware:
    """Middleware to log all requests and responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start time of request
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}"
        )

        # Process request
        response = self.get_response(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.path} completed in {duration:.2f}s "
            f"with status {response.status_code}"
        )

        return response


class RateLimitMiddleware:
    """Middleware to implement rate limiting."""

    def __init__(self, get_response):
        self.get_response = get_response
        # Rate limits: requests per minute
        self.rate_limits = {
            'POST': 30,    # 30 requests per minute for POST
            'PUT': 30,     # 30 requests per minute for PUT
            'DELETE': 20,  # 20 requests per minute for DELETE
            'GET': 60      # 60 requests per minute for GET
        }

    def __call__(self, request):
        # Skip rate limiting in debug mode
        if settings.DEBUG:
            return self.get_response(request)

        client_ip = request.META.get('REMOTE_ADDR')
        method = request.method

        if method in self.rate_limits:
            try:
                cache_key = f"rate_limit_{client_ip}_{method}"
                requests = cache.get(cache_key, 0)

                if requests >= self.rate_limits[method]:
                    logger.warning(f"Rate limit exceeded for {client_ip} - {method}")
                    return HttpResponse(
                        "Rate limit exceeded. Please try again later.",
                        status=429  # HTTP 429 Too Many Requests
                    )

                # Increment the request count
                cache.set(cache_key, requests + 1, 60)  # Expire after 1 minute
            except Exception as e:
                logger.warning(f"Rate limiting failed: {str(e)}")
                # Continue processing the request even if rate limiting fails
                pass

        return self.get_response(request) 