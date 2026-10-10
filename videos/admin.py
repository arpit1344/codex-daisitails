from django.contrib import admin
from .models import Category, Video
admin.site.site_header = 'Video Library Administration'
admin.site.site_title = 'Video Library Admin'
admin.site.index_title = 'Manage your content'
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'is_featured', 'quality', 'editor_rating', 'views', 'created_at']
    list_filter = ['is_published', 'is_featured', 'category']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published', 'is_featured']
    readonly_fields = ['created_at', 'views']
    actions = ['publish', 'unpublish']
    @admin.action(description='Publish selected videos')
    def publish(self, request, queryset):
        queryset.update(is_published=True)
    @admin.action(description='Unpublish selected videos')
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
