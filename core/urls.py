"""
URL configuration for core project.

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
from core.settings import URL_PREFIX

api_base_path = f'{URL_PREFIX}api/'

urlpatterns = [
    path(f'{URL_PREFIX}admin/', admin.site.urls),
    path(api_base_path, include('apps.api.urls')),
    path(f'{api_base_path}rag/', include('apps.rag_assistant.urls')),
]
