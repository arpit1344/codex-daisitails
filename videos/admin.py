from django.contrib import admin
from django import forms
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from .models import Category, Video, Tag, VideoImport
from .importer import validate_source
admin.site.site_header = 'Video Library Administration'
admin.site.site_title = 'Video Library Admin'
admin.site.index_title = 'Manage your content'
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    filter_horizontal = ['tags']
    def get_urls(self):
        return [path('<int:pk>/preview/', self.admin_site.admin_view(self.preview), name='videos_video_preview')] + super().get_urls()

    def preview(self, request, pk):
        video = get_object_or_404(Video, pk=pk)
        if not self.has_view_permission(request, video):
            raise PermissionDenied
        response = render(request, 'videos/detail.html', {'video': video, 'noindex': True})
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response

    @admin.display(description='Preview')
    def draft_preview(self, obj):
        if obj and obj.pk:
            return format_html('<a href="{}">Preview video</a>', reverse('admin:videos_video_preview', args=[obj.pk]))
        return 'Save the draft to preview it.'
    list_display = ['title', 'category', 'language', 'duration', 'is_published', 'is_featured', 'quality', 'editor_rating', 'views', 'created_at']
    list_filter = ['is_published', 'is_featured', 'category', 'language', 'quality']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published', 'is_featured']
    readonly_fields = ['created_at', 'views', 'duration_seconds', 'draft_preview']
    fieldsets = [
        (None, {'fields': ('title', 'slug', 'description', 'category', 'language', 'tags')}),
        ('Media', {'fields': ('file', 'thumbnail', 'duration', 'duration_seconds', 'quality')}),
        ('Search and sharing', {'fields': ('seo_title', 'seo_description'), 'description': 'Optional text for Google, WhatsApp and social previews.'}),
        ('Publishing', {'fields': ('draft_preview', 'is_published', 'is_featured', 'editor_rating', 'views', 'created_at')}),
    ]
    actions = ['publish', 'unpublish']
    @admin.action(description='Publish selected videos')
    def publish(self, request, queryset):
        queryset.update(is_published=True)
    @admin.action(description='Unpublish selected videos')
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']


class ImportForm(forms.ModelForm):
    class Meta:
        model = VideoImport
        fields = '__all__'

    def clean_source_url(self):
        url = self.cleaned_data['source_url']
        validate_source(url)
        return url

    def clean_rights_confirmed(self):
        if not self.cleaned_data['rights_confirmed']:
            raise forms.ValidationError('Confirm that you own or license this non-explicit video.')
        return True


@admin.register(VideoImport)
class VideoImportAdmin(admin.ModelAdmin):
    form = ImportForm
    list_display = ['title', 'status', 'review_draft', 'created_at']
    list_filter = ['status']
    filter_horizontal = ['tags']
    readonly_fields = ['status', 'error', 'video', 'review_draft', 'created_at', 'started_at', 'finished_at']
    actions = ['retry_failed']

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if obj:
            fields += ['source_url', 'title', 'description', 'category', 'tags', 'thumbnail', 'rights_confirmed']
        return fields

    @admin.display(description='Review and edit')
    def review_draft(self, obj):
        if obj and obj.video_id:
            return format_html('<a href="{}">Edit draft, preview and publish</a>', reverse('admin:videos_video_change', args=[obj.video_id]))
        return 'Available when import finishes'

    @admin.action(description='Retry failed imports')
    def retry_failed(self, request, queryset):
        count = queryset.filter(status='failed', video__isnull=True).update(status='queued', error='', started_at=None, finished_at=None)
        self.message_user(request, f'{count} import(s) queued for retry.')
