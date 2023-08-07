from datetime import datetime

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserReadSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    """Кастомный вьюсет рецептов модели Recipe."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    @staticmethod
    def create_relation(request, pk, serializer):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        context = {'request': request}
        serializer = serializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_relation(request, pk, model):
        get_object_or_404(
            model, user=request.user, recipe=get_object_or_404(
                Recipe, pk=pk)
        ).delete()
        message = {
            'detail':
                'Данные удалены.'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def export_file(ingredients):
        data = []
        for ingredient in ingredients:
            data.append(
                f'{ingredient["name"]}, '
                f'{ingredient["amount"]} '
                f'{ingredient["measurement_unit"]}'
            )
        content = 'Список покупок:\n\n' + '\n'.join(data)
        date = datetime.today()
        filename = f'{date}_shopping_list.txt'
        request = HttpResponse(content, content_type='text/plain')
        request['Content-Disposition'] = f'attachment; filename={filename}'
        return request

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthorOrAdminOrReadOnly]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__recipes_shoppingcart_related__user=user).values(
            name=F('ingredients__name'),
            measurement_unit=F('ingredients__measurement_unit')).order_by(
            'ingredients__name').annotate(
            amount=Sum('amount')
        )
        return RecipeViewSet.export_file(ingredients)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        """Список покупок."""
        return RecipeViewSet.create_relation(
            request,
            pk,
            ShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return RecipeViewSet.delete_relation(request, pk, ShoppingCart)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        """Функционал избранных рецептов."""
        return RecipeViewSet.create_relation(
            request,
            pk,
            FavoriteSerializer
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return RecipeViewSet.delete_relation(request, pk, Favorite)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Стандартный ридонли вьюсет тегов модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny, ]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Стандартный ридонли вьюсет ингридиентов модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = [AllowAny, ]


class FoodgramUserViewSet(UserViewSet):
    """Кастомный ViewSet модели User."""
    queryset = User.objects.all()
    permission_classes = [AllowAny, ]
    filter_backends = [DjangoFilterBackend]
    pagination_class = PageLimitPagination
    serializer_class = UserReadSerializer

    @action(
        detail=False,
        methods=['GET', ],
        permission_classes=[IsAuthorOrAdminOrReadOnly]
    )
    def subscriptions(self, request):
        """Список подписок."""
        user = request.user
        subscriptions = User.objects.filter(
            following__user=user
        )
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthorOrAdminOrReadOnly]
    )
    def subscribe(self, request, id):
        """Функционал подписок на авторов."""
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.pk,
            'author': author.pk
        }
        serializer = SubscribeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user
        get_object_or_404(Subscribe, user=user, author=author).delete()
        message = {
            'detail': f'Вы отписались от пользователя {author}'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)
