from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Criterion, Holiday, Present, History, User


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    pass


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    pass


@admin.register(Present)
class PresentAdmin(admin.ModelAdmin):
    pass


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    pass


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    list_display = ("email",)
    ordering = ("email",)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'premium',
         'theme', 'phone_number', 'birthday')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password')}
         ),
    )


admin.site.register(User, UserAdmin)
