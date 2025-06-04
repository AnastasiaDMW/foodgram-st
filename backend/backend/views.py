import os
import secrets

from django.db.models import Sum, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from djoser.views import UserViewSet

from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart, ShortLink
)
from users.models import Subscription, User
from .serializers import (
    IngredientsSerializer, CustomUserSerializer, SubscribeSerializer,
    UserSubscriptionsSerializer, RecipeSerializer, CreateRecipeSerializer,
    FavoriteSerializer, FavoriteShoppingSerializer, ShoppingCartSerializer,
    UserAvatarSerializer
)
from .filters import IngredientsSearchFilter, RecipeFilterSet
from backend.permissions import IsOwnerOrReadOnly


class IngredientsViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (IngredientsSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet

    def get_permissions(self):
        if self.action == 'create':
            return (permissions.IsAuthenticated(),)
        if self.action in ('partial_update', 'destroy'):
            return (IsOwnerOrReadOnly(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_favorite_shopping_action(
        self, request, recipe, model_class, serializer_class, error_message
    ):
        user = request.user
        instance = model_class.objects.filter(user=user, recipe=recipe).first()

        if request.method == 'POST':
            if instance:
                return Response(
                    {'detail': error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    FavoriteShoppingSerializer(
                        recipe, context={'request': request}
                    ).data,
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'DELETE':
            if instance:
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._handle_favorite_shopping_action(
            request,
            self.get_object(),
            Favorite,
            FavoriteSerializer,
            'Рецепт уже в избранном.'
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_favorite_shopping_action(
            request,
            self.get_object(),
            ShoppingCart,
            ShoppingCartSerializer,
            'Рецепт уже в корзине.'
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values('ingredients__name', 'ingredients__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = "attachment; filename='shopping_cart.pdf'"

        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'font/', 'Roboto.ttf'
        )
        pdfmetrics.registerFont(TTFont('Roboto', font_path))

        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setFont('Roboto', 14)
        pdf.drawString(210, 820, 'Корзина покупок:')

        y_position = 750
        pdf.setFont('Roboto', 12)

        for item in ingredients:
            name = item['ingredients__name']
            unit = item['ingredients__measurement_unit']
            amount = item['total_amount']
            pdf.drawString(70, y_position, f'{name} ({unit}) — {amount}')
            y_position -= 15

        pdf.showPage()
        pdf.save()

        return response

    @action(
        detail=True,
        methods=['GET'],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
        url_path='get-link',
        url_name='get-link'
    )
    def get_short_link(self, request, pk=None):
        short_link, created = ShortLink.objects.get_or_create(
            recipe=Recipe.objects.get(pk=pk),
            defaults={'key': secrets.token_urlsafe(6)[:6]}
        )

        scheme = 'https' if request.is_secure() else 'http'
        return Response({
            "short-link": f"{scheme}://{request.get_host()}/api/s/{short_link.key}"
        })


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in ('retrieve', 'list'):
            return (permissions.AllowAny(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get('id'))

        if user == author:
            return Response(
                {'detail': 'Вы подписываетесь на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = Subscription.objects.filter(
            subscriber=user, author=author
        ).first()

        if request.method == 'POST':
            if subscription:
                return Response(
                    {'detail': 'Вы уже подписались на пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SubscribeSerializer(
                data={'author': author.id},
                context={'user': user, 'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(subscriber=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar'
    )
    def update_my_avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if not request.data.get('avatar'):
                return Response(
                    {'field_name': 'Необходимо предоставить изображение аватара.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserAvatarSerializer(
                user,
                data={'avatar': request.data['avatar']},
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UserSubscriptionsSerializer,
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(author__subscriber=request.user) .prefetch_related('recipes') 
        
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ShortLinkRedirectView(APIView):
    def get(self, request, key):
        short_link = get_object_or_404(ShortLink, key=key)
        return redirect(f'/recipes/{short_link.recipe.id}/')
