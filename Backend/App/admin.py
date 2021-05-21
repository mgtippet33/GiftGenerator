from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Criterion, Holiday, Present, History, User


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    list_display = ('email', 'name',)
    ordering = ('email',)
    fieldsets = (
        (None, {
            'fields': ('email', 'password', 'name', 'premium',
                       'theme', 'phone_number', 'birthday')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password')}
         ),
    )


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)
    search_fields = ('name',)


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'owner',)
    ordering = ('name',)
    search_fields = ('name',)


@admin.register(Present)
class PresentAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'price', 'link', 'desc',)
    ordering = ('-rate',)
    search_fields = ('name',)


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'present', 'date',)
    ordering = ('user',)
    search_fields = ('user',)
