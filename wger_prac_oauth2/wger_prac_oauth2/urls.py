"""
URL configuration for wger_prac_oauth2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from .views import GoogleLogin

urlpatterns = [
    path("admin/", admin.site.urls),

    # Must use 'accounts/' plural for allauth compatibility
    path('accounts/', include('allauth.urls')), 
    
    # API Endpoints
    path('api/v2/auth/', include('dj_rest_auth.urls')),
    path('api/v2/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # The endpoint Flutter hits
    path('api/v2/auth/google/', GoogleLogin.as_view(), name='google_login'),
]
