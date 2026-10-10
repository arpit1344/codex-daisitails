from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.http import JsonResponse
urlpatterns = [path('health/', lambda request: JsonResponse({'status': 'ok'})), path('admin/', admin.site.urls), path('', include('videos.urls'))]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Ephemeral preview only: use object storage or a dedicated media server in production.
if not settings.DEBUG and settings.PREVIEW_MODE:
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
