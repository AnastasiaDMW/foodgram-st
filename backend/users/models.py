from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from backend.settings import REGEX_USERNAME


class User(AbstractUser):
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    USERNAME_FIELD = 'email'

    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True,
        error_messages={
            'field_name': 'email',
        },
    )
    username = models.CharField(
        verbose_name='Юзернейм',
        max_length=150,
        unique=True,
        db_index=True,
        error_messages={
            'field_name': 'username',
        },
        validators=[RegexValidator(regex=REGEX_USERNAME)],
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )
    avatar = models.ImageField(
        upload_to='users',
        verbose_name='Аватарка',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Текущий пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='На кого подписан',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('subscriber', 'author'),
                name='unique_subscriber_author',
            ),
        ]

    def clean(self):
        if self.subscriber == self.author:
            raise ValidationError(
                'Вы не можете подписаться на самого себя.'
            )

    def __str__(self):
        return f'{self.subscriber.username} -> {self.author.username}'
