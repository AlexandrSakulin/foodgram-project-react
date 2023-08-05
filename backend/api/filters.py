from django_filters import rest_framework as filter
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(filter.FilterSet):
    """Кастомный фильтр."""

    tags = filter.AllValuesMultipleFilter(
        field_name='tags__slug',
    )

    is_favorited = filter.BooleanFilter(field_name='get_is_favorited')
    is_in_shopping_cart = filter.BooleanFilter(
        field_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_favorite(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
