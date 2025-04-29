import time
from prometheus_client import Counter, Histogram, Gauge
from django.conf import settings

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

database_queries_total = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['operation']
)

class MonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timer
        start_time = time.time()

        # Get response
        response = self.get_response(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.path
        ).observe(duration)

        # Update active users if authenticated
        if request.user.is_authenticated:
            active_users.inc()

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # This method is called before the view is executed
        if hasattr(view_func, '__name__'):
            view_name = view_func.__name__
        else:
            view_name = view_func.__class__.__name__

        # You can add additional metrics here
        return None

    def process_exception(self, request, exception):
        # Record exception metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.path,
            status=500
        ).inc()
        return None 