from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')  # Поля в списке
    search_fields = ('name',)  # Поиск по названию
    list_filter = ('measurement_unit',)  # Фильтр по единицам измерения


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorite_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author',)
    readonly_fields = ('get_favorite_count',)

    def get_favorite_count(self, obj):
        return obj.favorite.count()
    get_favorite_count.short_description = 'В избранном'

    fieldsets = (
        (None, {
            'fields': ('author', 'name', 'image', 'text', 'cooking_time')
        }),
        ('Дополнительно', {
            'fields': ('get_favorite_count',),
            'classes': ('collapse',),
        }),
    )

    inlines = [RecipeIngredientInline]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        recipe = Recipe.objects.get(pk=object_id)
        extra_context['favorite_count'] = self.get_favorite_count(recipe)
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients', 'amount')
    search_fields = ('recipe__name', 'ingredients__name')
    list_filter = ('recipe', 'ingredients')
