import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load data from JSON file into database'

    def handle(self, *args, **options):
        try:
            with open(
                    'data/ingredients.json',
                    'r',
                    encoding='utf-8'
            ) as f:
                data = json.load(f)
                ingredients = ([Ingredient(name=d['name'],
                                measurement_unit=d['measurement_unit'])
                                for d in data])
                Ingredient.objects.bulk_create(ingredients)
                self.stdout.write(self.style.SUCCESS(
                    'Data loaded successfully.')
                )
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('File not found!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Error decoding JSON file!'))
