import json

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Load tags from JSON file into database'

    def handle(self, *args, **options):
        with open(
                'data/tags.json',
                'r',
                encoding='UTF-8'
        ) as tags:
            data = json.load(tags)
        for note in data:
            try:
                Tag.objects.get_or_create(**note)
                print(f'{note["name"]} в базе')
            except Exception as error:
                print(f'Ошибка при добавлении {note["name"]}.\n'
                      f'Текст - {error}')

        print('Загрузка тэгов завершена')
