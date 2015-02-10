# Amara, universalsubtitles.org
# 
# Copyright (C) 2013 Participatory Culture Foundation
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see 
# http://www.gnu.org/licenses/agpl-3.0.html.
from datetime import datetime

from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from models import CustomUser, Announcement


class CustomUserCreationForm(UserCreationForm):
    username = forms.RegexField(label=_("Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."))
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
    email = forms.EmailField(label=_('Email'))

    class Meta:
        model = CustomUser
        fields = ("username", "email")

class UserChangeList(ChangeList):
    def get_ordering(self, request, queryset):
        # The default ChangeList code adds CustomUser.id to the list of
        # ordering fields to make things deterministic.  However this kills
        # performance because the ORDER BY clause includes columns from 2
        # different tables (auth_user.username, auth_customuser.id).
        #
        # Also, sorting by any column other than user also kills performance
        # since our user table is quite large at this point.
        #
        # So we just override everything and force the sort to be username.
        # Username is a unique key so the sort will be fast and deterministic.
        return ['username']

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'is_superuser', 'last_ip', 'partner')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'id')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')}
        ),
    )

    def get_changelist(self, request, **kwargs):
        return UserChangeList

class AnnouncementAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {'widget': widgets.AdminTextareaWidget}
    }
    list_display = ('content', 'created', 'visible')
    actions = ['make_hidden']

    def get_form(self, request, obj=None, **kwargs):
        form = super(AnnouncementAdmin, self).get_form(request, obj=None, **kwargs)

        default_help_text = form.base_fields['created'].help_text
        now = datetime.now()
        form.base_fields['created'].help_text = default_help_text+\
            u'</br>Current server time is %s. Value is saved without timezone converting.' % now.strftime('%m/%d/%Y %H:%M:%S')
        return form

    def visible(self, obj):
        return not obj.hidden
    visible.boolean = True

    def make_hidden(self, request, queryset):
        Announcement.clear_cache()
        queryset.update(hidden=True)
    make_hidden.short_description = _(u'Hide')

admin.site.register(Announcement, AnnouncementAdmin)
admin.site.unregister(User)
admin.site.register(CustomUser, CustomUserAdmin)
