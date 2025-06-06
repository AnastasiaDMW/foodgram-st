import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User


class Command(BaseCommand):
    help = 'Import model from a JSON file'

    def handle(self, *args, **kwargs):
        self.import_ingredients()
        if os.getenv('DATA_TEST', '') == 'True':
            self.import_recipes()

    def import_ingredients(self):
        with open('data/ingredients.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            ingredients = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                for item in data
            ]
            Ingredient.objects.bulk_create(ingredients)
            self.stdout.write(self.style.SUCCESS(
                'Successfully imported ingredients'))

    def import_recipes(self):
        with open('data/recipes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

            recipes = []
            recipe_ingredients = []

            for item in data:
                recipe = Recipe(
                    author=User.objects.get(pk=item['author']),
                    name=item['name'],
                    text=item['text'],
                    cooking_time=item['cooking_time'],
                    image=item['image']
                )
                recipes.append(recipe)

                for ing in item['ingredients']:
                    recipe_ingredients.append((
                        recipe,
                        Ingredient.objects.get(pk=ing['id']),
                        ing['amount']
                    ))

            Recipe.objects.bulk_create(recipes)

            RecipeIngredient.objects.bulk_create([
                RecipeIngredient(
                    recipe=recipe,
                    ingredients=ingredient,
                    amount=amount
                ) for recipe, ingredient, amount in recipe_ingredients
            ])

            self.stdout.write(self.style.SUCCESS(
                'Successfully imported recipes'))
