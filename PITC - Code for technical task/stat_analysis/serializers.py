"""stat_analysis.serializers.py

This module implements serializers for statistical analysis models.
"""

from rest_framework import serializers
from .models import Report, JobReportResult


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""

    period = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "description",
            "quarter_from",
            "year_from",
            "quarter_to",
            "year_to",
            "created_at",
            "created_by",
            "period",
        ]
        read_only_fields = ["created_at", "created_by"]

    def get_period(self, obj: Report) -> str:
        """Get a formatted string representation of the report period."""
        return f"{obj.quarter_from}/{obj.year_from} - {obj.quarter_to}/{obj.year_to}"


class JobReportResultSerializer(serializers.ModelSerializer):
    """Serializer for JobReportResult model with detailed statistics."""

    report_period = serializers.SerializerMethodField()
    campaign_stats = serializers.SerializerMethodField()
    customer_stats = serializers.SerializerMethodField()

    class Meta:
        model = JobReportResult
        fields = [
            "id",
            "report",
            "report_period",
            "total_jobs",
            "completed_jobs",
            "failed_jobs",
            "avg_completion_time",
            "median_completion_time",
            "min_completion_time",
            "max_completion_time",
            "success_rate",
            "campaign_stats",
            "customer_stats",
        ]
        read_only_fields = ["report", "report_period"]

    def get_report_period(self, obj: JobReportResult) -> str:
        """Get a formatted string representation of the report period."""
        report = obj.report
        return f"{report.quarter_from}/{report.year_from} - {report.quarter_to}/{report.year_to}"

    def get_campaign_stats(self, obj: JobReportResult) -> dict:
        """Format campaign distribution data."""
        stats = obj.campaign_distribution

        # Sort campaigns by job count
        sorted_campaigns = sorted(stats.items(), key=lambda x: x[1], reverse=True)

        return {
            "distribution": {campaign: count for campaign, count in sorted_campaigns},
            "top_campaigns": [
                {
                    "name": campaign,
                    "jobs": count,
                    "percentage": (
                        (count / obj.total_jobs * 100) if obj.total_jobs > 0 else 0
                    ),
                }
                for campaign, count in sorted_campaigns[:5]  # Top 5 campaigns
            ],
        }

    def get_customer_stats(self, obj: JobReportResult) -> dict:
        """Format customer distribution data."""
        stats = obj.customer_distribution

        # Sort customers by job count
        sorted_customers = sorted(stats.items(), key=lambda x: x[1], reverse=True)

        return {
            "distribution": {customer: count for customer, count in sorted_customers},
            "top_customers": [
                {
                    "name": customer,
                    "jobs": count,
                    "percentage": (
                        (count / obj.total_jobs * 100) if obj.total_jobs > 0 else 0
                    ),
                }
                for customer, count in sorted_customers[:5]  # Top 5 customers
            ],
        }
