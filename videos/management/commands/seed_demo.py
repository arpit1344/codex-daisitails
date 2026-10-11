"""Create six clearly labelled demo entries with original artwork and a playable clip."""
import io
from pathlib import Path
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw
from videos.models import Category, Video

class Command(BaseCommand):
    help = 'Create general-purpose demo videos; skips existing demo slugs.'

    def handle(self, *args, **options):
        scenes = [
            ('A quiet morning in the mountains', 'Travel', (48, 99, 131), (244, 189, 125)),
            ('Small ideas, beautiful spaces', 'Lifestyle', (105, 123, 98), (229, 225, 186)),
            ('Create something new today', 'Creative', (123, 81, 117), (246, 197, 163)),
            ('The art of slowing down', 'Wellness', (61, 111, 106), (167, 212, 191)),
            ('A little adventure goes a long way', 'Travel', (60, 88, 133), (183, 204, 239)),
            ('Make time for what you love', 'Lifestyle', (168, 94, 64), (251, 210, 153)),
        ]
        clip_bytes = (Path(__file__).resolve().parents[2] / 'demo_assets' / 'preview.mp4').read_bytes()
        for index, (title, name, lower, upper) in enumerate(scenes):
            slug = f'demo-video-{index+1}'
            if Video.objects.filter(slug=slug).exists():
                continue
            category, _ = Category.objects.get_or_create(slug=name.lower(), defaults={'name': name})
            image = Image.new('RGB', (960, 540))
            draw = ImageDraw.Draw(image)
            for y in range(540):
                ratio = y/539
                color = tuple(int(upper[c]*(1-ratio)+lower[c]*ratio) for c in range(3))
                draw.line((0,y,960,y),fill=color)
            draw.ellipse((650,65,785,200),fill=upper)
            draw.polygon([(0,390),(230,180),(460,420),(650,270),(960,440),(960,540),(0,540)], fill=lower)
            foreground=tuple(max(0,c-24) for c in lower)
            draw.polygon([(0,490),(320,350),(640,480),(810,330),(960,460),(960,540),(0,540)],fill=foreground)
            draw.rounded_rectangle((32,30,156,67),radius=10,fill='white')
            draw.text((48,42),'DEMO VIDEO',fill=lower)
            out=io.BytesIO()
            image.save(out,format='JPEG',quality=90)
            video=Video(title=title,slug=slug,category=category,language='Hindi' if index % 2 == 0 else 'English',description='Demo entry with original illustrated artwork and a three-second test-pattern clip. Replace it with your own video and thumbnail in the admin panel.',duration='0:03',quality='HD',editor_rating=90-index*3,is_published=True,is_featured=index<2)
            video.file.save(f'{slug}.mp4',ContentFile(clip_bytes),save=False)
            video.thumbnail.save(f'{slug}.jpg',ContentFile(out.getvalue()),save=False)
            video.save()
        self.stdout.write(self.style.SUCCESS('Demo collection ready. Existing entries were preserved.'))
