import json

from django.core.management.base import BaseCommand
from django.db import connection

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load data from JSON file into database'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='JSON file to load data from')

    def handle(self, *args, **options):

        # очищаем данные
        # Ingredient.objects.all().delete()
        # with connection.cursor() as cursor:
        #     cursor.execute('DELETE FROM "recipes_ingredient"')
        #     cursor.execute(
        #         "UPDATE sqlite_sequence  SET seq = 0 WHERE name = 'recipes_ingredient'")
        # Получаем имя файла из аргументов команды
        file_name = options['file']

        # Открываем файл с данными JSON
        with open(file_name, encoding='utf-8') as f:
            data = json.load(f)

        # Создаем экземпляры модели Ingredient на основе данных из файла JSON
        for item in data:
            ingredient = Ingredient(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            ingredient.save()

        # Выводим сообщение о завершении процесса загрузки
        self.stdout.write(self.style.SUCCESS('Data loaded successfully.'))
