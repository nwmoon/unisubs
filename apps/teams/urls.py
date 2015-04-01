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

from django.views.generic.base import TemplateView
from django.conf.urls import url, patterns
from teams.rpc import rpc_router

urlpatterns = patterns('teams.new_views',
    url(r'^(?P<slug>[-\w]+)/$', 'dashboard', name='dashboard'),
)

urlpatterns += patterns('teams.views',
    url(r'^$', 'index', name='index'),
    url(r'^my/$', 'index', {'my_teams': True}, name='user_teams'),
    url(r'^create/$', 'create', name='create'),
    url(r'^router/$', rpc_router, name='rpc_router'),
    url(r'^router/api/$', rpc_router.api, name='rpc_api'),
    url(r'^tasks/perform/$', 'perform_task', name='perform_task'),
    url(r'^invite/accept/(?P<invite_pk>\d+)/$', 'accept_invite', name='accept_invite'),
    url(r'^invite/deny/(?P<invite_pk>\d+)/$', 'accept_invite', {'accept': False}, name='deny_invite'),
    url(r'^join_team/(?P<slug>[-\w]+)/$', 'join_team', name='join_team'),
    url(r'^leave_team/(?P<slug>[-\w]+)/$', 'leave_team', name='leave_team'),
    url(r'^highlight/(?P<slug>[-\w]+)/$', 'highlight', name='highlight'),
    url(r'^unhighlight/(?P<slug>[-\w]+)/$', 'highlight', {'highlight': False}, name='unhighlight'),
    url(r'^(?P<slug>[-\w]+)/approvals/$', 'approvals', name='approvals'),
    url(r'^(?P<slug>[-\w]+)/move-videos/$', 'move_videos', name='move_videos'),
    url(r'^(?P<slug>[-\w]+)/applications/$', 'applications', name='applications'),
    url(r'^(?P<slug>[-\w]+)/application/approve/(?P<application_pk>\d+)/$', 'approve_application', name='approve_application'),
    url(r'^(?P<slug>[-\w]+)/application/deny/(?P<application_pk>\d+)/$', 'deny_application', name='deny_application'),
    url(r'^move/$', 'move_video', name='move_video'),
    url(r'^add/video/(?P<slug>[-\w]+)/$', 'add_video', name='add_video'),
    url(r'^add/videos/(?P<slug>[-\w]+)/$', 'add_videos', name='add_videos'),
    url(r'^add-video-to-team/(?P<video_id>(\w|-)+)/', 'add_video_to_team', name='add_video_to_team'),
    url(r'^edit/video/(?P<team_video_pk>\d+)/$', 'team_video', name='team_video'),
    url(r'^remove/video/(?P<team_video_pk>\d+)/$', 'remove_video', name='remove_video'),
    url(r'^remove/members/(?P<slug>[-\w]+)/(?P<user_pk>\d+)/$', 'remove_member', name='remove_member'),
    url(r'^(?P<slug>[-\w]+)/videos/$', 'detail', name='detail'),
    url(r'^(?P<slug>[-\w]+)/members/$', 'detail_members', name='detail_members'),
    url(r'^(?P<slug>[-\w]+)/members/role-saved/$', 'role_saved', name='role_saved'),
    url(r'^(?P<slug>[-\w]+)/members/invite/$', 'invite_members', name='invite_members'),
    url(r'^(?P<slug>[-\w]+)/members/search/$', 'search_members', name='search_members'),
    url(r'^(?P<slug>[-\w]+)/members/(?P<role>[-\w]+)/$', 'detail_members', name='detail_members_role'),
    url(r'^(?P<slug>[-\w]+)/activity/$', 'activity', name='activity'),
    url(r'^(?P<slug>[-\w]+)/activity/team/$', 'team_activity',
        name='team-activity'),
    url(r'^(?P<slug>[-\w]+)/activity/videosstatistics/$', 'videosstatistics_activity',
        name='videosstatistics-activity'),
    url(r'^(?P<slug>[-\w]+)/activity/teamstatistics/$', 'teamstatistics_activity',
        name='teamstatistics-activity'),
    url(r'^(?P<slug>[-\w]+)/projects/$', 'project_list', name='project_list'),
    url(r'^(?P<slug>[-\w]+)/tasks/$', 'team_tasks', name='team_tasks'),
    url(r'^(?P<slug>[-\w]+)/create-task/(?P<team_video_pk>\d+)/$', 'create_task', name='create_task'),
    url(r'^(?P<slug>[-\w]+)/delete-task/$', 'delete_task', name='delete_task'),
    url(r'^(?P<slug>[-\w]+)/upload-draft/(?P<video_id>\w+)/$', 'upload_draft', name='upload_draft'),
    url(r'^(?P<slug>[-\w]+)/(?P<task_pk>\d+)/download/(?P<type>[-\w]+)/$', 'download_draft', name='download_draft'),
    url(r'^(?P<slug>[-\w]+)/assign-task/$', 'assign_task', name='assign_task'),
    url(r'^(?P<slug>[-\w]+)/assign-task/a/$', 'assign_task_ajax', name='assign_task_ajax'),
    url(r'^(?P<slug>[-\w]+)/tasks/(?P<task_pk>\d+)/perform/$', 'perform_task', name='perform_task'),
    url(r'^(?P<slug>[-\w]+)/tasks/(?P<task_pk>\d+)/perform/$', 'perform_task', name='perform_task'),
    url(r'^(?P<slug>[-\w]+)/feeds/$', 'video_feeds', name='video_feeds'),
    url(r'^(?P<slug>[-\w]+)/feeds/(?P<feed_id>\d+)$', 'video_feed', name='video_feed'),
    url(r'^(?P<slug>[-\w]+)/settings/$', 'settings_basic', name='settings_basic'),
    url(r'^(?P<slug>[-\w]+)/settings/guidelines/$', 'settings_guidelines', name='settings_guidelines'),
    url(r'^(?P<slug>[-\w]+)/settings/permissions/$', 'settings_permissions', name='settings_permissions'),
    url(r'^(?P<slug>[-\w]+)/settings/languages/$', 'settings_languages', name='settings_languages'),
    url(r'^(?P<slug>[-\w]+)/settings/projects/$', 'settings_projects', name='settings_projects'),
    url(r'^(?P<slug>[-\w]+)/settings/projects/add/$', 'add_project', name='add_project'),
    url(r'^(?P<slug>[-\w]+)/settings/projects/(?P<project_slug>[-\w]+)/$', 'edit_project', name='edit_project'),
    # just /p/ will bring all videos on any projects
    url(r'^(?P<slug>[-\w]+)/p/(?P<project_slug>[-\w]+)?/?$', 'detail', name='project_video_list'),
    # TODO: Review these...
    url(r'^(?P<slug>[-\w]+)/p/(?P<project_slug>[-\w]+)/tasks/?$', 'team_tasks', name='project_tasks'),
    url(r'^(?P<slug>[-\w]+)/delete-language/(?P<lang_id>[\w\-]+)/', 'delete_language', name='delete-language'),
    url(r'^(?P<slug>[-\w]+)/auto-captions-status/$', 'auto_captions_status', name='auto-captions-status'),
)

urlpatterns += patterns('',
    (r'^t1$',
     TemplateView.as_view(template_name='jsdemo/teams_profile.html')),
)

# settings views that are handled by other apps
urlpatterns += patterns('',
    url(r'^(?P<slug>[-\w]+)/settings/accounts/$', 'externalsites.views.team_settings_tab', name='settings_externalsites'),
)
