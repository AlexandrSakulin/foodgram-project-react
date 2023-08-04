from datetime import datetime

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer, UserCreateSerializer
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag)
from users.models import User
from .filters import IngredientFilter, RecipeFilter
from .pagination import StandartPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeReadSerializer,
                          RecipeShortSerializer, ShoppingCartSerializer,
                          SubscribeSerializer, SubscriptionSerializer,
                          TagSerializer, UserReadSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    """Кастомный вьюсет рецептов модели Recipe."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filterset_class = RecipeFilter
    pagination_class = StandartPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        if self.action in ('shopping_cart', 'favorite'):
            return RecipeShortSerializer
        return RecipeCreateUpdateSerializer

    @staticmethod
    def create_relation(request, pk, model, serializer):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response({
                'errors': 'Данный объект уже существует.'
            }, status.HTTP_400_BAD_REQUEST)
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
        model.objects.filter(user=request.user, recipe=get_object_or_404(
            Recipe, pk=pk)).delete()
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
            recipe__shoppingcart__user=user).values(
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
            ShoppingCart,
            ShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    def undo_shopping_cart(self, request, pk):
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
            Favorite,
            FavoriteSerializer
        )

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
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
    filter_backends = (IngredientFilter, )
    search_fields = ('^name',)
    permission_classes = [AllowAny, ]


class FoodgramUserViewSet(UserViewSet):
    """Кастомный ViewSet модели User."""
    queryset = User.objects.all()
    permission_classes = [AllowAny, ]
    filter_backends = [DjangoFilterBackend]
    pagination_class = StandartPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'me'):
            return UserReadSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action in ('subscriptions', 'subscribe'):
            return SubscriptionSerializer
        return UserCreateSerializer  # есть аналогичный из djoser

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
        serializer = self.get_serializer(page, many=True)
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
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user
        Subscribe.objects.get_object_or_404(
            user=user, author=author
        ).delete()
        message = {
            'detail': f'Вы отписались от пользователя {author}'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)
