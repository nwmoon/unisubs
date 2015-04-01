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

from django.shortcuts import render

from . import views as old_views
from .models import Team

def get_team_for_view(slug, user, exclude_private=True):
    try:
        return Team.objects.for_user(user, exclude_private).get(slug=slug)
    except Team.DoesNotExist:
        raise Http404

def dashboard(request, slug):
    team = get_team_for_view(slug, request.user, exclude_private=False)
    if not team.is_old_style() and not team.user_is_member(request.user):
        return welcome(request, team)
    else:
        return team.new_workflow.dashboard_view(request, team)


def welcome(request, team):
    if team.is_visible:
        videos = team.videos.order_by('-id')[:3]
    else:
        videos = None
    return render(request, 'teams/welcome.html', {
        'team': team,
        'messages': team.get_messages([
            'pagetext_welcome_heading',
            'pagetext_welcome_heading2',
        ]),
        'videos': videos,
    })
