# Monitoring and Logging Configuration
LOGGING = get_logger_config()

# Sentry Configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# Only initialize Sentry if DSN is provided
if env('SENTRY_DSN'):
    sentry_sdk.init(
        dsn="https://9b12ae57b8d2a8d17eb468ca0286e1b3@o4509237831467008.ingest.de.sentry.io/4509237833760848",
        
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        
        # Enable performance monitoring
        enable_tracing=True,
        
        # Initialize the Django integration
        integrations=[
            DjangoIntegration(),
        ],
    )

# Prometheus Configuration
INSTALLED_APPS += [
    'django_prometheus',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.migrations',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
] + MIDDLEWARE + [
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Health Check Configuration
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,    # MB
}

# Monitoring Endpoints
PROMETHEUS_EXPORT_MIGRATIONS = False
PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = '0.0.0.0' 