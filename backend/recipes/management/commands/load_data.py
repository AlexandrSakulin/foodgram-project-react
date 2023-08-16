import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load data from JSON file into database'

    def handle(self, *args, **options):
        with open(
            'data/ingredients.json',
            'r',
            encoding='utf-8'
        ) as file:
            data = json.load(file)
        for note in data:
            try:
                Ingredient.objects.get_or_create(**note)
                print(f'{note["name"]} в базе')
            except Exception as error:
                print(f'Ошибка при добавлении {note["name"]}.\n'
                      f'Текст - {error}')

        print('Загрузка ингредиентов завершена')
