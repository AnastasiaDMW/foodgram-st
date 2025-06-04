import base64

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Recipe, Ingredient, RecipeIngredient, Favorite, ShoppingCart
)
from users.models import User, Subscription
from backend.settings import (
    REGEX_USERNAME, MIN_COOKING_TIME, MIN_AMOUNT_COUNT,
    MIN_INGREDIENTS_COUNT, DEFAULT_AVATAR
)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'image.{ext}')
        return super().to_internal_value(data)


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField() 
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT_COUNT,
        error_messages={
            'min_value': f'Количество ингредиента не может быть меньше {MIN_AMOUNT_COUNT}.'
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngridientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredients.id', queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit', read_only=True
    )
    name = serializers.CharField(source='ingredients.name', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили в избранное.',
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили в корзину.',
            )
        ]


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    username = serializers.RegexField(
        regex=REGEX_USERNAME, required=True
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=True)
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'password', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated and 
                user.subscriber.filter(author=obj).exists())


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar', instance.avatar)
        instance.avatar = avatar or DEFAULT_AVATAR
        instance.save()
        return instance


class SubscribeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name', read_only=True)
    last_name = serializers.CharField(source='author.last_name', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author.recipes.count', read_only=True
    )
    avatar = Base64ImageField(source='author.avatar', read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        subscriber = self.context['user']
        return Subscription.objects.filter(
            subscriber=subscriber, author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.author.recipes.all()
        
        if recipes_limit := request.query_params.get('recipes_limit'):
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        
        return RecipeShortInfoSerializer(
            recipes, many=True, context=self.context
        ).data


class UserSubscriptionsSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeShortInfoSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated and
                user.subscriber.filter(author=obj).exists())

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if recipes_limit := self.context['request'].query_params.get('recipes_limit'):
            try:
                limit = int(recipes_limit)
                if limit > 0:
                    data['recipes'] = data['recipes'][:limit]
                else:
                    data['error'] = 'recipes_limit должен быть положительным числом'
            except ValueError:
                data['error'] = 'Неверное значение для recipes_limit'
        return data


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngridientsSerializer(
        many=True, read_only=True, source='recipes_ingredient'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def _check_user_relation(self, obj, model):
        user = self.context['request'].user
        return (user.is_authenticated and
                model.objects.filter(user=user, recipe=obj).exists())

    def get_is_favorited(self, obj):
        return self._check_user_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self._check_user_relation(obj, ShoppingCart)


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientAmountSerializer(
        many=True, source='recipes_ingredient'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME:
            raise ValidationError(
                f'Минимальное время готовки {MIN_COOKING_TIME}.'
            )
        return value

    def validate_ingredients(self, value):
        ingredient_ids = set()
        for ingredient in value:
            if ingredient['id'] in ingredient_ids:
                raise ValidationError('Ингредиенты не должны повторяться.')
            ingredient_ids.add(ingredient['id'])
            if not Ingredient.objects.filter(pk=ingredient['id']).exists():
                raise ValidationError(
                    f'Ингредиент с id {ingredient["id"]} не найден.'
                )
        return value

    def validate_ingredient_count(self, ingredients_data):
        if len(ingredients_data) < MIN_INGREDIENTS_COUNT:
            raise ValidationError(
                f'Минимальное количество ингредиентов {MIN_INGREDIENTS_COUNT}.'
            )
        return ingredients_data

    def validate(self, data):
        ingredients_data = data.get('recipes_ingredient', [])
        self.validate_ingredient_count(ingredients_data)
        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipes_ingredient')
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients_id=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()

        if ingredients_data := validated_data.get('ingredients'):
            instance.recipes_ingredient.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredients_id=ingredient_data['id'],
                    amount=ingredient_data['amount'],
                )

        return instance

    def get_is_favorited(self, obj):
        return RecipeSerializer.get_is_favorited(self, obj)

    def get_is_in_shopping_cart(self, obj):
        return RecipeSerializer.get_is_in_shopping_cart(self, obj)

    def to_representation(self, instance):
        return RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data
