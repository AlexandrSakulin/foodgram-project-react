from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Модель создания пользователя."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        max_length=settings.MAX_LENGTH_USERNAME,
        unique=True,
        validators=[
            RegexValidator(
                regex=(r'^[а-яА-Я ]+$'),
                message='Имя пользователя должно соответсвовать критериям',
            )
        ],
    )
    email = models.EmailField(
        max_length=settings.MAX_LENGTH_EMAIL,
        unique=True,
    )
    bio = models.TextField(
        verbose_name='Биография',
        blank=True,
    )
    confirmation_code = models.CharField(
        verbose_name='Токен пользователя',
        max_length=settings.MAX_LENGTH_CONFIRMATION_CODE,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """ Модель подписок. """

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='user_author_unique'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'
