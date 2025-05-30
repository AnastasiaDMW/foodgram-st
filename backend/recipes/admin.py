from django.contrib import admin
from .models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeIngredient
)


admin.site.register(Ingredient) 
admin.site.register(Recipe) 
admin.site.register(Favorite) 
admin.site.register(ShoppingCart) 
admin.site.register(RecipeIngredient)
