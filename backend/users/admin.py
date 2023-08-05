from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscribe


@admin.register(User)
class UserAdmin(UserAdmin):

    def subscriptions_count(self, user):
        return user.author.count()

    def recipes_count(self, user):
        return user.recipes.count()

    list_display = (
        'id',
        'first_name',
        'last_name',
        'username',
        'email',
        'bio',
        'subscriptions_count',
        'recipes_count'
    )
    list_display_links = (
        'id',
    )
    search_fields = (
        'username',
    )


@admin.register(Subscribe)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'author']
    search_fields = [
        'author__username',
        'author__email',
        'user__username',
        'user__email'
    ]
    list_filter = ['author__username', 'user__username']
    empty_value_display = ''
