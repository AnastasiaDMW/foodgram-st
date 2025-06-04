from django.core.validators import MinValueValidator
from django.db import models
import secrets
from backend.settings import (
    MIN_COOKING_TIME,
    MIN_AMOUNT_COUNT,
    MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_RECIPE_NAME,
    MAX_LENGTH_SHORT_LINK_KEY
)
from users.models import User

class Ingredient(models.Model):
    
    name = models.CharField(max_length=MAX_LENGTH_INGREDIENT_NAME, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=64, verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            ),
        ]

    def __str__(self):
        return self.name

class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipe',
    )
    name = models.CharField(max_length=MAX_LENGTH_RECIPE_NAME, verbose_name='Название')
    image = models.ImageField(upload_to='recipes/images', verbose_name='Картинка')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
        ],
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes_ingredient',
        verbose_name='Рецепт',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(MIN_AMOUNT_COUNT),
        ),
    )

    class Meta:
        verbose_name = 'Рецепт и ингредиент'
        verbose_name_plural = 'Рецепты и ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredients'),
                name='unique_recipe_ingredient'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipes',
            ),
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            ),
        ]

class ShortLink(models.Model):
    key = models.CharField(max_length=MAX_LENGTH_SHORT_LINK_KEY, unique=True)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='short_link',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_for_url(cls, url):
        key = secrets.token_urlsafe(MAX_LENGTH_SHORT_LINK_KEY)[:MAX_LENGTH_SHORT_LINK_KEY]
        return cls.objects.create(key=key, original_url=url)
