from django_filters import rest_framework as filters
from django_filters.rest_framework import FilterSet
from rest_framework.filters import SearchFilter

from recipes.models import Recipe
from users.models import User


class IngredientsSearchFilter(SearchFilter):
    search_param = "name"

    def filter_queryset(self, request, queryset, view):
        if view.action == "retrieve":
            return queryset
        return super().filter_queryset(request, queryset, view)


class RecipeFilterSet(FilterSet):
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("author", "is_favorited", "is_in_shopping_cart")

    def _filter_by_user_relation(self, queryset, relation_field, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                **{f"{relation_field}__user": self.request.user})
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_by_user_relation(queryset, "favorite", value)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_by_user_relation(queryset, "shopping_cart", value)
