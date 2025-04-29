"""execution.serializers.py

This module implements serializers for the workflow management models.
"""

from rest_framework import serializers
from .models import Campaign, Customer, Order, Job


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model."""

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "priority",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "active", "created_at"]
        read_only_fields = ["created_at"]


class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job model with related data."""

    customer_name = serializers.CharField(source="order.customer.name", read_only=True)
    campaign_name = serializers.CharField(source="order.campaign.name", read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "job_id",
            "job_name",
            "order",
            "customer_name",
            "campaign_name",
            "state",
            "job_type",
            "starting_date",
            "end_date",
            "completion_time",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "job_id",
            "created_at",
            "updated_at",
            "customer_name",
            "campaign_name",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with related data."""

    customer_name = serializers.CharField(source="customer.name", read_only=True)
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    jobs = JobSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_name",
            "campaign",
            "campaign_name",
            "status",
            "scheduled_for",
            "created_at",
            "updated_at",
            "jobs",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "customer_name",
            "campaign_name",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new orders."""

    class Meta:
        model = Order
        fields = ["customer", "campaign", "scheduled_for"]

    def validate(self, attrs):
        """Validate the order data."""
        # Ensure customer is active
        customer = attrs["customer"]
        if not customer.active:
            raise serializers.ValidationError({"customer": "Customer is not active"})

        # Ensure campaign is active
        campaign = attrs["campaign"]
        if not campaign.active:
            raise serializers.ValidationError({"campaign": "Campaign is not active"})

        return attrs
