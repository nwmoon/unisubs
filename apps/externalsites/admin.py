# -*- coding: utf-8 -*-
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


from django.contrib import admin

from externalsites import models

class SyncHistoryAdmin(admin.ModelAdmin):
    fields = (
        'video_url',
        'account_type',
        'account_id',
        'language',
        'datetime',
        'version',
        'result',
        'details',
        'retry',
    )
    readonly_fields = (
        'video_url',
        'account_type',
        'account_id',
        'language',
        'datetime',
        'version',
    )
    list_display = (
        'account',
        'video_url',
        'language',
        'retry',
    )
    list_filter = (
        'result',
        'retry',
    )
    list_select_related = True

    class Meta:
        model = models.SyncHistory

    def account(self, sh):
        return sh.get_account()

    def has_add_permission(self, request):
        return False

admin.site.register(models.KalturaAccount)
admin.site.register(models.BrightcoveAccount)
admin.site.register(models.YouTubeAccount)
admin.site.register(models.SyncedSubtitleVersion)
admin.site.register(models.SyncHistory, SyncHistoryAdmin)
