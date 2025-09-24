from django.apps import AppConfig


class AIGovernanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.ai_governance'
    verbose_name = 'AI Governance'

    def ready(self):
        """Initialize AI governance components when Django starts"""
        from . import signals  # noqa
