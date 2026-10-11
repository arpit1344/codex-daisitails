from django.db import migrations, models


def fill_duration_seconds(apps, schema_editor):
    Video = apps.get_model('videos', 'Video')
    for video in Video.objects.only('pk', 'duration').iterator():
        parts = video.duration.split(':') if video.duration else []
        try:
            values = [int(part) for part in parts]
            seconds = values[0] * 60 + values[1] if len(values) == 2 else values[0] * 3600 + values[1] * 60 + values[2] if len(values) == 3 else 0
        except (ValueError, IndexError):
            seconds = 0
        Video.objects.filter(pk=video.pk).update(duration_seconds=seconds)


class Migration(migrations.Migration):
    dependencies = [('videos', '0002_video_editor_rating_video_quality_video_views')]
    operations = [
        migrations.AddField(
            model_name='video',
            name='duration_seconds',
            field=models.PositiveIntegerField(default=0, help_text='Used for duration filters. It is filled automatically from the display duration.'),
        ),
        migrations.AddField(
            model_name='video',
            name='language',
            field=models.CharField(choices=[('Hindi', 'Hindi'), ('English', 'English'), ('Bengali', 'Bengali'), ('Punjabi', 'Punjabi'), ('Tamil', 'Tamil'), ('Telugu', 'Telugu'), ('Other', 'Other')], db_index=True, default='Hindi', max_length=20),
        ),
        migrations.RunPython(fill_duration_seconds, migrations.RunPython.noop),
    ]
