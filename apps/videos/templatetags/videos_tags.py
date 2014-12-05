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
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django import template

register = template.Library()

from django.contrib.sites.models import Site

from staticmedia import utils
from utils.basexconverter import base62
from videos.views import LanguageList
from videos.types import video_type_registrar, VideoTypeError
from videos import permissions
from videos import share_utils

@register.inclusion_tag('videos/_video.html', takes_context=True)
def render_video(context, video, display_views='total'):
    context['video'] = video

    if display_views and hasattr(video, '%s_views' % display_views):
        context['video_views'] = getattr(video, '%s_views' % display_views)
    else:
        context['video_views'] = video.total_views

    return context

@register.inclusion_tag('videos/_feature_video.html', takes_context=True)
def feature_video(context, video):
    context['video'] = video
    return context

@register.filter
def is_follower(obj, user):
    # obj is Video or SubtitleLanguage
    if not user.is_authenticated():
        return False

    if not obj:
        return False

    return obj.user_is_follower(user)

@register.filter
def can_user_edit_video_urls(video, user):
    return permissions.can_user_edit_video_urls(video, user)

@register.simple_tag
def write_video_type_js(video):
    if not video or not bool(video.get_video_url()):
        return
    try:
        vt = video_type_registrar.video_type_for_url(video.get_video_url())
        if hasattr(vt, "js_url"):
            return '<script type="text/javascript" src="%s"><script/>' % vt.js_url
    except VideoTypeError:
        return

from django.template.defaulttags import URLNode
class VideoURLNode(URLNode):
    def render(self, video, request):
        if self.asvar:
            context[self.asvar]= urlparse.urljoin(domain, context[self.asvar])
            return ''
        else:
            return urlparse.urljoin(domain, path)
        path = super(AbsoluteURLNode, self).render(context)

        return urlparse.urljoin(domain, path)

def video_url(parser, token, node_cls=VideoURLNode):
    """
    Does the logic to decide if a video must have a secret url passed into it or not.
    If video must be acceceed thourgh private url, the 40chars hash are inserted instead
    of the video_id.
    """
    bits = token.split_contents()
    print "token", token
    print "bits", bits
    node_instance = url(parser, token)
    return node_cls(view_name=node_instance.view_name,
        args=node_instance.args,
        kwargs=node_instance.kwargs,
        asvar=node_instance.asvar)
video_url = register.tag(video_url)

@register.filter
def in_progress(language):
    return (not language.get_tip(public=True) and
        language.get_tip(public=False))

@register.filter
def format_duration(value):

    """
    Based on a Template Tag by Dan Ward 2009 (http://d-w.me)
    Usage: {{ VALUE|format_duration }}
    """

    # Place seconds in to integer
    secs = int(value)

    # If seconds are greater than 0
    if secs > 0:

        # Import math library
        import math

        # Place durations of given units in to variables
        daySecs = 86400
        hourSecs = 3600
        minSecs = 60

        # Create string to hold outout
        durationString = ''

        # Calculate number of days from seconds
        days = int(math.floor(secs / int(daySecs)))

        # Subtract days from seconds
        secs = secs - (days * int(daySecs))

        # Calculate number of hours from seconds (minus number of days)
        hours = int(math.floor(secs / int(hourSecs)))

        # Subtract hours from seconds
        secs = secs - (hours * int(hourSecs))

        # Calculate number of minutes from seconds (minus number of days and hours)
        minutes = int(math.floor(secs / int(minSecs)))

        # Subtract days from seconds
        secs = secs - (minutes * int(minSecs))

        # Calculate number of seconds (minus days, hours and minutes)
        seconds = secs

        # If number of days is greater than 0
        if days > 0:

            durationString += '%02d' % (days,) + ':'

        # Determine if next string is to be shown
        if hours > 0 or days > 0:

            durationString += '%02d' % (hours,) + ':'

        # If number of minutes is greater than 0
        if minutes > 0 or days > 0 or hours > 0:

            durationString += '%02d' % (minutes,) + ':'

        # If number of seconds is greater than 0
        if seconds > 0 or minutes > 0 or days > 0 or hours > 0:

            if minutes == 0 and days == 0 and hours == 0:
                durationString += '0:%02d' % (seconds,)
            else:
                durationString += '%02d' % (seconds,)

        # Return duration string
        return durationString.strip()

    # If seconds are not greater than 0
    else:

        # Provide 'No duration' message
        return 'No duration'


def shortlink_for_video( video):
    """Return a shortlink string for the video.

    The pattern is http://amara.org/v/<pk>
    """
    protocol = getattr(settings, 'DEFAULT_PROTOCOL')
    domain = Site.objects.get_current().domain
    # don't www me, we'll redirect users and save three
    # chars. Yay for our twitter-brave-new-world
    domain = domain.replace("www.", '')
    encoded_pk = base62.from_decimal(video.pk)
    path = reverse('shortlink', args=[encoded_pk], no_locale=True)

    return u"{0}://{1}{2}".format(unicode(protocol),
                                  unicode(domain), 
                                  unicode(path))

@register.filter
def multi_video_create_subtitles_data_attrs(video):
    attrs = [
        ('data-video-id', video.id),
        ('data-video-langs', ':'.join(l.language_code for l in
                                      video.all_subtitle_languages())),
    ]
    if video.primary_audio_language_code:
        attrs.append(('data-video-primary-audio-lang-code',
                      video.primary_audio_language_code))
    return mark_safe(' '.join('%s="%s"' % (key, value)
                              for (key, value) in attrs))

@register.simple_tag(name='language-list')
def language_list(video):
    cached = video.cache.get('language-list')
    if cached is not None:
        return cached
    video.prefetch_languages(with_public_tips=True,
                             with_private_tips=True)
    content = render_to_string('videos/_language-list.html', {
        'video': video,
        'language_list': LanguageList(video),
        'STATIC_URL': utils.static_url(),
    })
    video.cache.set('language-list', content)
    return content

@register.simple_tag(name='video-metadata', takes_context=True)
def video_metadata(context, video):
    request = context['request']
    metadata = video.get_metadata_for_locale(request.LANGUAGE_CODE)
    return "\n".join(
        '<h4>{0}: {1}</h4>'.format(field['label'], field['content'])
        for field in metadata.convert_for_display()
    )

@register.simple_tag(name='sharing-widget-for-video')
def sharing_widget_for_video(video):
    cached = video.cache.get('sharing-widget')
    if cached is not None:
        return cached
    context = share_utils.share_panel_context_for_video(video)
    content = render_to_string('_sharing_widget.html', context)
    video.cache.set("sharing-widget", content)
    return content
