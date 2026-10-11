from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Video


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['video_list']

    def location(self, item):
        return reverse(item)


class VideoSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return Video.objects.filter(is_published=True).order_by('-created_at')

    def lastmod(self, item):
        return item.created_at
