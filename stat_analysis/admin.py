from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Report, JobStatistics, OrderStatistics, UserStatistics


class JobStatisticsInline(admin.TabularInline):
    model = JobStatistics
    extra = 0
    readonly_fields = (
        'service_provider',
        'job_type',
        'total_jobs',
        'completed_jobs',
        'failed_jobs',
        'average_completion_time'
    )


class OrderStatisticsInline(admin.TabularInline):
    model = OrderStatistics
    extra = 0
    readonly_fields = (
        'service_provider',
        'total_orders',
        'total_revenue',
        'average_order_value',
        'completion_rate'
    )


class UserStatisticsInline(admin.TabularInline):
    model = UserStatistics
    extra = 0
    readonly_fields = (
        'account_manager',
        'total_customers',
        'total_orders',
        'total_revenue',
        'average_customer_value'
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'start_date',
        'end_date',
        'created_by',
        'get_pdf_link',
        'created_at'
    )
    search_fields = ('title', 'description', 'created_by__email')
    list_filter = ('created_at', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [
        JobStatisticsInline,
        OrderStatisticsInline,
        UserStatisticsInline
    ]
    
    def get_pdf_link(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank">View PDF</a>',
                obj.pdf_file.url
            )
        return '-'
    get_pdf_link.short_description = 'PDF Report'


@admin.register(JobStatistics)
class JobStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        'report',
        'service_provider',
        'job_type',
        'total_jobs',
        'completed_jobs',
        'failed_jobs',
        'get_completion_time'
    )
    search_fields = (
        'report__title',
        'service_provider__name',
        'job_type'
    )
    list_filter = ('job_type', 'service_provider', 'report')
    
    def get_completion_time(self, obj):
        if obj.average_completion_time:
            return format_html(
                '<span style="color: green;">{}</span>',
                str(obj.average_completion_time)
            )
        return '-'
    get_completion_time.short_description = 'Avg. Completion Time'


@admin.register(OrderStatistics)
class OrderStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        'report',
        'service_provider',
        'total_orders',
        'total_revenue',
        'average_order_value',
        'completion_rate'
    )
    search_fields = ('report__title', 'service_provider__name')
    list_filter = ('service_provider', 'report')


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        'report',
        'account_manager',
        'total_customers',
        'total_orders',
        'total_revenue',
        'average_customer_value'
    )
    search_fields = (
        'report__title',
        'account_manager__user__email',
        'account_manager__user__first_name',
        'account_manager__user__last_name'
    )
    list_filter = ('account_manager', 'report')
