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
from django import template
from django.template.loader import render_to_string

from messages.models import Message

register = template.Library()

@register.simple_tag(takes_context=True)
def messages(context):
    user = context['user']
    request = context['request']
    hidden_message_id = request.COOKIES.get(Message.hide_cookie_name)
    if not user.is_authenticated():
        return ''

    cached = user.cache.get('messages')
    if isinstance(cached, tuple) and cached[0] == hidden_message_id:
        return cached[1]

    qs = user.unread_messages(hidden_message_id)
    try:
        last_unread = qs[:1].get().pk
    except Message.DoesNotExist:
        last_unread = ''
    count = user.unread_messages_count(hidden_message_id)
    
    content = render_to_string('messages/_messages.html',  {
        'msg_count': count,
        'last_unread': last_unread,
        'cookie_name': Message.hide_cookie_name
    })
    user.cache.set('messages', (hidden_message_id, content), 30 * 60)
    return content

