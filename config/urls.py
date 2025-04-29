"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from rest_framework import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from execution.views import (
    CustomerViewSet, 
    OrderViewSet, 
    JobViewSet,
    ServiceProviderViewSet,
    ServiceViewSet,
    UserRegistrationView
)
from stat_analysis.views import ReportViewSet, AnalyticsViewSet

# Create a router and register our viewsets
router = routers.DefaultRouter()
router.register(r'service-providers', ServiceProviderViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

# Create the API documentation schema
schema_view = get_schema_view(
    openapi.Info(
        title="Customer Order Workflow API",
        default_version='v1',
        description="API for managing customer orders and analyzing workflow statistics",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Redirect root URL to API docs
    path('', RedirectView.as_view(url='/swagger/', permanent=True), name='index'),
    
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
