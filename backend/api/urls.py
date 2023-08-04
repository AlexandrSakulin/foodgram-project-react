from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (TagViewSet, RecipeViewSet,
                    IngredientViewSet, FoodgramUserViewSet)

app_name = 'api'

router = DefaultRouter()

router.register('users', FoodgramUserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls.base')),
    path('auth/', include('djoser.urls.authtoken')),
]
