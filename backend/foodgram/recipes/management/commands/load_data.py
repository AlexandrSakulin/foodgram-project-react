import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load data from JSON file into database'

    def add_arguments(self, parser):
        parser.add_argument(
            'file', type=str, help='JSON file to load data from'
        )

    def handle(self, *args, **options):

        file_name = options['file']

        with open(file_name, encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            ingredient = Ingredient(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            ingredient.save()

        self.stdout.write(self.style.SUCCESS('Data loaded successfully.'))
