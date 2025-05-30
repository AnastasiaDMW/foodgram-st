from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from .models import User, Subscription


class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['password'].widget.attrs['value'] = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        if 'password' in self.changed_data and self.cleaned_data['password']:
            user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('email', 'username', 'first_name', 'last_name')
    fieldsets = (
        (
            None,
            {
                'fields': ('email', 'password'),
                'description': _(
                    "Введите новый пароль в чистом виде. "
                    "Он будет автоматически зашифрован при сохранении."
                ),
            },
        ),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
