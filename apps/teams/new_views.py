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

"""new_views -- New team views

This module holds view functions for new-style teams.  Eventually it should
replace the old views.py module.
"""

from __future__ import absolute_import
import logging

from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _

from . import views as old_views
from . import forms
from . import permissions
from .models import Team

logger = logging.getLogger('teams.views')

def team_view(view_func):
    def wrapper(request, slug, *args, **kwargs):
        try:
            team = Team.objects.for_user(request.user, exclude_private=True).get(slug=slug)
        except Team.DoesNotExist:
            raise Http404
        return view_func(request, team, *args, **kwargs)
    return wrapper

@team_view
def dashboard(request, team):
    if not team.is_old_style() and not team.user_is_member(request.user):
        return welcome(request, team)
    else:
        return team.new_workflow.dashboard_view(request, team)

def welcome(request, team):
    if team.is_visible:
        videos = team.videos.order_by('-id')[:2]
    else:
        videos = None
    return render(request, 'new-teams/welcome.html', {
        'team': team,
        'messages': team.get_messages([
            'pagetext_welcome_heading',
        ]),
        'videos': videos,
    })

@team_view
def settings_basic(request, team):
    if team.is_old_style():
        return old_views.settings_basic(request, team)

    if permissions.can_rename_team(team, request.user):
        FormClass = forms.RenameableSettingsForm
    else:
        FormClass = forms.SettingsForm

    if request.POST:
        form = FormClass(request.POST, request.FILES, instance=team)

        is_visible = team.is_visible

        if form.is_valid():
            try:
                form.save()
            except:
                logger.exception("Error on changing team settings")
                raise

            if is_visible != form.instance.is_visible:
                update_video_public_field.delay(team.id)
                invalidate_video_visibility_caches.delay(team)

            messages.success(request, _(u'Settings saved.'))
            return HttpResponseRedirect(request.path)
    else:
        form = FormClass(instance=team)

    return render(request, "new-teams/settings.html", {
            'team': team, 'form': form,
    })
