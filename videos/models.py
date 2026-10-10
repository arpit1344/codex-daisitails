from django.core.validators import FileExtensionValidator, MaxValueValidator
from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name

class Video(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    file = models.FileField(upload_to='videos/%Y/%m/', validators=[FileExtensionValidator(['mp4', 'webm', 'ogv'])], help_text='Upload MP4, WebM or OGV. MP4 with H.264/AAC is recommended.')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/', blank=True)
    duration = models.CharField(max_length=12, blank=True, help_text='Display duration, e.g. 12:30')
    quality = models.CharField(max_length=8, choices=[('', 'Not specified'), ('HD', 'HD'), ('2K', '2K'), ('4K', '4K')], blank=True)
    editor_rating = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)], help_text='Editorial score from 0 to 100, not a user vote.')
    views = models.PositiveBigIntegerField(default=0, editable=False)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at', '-pk']
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse('video_detail', args=[self.slug])
