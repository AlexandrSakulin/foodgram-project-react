import os
from csv import reader

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Tag

DATA_PATH = os.path.join(settings.BASE_DIR, 'data')
TAGS_DATA = os.path.join(DATA_PATH, 'tags.csv')


class Command(BaseCommand):
    """Импорт тегов из .csv."""

    def handle(self, *args, **kwargs):
        with open(TAGS_DATA, 'r', encoding='UTF-8') as tags:
            for row in reader(tags):
                if len(row) == 3:
                    name, color, slug = row
                    Tag.objects.get_or_create(
                        name=name,
                        color=color,
                        slug=slug
                    )
