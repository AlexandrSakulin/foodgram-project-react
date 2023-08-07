from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User
from foodgram.global_constants import (
    MAX_LENGTH_AUTHOR,
    MAX_LENGTH_RECIPE_NAME,
    MAX_LENGTH_TAG_NAME,
    MAX_LENGTH_TAG_COLOR,
    MAX_LENGTH_TAG_SLUG,
    MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_INGREDIENT_MEAUNIT,
)


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
        max_length=MAX_LENGTH_AUTHOR
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_RECIPE_NAME
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/image/recipes',
        blank=True,
        null=True
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='Ингредиенты',
        through='IngredientInRecipe'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (минут)',
        validators=[
            MinValueValidator(1,
                              'Время приготовления не менее 1 минуты!'),
            MaxValueValidator(
                32767, 'Время приготовления должно быть не более 32767 минут!')
        ]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    update = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True
    )
    color = models.CharField(
        verbose_name='HEX-код цвета',
        max_length=MAX_LENGTH_TAG_COLOR,
        unique=True,
        help_text='Например, #49B64E',
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Внесите данные согласно заданной маске',
            )
        ],
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_INGREDIENT_NAME,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH_INGREDIENT_MEAUNIT,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique measurement_unit')]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientInRecipe(models.Model):
    """ Модель связи ингредиента и рецепта. """
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE
    )
    ingredients = models.ForeignKey(
        Ingredient,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(1, 'Не менее 1'),
            MaxValueValidator(32767, 'Не более 32767')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredients', 'amount'],
                name='unique ingredient and amount')]

    def __str__(self):
        return f'{self.ingredients}: {self.amount}'


class AbstractModel(models.Model):
    """Abstract model for Favorite and ShoppingCart"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    class Meta:
        abstract = True


class Favorite(AbstractModel):
    """ Модель избранного. """

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                name='unique_favorite',
                fields=['recipe', 'user'],
            ),
        ]


class ShoppingCart(AbstractModel):
    """ Модель корзины. """

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                name='unique_shopping_cart',
                fields=['recipe', 'user'],
            ),
        ]