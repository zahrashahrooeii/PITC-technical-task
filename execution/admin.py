from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ServiceProvider,
    AccountManager,
    Customer,
    Service,
    Order,
    OrderService,
    Job
)


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'created_at')
    search_fields = ('name', 'contact_email', 'contact_phone')
    list_filter = ('created_at',)


@admin.register(AccountManager)
class AccountManagerAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_service_providers', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    filter_horizontal = ('service_providers',)
    
    def get_service_providers(self, obj):
        return ", ".join([sp.name for sp in obj.service_providers.all()])
    get_service_providers.short_description = 'Service Providers'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'account_manager', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('account_manager', 'created_at')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_provider', 'price', 'is_active', 'created_at')
    search_fields = ('name', 'service_provider__name')
    list_filter = ('service_provider', 'is_active', 'created_at')


class OrderServiceInline(admin.TabularInline):
    model = OrderService
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'total_amount', 'status', 'created_at')
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name')
    list_filter = ('status', 'created_at')
    inlines = [OrderServiceInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter orders based on account manager's customers
        return qs.filter(
            customer__account_manager__user=request.user
        )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'job_type',
        'service_provider',
        'status',
        'get_completion_time',
        'created_at'
    )
    search_fields = ('job_type', 'service_provider__name')
    list_filter = ('job_type', 'status', 'service_provider', 'created_at')
    
    def get_completion_time(self, obj):
        if obj.status == 'COMPLETED' and obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return format_html(
                '<span style="color: green;">{}</span>',
                str(duration)
            )
        return '-'
    get_completion_time.short_description = 'Completion Time'
