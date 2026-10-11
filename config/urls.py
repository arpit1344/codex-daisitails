from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve
from django.http import HttpResponse, JsonResponse
from videos.sitemaps import StaticSitemap, VideoSitemap

sitemaps = {'pages': StaticSitemap, 'videos': VideoSitemap}

def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    return HttpResponse(f'User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {sitemap_url}\n', content_type='text/plain')

urlpatterns = [path('health/', lambda request: JsonResponse({'status': 'ok'})), path('robots.txt', robots_txt, name='robots_txt'), path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'), path('admin/', admin.site.urls), path('', include('videos.urls'))]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Ephemeral preview only: use object storage or a dedicated media server in production.
if not settings.DEBUG and settings.PREVIEW_MODE:
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
