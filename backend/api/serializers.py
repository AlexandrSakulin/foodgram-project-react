from django.db.models import F

from djoser import serializers as ds
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag)
from users.models import User


# USERS ZONE
class UserReadSerializer(ds.UserSerializer):
    """USER for READ: GET: api/users/ :: /api/users/{id}/ :: /api/users/me/."""

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta(ds.UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return (request.user.is_authenticated and user.follower.filter(
            user=request.user).exists())


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписки. POST, DEL: /api/users/{id}/subscribe/"""

    class Meta:
        model = Subscribe
        fields = ('user', 'author')

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise serializers.ValidationError(
                {
                    'error': 'Ошибка подписки. Попытка подписаться на себя.'
                }
            )
        return data


class SubscriptionSerializer(UserReadSerializer):
    """Сериализатор списка подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:(int(recipes_limit))]
        return RecipeShortSerializer(recipes, many=True).data


# TAGS ZONE
class TagSerializer(serializers.ModelSerializer):
    """Сериализато тегов. GET: api/tags/ :: api/tags/{id}/"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


# INGREDIENTS ZONE
class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты. GET: api/ingredients/ :: api/ingredients/{id}/"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте. Include in RecipeReadSerializer. OK"""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all())
    name = serializers.StringRelatedField(source='ingredient'
                                                 '.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


# RECIPES ZONE
class RecipeReadSerializer(serializers.ModelSerializer):
    """Чтение рецептов. GET: api/recipes/ :: api/recipes/{id}/"""
    tags = TagSerializer(many=True, read_only=True)
    author = UserReadSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',  # link
            'author',  # link
            'ingredients',  # method
            'is_favorited',  # method
            'is_in_shopping_cart',  # method
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):
        """Custom queryset: filter IngredientInRecipe by recipe."""
        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredients__amount')
        )
        return ingredients

    def get_is_favorited(self, recipe):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and recipe.favorite.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and recipe.shoppingcart.filter(user=request.user).exists()
        )


class IngredientInRecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте доп. Include RecipeCreateUpdateSerializer"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и обновление рецепта. POST: api/recipes/"""
    ingredients = IngredientInRecipeCreateUpdateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(max_length=None, use_url=True, required=False)
    author = UserReadSerializer(read_only=True, required=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'author',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        # униальные теги
        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError('Теги повторяются.')
        # количество тегов больше или равно 1
        if len(data['tags']) == 0:
            raise serializers.ValidationError(
                'Необходимо выбрать хотя бы один тег.')
        # уникальыне ингредиенты
        ingredients_list = data['ingredients']
        if len(ingredients_list) != len(
                set(obj['id'] for obj in ingredients_list)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        # ингредиенты больше или равно 1
        if len(data['ingredients']) == 0:
            raise serializers.ValidationError(
                'Необходимо добавить ингредиент.'
            )
        # количество ингредиентов
        if any(obj['amount'] <= 0 for obj in ingredients_list):
            raise serializers.ValidationError(
                'Введите корректное количество ингредиентов.'
            )
        # время приготовления
        if data['cooking_time'] <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return super().validate(data)

    @staticmethod
    def create_ingredients(ingredients, recipe):
        """Создать ингредиент."""
        ingredients_in_recipe = [
            IngredientInRecipe(
                recipe=recipe,
                ingredients=item['id'],
                amount=item['amount']
            ) for item in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(ingredients_in_recipe)

    def create(self, data):
        """Создать рецепт."""
        request = self.context.get('request')
        ingredients = data.pop('ingredients')
        tags = data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, data):
        """Обновить рецепт."""
        tags = data.pop('tags')
        ingredients = data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients(recipe=instance, ingredients=ingredients)
        return super().update(instance, data)


class RecipeShortSerializer(RecipeReadSerializer):
    """Короткая версия рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(RecipeShortSerializer):
    """Список покупок. POST/DELETE: api/recipes/{id}/shopping_cart/"""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class FavoriteSerializer(RecipeShortSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
