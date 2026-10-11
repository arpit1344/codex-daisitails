import io
import re
from pathlib import Path

from PIL import Image, ImageOps
from django.core.files.base import ContentFile
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
    LANGUAGE_CHOICES = [
        ('Hindi', 'Hindi'), ('English', 'English'), ('Bengali', 'Bengali'),
        ('Punjabi', 'Punjabi'), ('Tamil', 'Tamil'), ('Telugu', 'Telugu'),
        ('Other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    description = models.TextField(blank=True)
    seo_title = models.CharField(max_length=60, blank=True, help_text='Optional search result title. Leave blank to use the video title.')
    seo_description = models.CharField(max_length=160, blank=True, help_text='Optional search result description. Leave blank to use the video description.')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    file = models.FileField(upload_to='videos/%Y/%m/', validators=[FileExtensionValidator(['mp4', 'webm', 'ogv'])], help_text='Upload MP4, WebM or OGV. MP4 with H.264/AAC is recommended.')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/', blank=True)
    duration = models.CharField(max_length=12, blank=True, help_text='Display duration, e.g. 12:30')
    duration_seconds = models.PositiveIntegerField(default=0, help_text='Used for duration filters. It is filled automatically from the display duration.')
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='Hindi', db_index=True)
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

    @property
    def meta_title(self):
        return self.seo_title or self.title

    @property
    def meta_description(self):
        text = self.seo_description or self.description or f'Watch {self.title} on Video Tales.'
        return text[:160]

    @staticmethod
    def parse_duration(value):
        if not value or not re.fullmatch(r'\d{1,3}:[0-5]\d(?::[0-5]\d)?', value.strip()):
            return 0
        parts = [int(part) for part in value.split(':')]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0] * 3600 + parts[1] * 60 + parts[2]

    def save(self, *args, **kwargs):
        self.duration_seconds = self.parse_duration(self.duration)
        if self.thumbnail and not self.thumbnail._committed:
            image = ImageOps.exif_transpose(Image.open(self.thumbnail))
            image.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            output = io.BytesIO()
            image.save(output, format='WEBP', quality=78, method=6)
            name = f'{Path(self.thumbnail.name).stem}.webp'
            self.thumbnail = ContentFile(output.getvalue(), name=name)
        super().save(*args, **kwargs)
