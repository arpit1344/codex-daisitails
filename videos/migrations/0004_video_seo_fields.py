from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('videos', '0003_video_language_and_duration_seconds')]
    operations = [
        migrations.AddField(model_name='video', name='seo_title', field=models.CharField(blank=True, help_text='Optional search result title. Leave blank to use the video title.', max_length=60)),
        migrations.AddField(model_name='video', name='seo_description', field=models.CharField(blank=True, help_text='Optional search result description. Leave blank to use the video description.', max_length=160)),
    ]
