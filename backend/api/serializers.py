from django.db.models import F
from djoser import serializers as ds
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class UserReadSerializer(ds.UserSerializer):
    """ Сериализатор Пользователей """

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
        return (request.user.is_authenticated and user.following.filter(
            user=request.user).exists())


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписки. """

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


class TagSerializer(serializers.ModelSerializer):
    """Сериализато тегов. """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты. """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте. """
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all())
    name = serializers.StringRelatedField(source='ingredient'
                                                 '.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Чтение рецептов. """
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
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):

        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipe_ingredients__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and obj.recipes_favorite_related.filter(
                user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and obj.recipes_shoppingcart_related.filter(
                user=request.user).exists()
        )


class IngredientInRecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и обновление рецепта."""
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

        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError('Теги повторяются.')

        if len(data['tags']) == 0:
            raise serializers.ValidationError(
                'Необходимо выбрать хотя бы один тег.')
        ingredients_list = data['ingredients']
        if len(ingredients_list) != len(
                set(obj['id'] for obj in ingredients_list)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        if len(data['ingredients']) == 0:
            raise serializers.ValidationError(
                'Необходимо добавить ингредиент.'
            )
        if any(obj['amount'] <= 0 for obj in ingredients_list):
            raise serializers.ValidationError(
                'Введите корректное количество ингредиентов.'
            )
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
    """Список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        if user.recipes_shoppingcart_related.filter(
                recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже в списке покупок.'
            )
        return data


class FavoriteSerializer(RecipeShortSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        if user.recipes_favorite_related.filter(
                recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже в избранном.'
            )
        return data