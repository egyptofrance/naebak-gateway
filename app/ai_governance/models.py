"""
AI Governance Models

These models track and control AI usage within the microservice
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class AIModel(models.Model):
    """Represents an AI model that can be used by the service"""
    
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=50)  # openai, anthropic, etc.
    model_type = models.CharField(max_length=50)  # text, image, audio
    max_tokens = models.IntegerField(default=4000)
    cost_per_token = models.DecimalField(max_digits=10, decimal_places=8, default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_models'
        ordering = ['name']

    def __str__(self):
        return f"{self.provider}/{self.name}"


class AIRequest(models.Model):
    """Tracks all AI requests made through the service"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    
    # Request details
    prompt = models.TextField()
    prompt_tokens = models.IntegerField(default=0)
    max_tokens = models.IntegerField(default=1000)
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)]
    )
    
    # Response details
    response = models.TextField(blank=True)
    response_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Governance tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    blocked_reason = models.TextField(blank=True)
    quality_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    bias_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    
    # Cost tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)

    class Meta:
        db_table = 'ai_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ai_model', 'status']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"AI Request {self.id} - {self.status}"


class AIUsageQuota(models.Model):
    """Defines usage quotas for users or groups"""
    
    QUOTA_TYPE_CHOICES = [
        ('user', 'Per User'),
        ('session', 'Per Session'),
        ('global', 'Global'),
    ]
    
    PERIOD_CHOICES = [
        ('minute', 'Per Minute'),
        ('hour', 'Per Hour'),
        ('day', 'Per Day'),
        ('month', 'Per Month'),
    ]

    quota_type = models.CharField(max_length=20, choices=QUOTA_TYPE_CHOICES)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    max_requests = models.IntegerField()
    max_tokens = models.IntegerField()
    max_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # Optional specific targeting
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_usage_quotas'
        unique_together = ['quota_type', 'period', 'user', 'ai_model']

    def __str__(self):
        return f"{self.quota_type} quota: {self.max_requests} requests/{self.period}"


class AIContentFilter(models.Model):
    """Defines content filtering rules"""
    
    FILTER_TYPE_CHOICES = [
        ('profanity', 'Profanity Filter'),
        ('bias', 'Bias Detection'),
        ('factcheck', 'Fact Checking'),
        ('safety', 'Safety Filter'),
        ('custom', 'Custom Filter'),
    ]

    name = models.CharField(max_length=100)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPE_CHOICES)
    description = models.TextField()
    
    # Filter configuration
    keywords = models.JSONField(default=list, blank=True)  # List of keywords to filter
    patterns = models.JSONField(default=list, blank=True)  # Regex patterns
    threshold = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Actions
    block_request = models.BooleanField(default=False)
    flag_for_review = models.BooleanField(default=True)
    modify_response = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_content_filters'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.filter_type})"


class AIAuditLog(models.Model):
    """Comprehensive audit log for AI governance actions"""
    
    ACTION_CHOICES = [
        ('request_created', 'Request Created'),
        ('request_blocked', 'Request Blocked'),
        ('content_filtered', 'Content Filtered'),
        ('quota_exceeded', 'Quota Exceeded'),
        ('model_switched', 'Model Switched'),
        ('response_modified', 'Response Modified'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ai_request = models.ForeignKey(AIRequest, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    # Context information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Audit: {self.action} at {self.created_at}"
