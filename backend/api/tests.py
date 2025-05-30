from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from recipes.models import Ingredient, Recipe, RecipeIngredient

User = get_user_model()


class RecipesAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ingredient = Ingredient.objects.create(
            name='Тестовый ингредиент',
            measurement_unit='г'
        )

    def test_ingredients_list_exists(self):
        response = self.client.get(reverse('ingredients-list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_recipes_list_exists(self):
        response = self.client.get(reverse('recipes-list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_recipe_creation_unauthenticated(self):
        data = {
            'name': 'Тестовый рецепт',
            'text': 'Тестовое описание',
            'cooking_time': 30,
            'ingredients': [{'id': self.ingredient.id, 'amount': 100}]
        }
        response = self.client.post(
            reverse('recipes-list'),
            data=data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_recipe_detail_view(self):
        recipe = Recipe.objects.create(
            author=self.user,
            name='Тестовый рецепт',
            text='Тестовое описание',
            cooking_time=30
        )
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredients=self.ingredient,
            amount=100
        )
        response = self.client.get(
            reverse('recipes-detail', kwargs={'pk': recipe.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data['name'], 'Тестовый рецепт')