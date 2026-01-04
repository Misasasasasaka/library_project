"""
URL configuration for library_project project.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # API 路由
    path("api/auth/", include("users.urls")),
    path("api/", include("books.urls")),
    path("api/", include("borrows.urls")),

    # SPA 前端路由 - 所有非 API 路由都返回 index.html
    re_path(r'^(?!api/)(?!admin/)(?!media/)(?!static/).*$', views.spa_view, name='spa'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
