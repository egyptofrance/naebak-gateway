"""
URL configuration for Naibak Microservice Template
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Core API
    path('api/v1/', include('app.core.urls')),
    
    # AI Governance API
    path('api/v1/ai-governance/', include('app.ai_governance.urls')),
    
    # Monitoring endpoints
    path('', include('app.monitoring.urls')),
]
