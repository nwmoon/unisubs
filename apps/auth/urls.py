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

from django.conf.urls import patterns, url

urlpatterns = patterns('auth.views',
    url(r'^login/$', 'login', name='login'),
    url(r'^create/$', 'create_user', name='create_user'),
    url(r'^delete/$', 'delete_user', name='delete_user'),
    url(r'^login_post/$', 'login_post', name='login_post'),
    url(r'confirm_email/(?P<confirmation_key>\w+)/$', 'confirm_email', name='confirm_email'),
    url(r'auto-login/(?P<token>[\w]{40})/$', 'token_login', name='token-login'),
    url(r'resend_confirmation_email/$', 'resend_confirmation_email', name='resend_confirmation_email'),
    url(r'login-trap/$', 'login_trap', name='login_trap'),
)
