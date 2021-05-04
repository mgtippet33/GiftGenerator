from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Criterion, Holiday, Present, History, Membership


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


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    pass


class MembershipInline(admin.StackedInline):
    model = Membership
    can_delete = False
    verbose_name_plural = 'Membership'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (MembershipInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
