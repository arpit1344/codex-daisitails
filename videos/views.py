import json

from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Category, Video

def home(request):
    return redirect('video_list')

def video_list(request):
    videos = Video.objects.filter(is_published=True).select_related('category')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    language = request.GET.get('language', '')
    duration = request.GET.get('duration', '')
    sort = request.GET.get('sort', 'latest')
    if query:
        videos = videos.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(tags__name__icontains=query)).distinct()
    if category:
        videos = videos.filter(category__slug=category)
    valid_languages = {value for value, _ in Video.LANGUAGE_CHOICES}
    if language in valid_languages:
        videos = videos.filter(language=language)
    else:
        language = ''
    if duration == 'short':
        videos = videos.filter(duration_seconds__gt=0, duration_seconds__lt=5 * 60)
    elif duration == 'medium':
        videos = videos.filter(duration_seconds__gte=5 * 60, duration_seconds__lte=20 * 60)
    elif duration == 'long':
        videos = videos.filter(duration_seconds__gt=20 * 60)
    else:
        duration = ''
    if sort not in {'latest', 'featured', 'top', 'views'}:
        sort = 'latest'
    if sort == 'top':
        videos = videos.order_by('-editor_rating', '-created_at', '-pk')
    elif sort == 'views':
        videos = videos.order_by('-views', '-created_at', '-pk')
    elif sort == 'featured':
        videos = videos.order_by('-is_featured', '-created_at', '-pk')
    page = Paginator(videos, 12).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    canonical_url = request.build_absolute_uri(reverse('video_list'))
    return render(request, 'videos/list.html', {'page': page, 'categories': Category.objects.annotate(published_count=Count('videos', filter=Q(videos__is_published=True))), 'languages': Video.LANGUAGE_CHOICES, 'query': query, 'selected_category': category, 'selected_language': language, 'selected_duration': duration, 'sort': sort, 'pagination_query': params.urlencode(), 'canonical_url': canonical_url, 'meta_description': 'Discover the latest, popular and top-rated videos on Video Tales. Search by category, language and duration.', 'noindex': bool(request.GET)})

def video_detail(request, slug):
    video = get_object_or_404(Video.objects.select_related('category'), slug=slug, is_published=True)
    if request.method == 'GET':
        Video.objects.filter(pk=video.pk).update(views=F('views') + 1)
        video.refresh_from_db(fields=['views'])
    related = Video.objects.filter(is_published=True, category=video.category).exclude(pk=video.pk)[:4]
    canonical_url = request.build_absolute_uri(video.get_absolute_url())
    image_url = request.build_absolute_uri(video.thumbnail.url) if video.thumbnail else ''
    content_url = request.build_absolute_uri(video.file.url)
    structured_data = {
        '@context': 'https://schema.org', '@type': 'VideoObject',
        'name': video.meta_title, 'description': video.meta_description,
        'uploadDate': video.created_at.isoformat(), 'contentUrl': content_url,
        'url': canonical_url, 'inLanguage': video.language,
    }
    if image_url:
        structured_data['thumbnailUrl'] = [image_url]
    if video.duration_seconds:
        structured_data['duration'] = f'PT{video.duration_seconds}S'
    structured_json = json.dumps(structured_data, ensure_ascii=False).replace('<', '\\u003c')
    return render(request, 'videos/detail.html', {'video': video, 'related': related, 'canonical_url': canonical_url, 'meta_description': video.meta_description, 'social_image': image_url, 'structured_data': structured_json})
