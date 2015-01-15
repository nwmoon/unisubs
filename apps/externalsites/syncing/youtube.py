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

"""externalsites.syncing.youtube -- Sync subtitles to/from Youtube"""

import logging

from django.conf import settings
from django.utils import translation
from gdata.youtube.client import YouTubeClient
from gdata.youtube.data import CaptionFeed
from gdata.gauth import OAuth2Token
import babelsubs
import unilangs

from utils.metrics import Meter, Occurrence

# NOTE
# It would be nice to use API version 3 for this and also to use the
# utils.youtube module to handle it.  However, captions are currently only
# supported on version 2 -- even though its deprecated.  So this is basically
# code copied from the old videos.types.youtube module and it uses the version
# 2 client library.

AMARA_CREDIT = translation.ugettext_lazy("Subtitles by the Amara.org community")
AMARA_DESCRIPTON_CREDIT = translation.ugettext_lazy(
    "Help us caption & translate this video!")

logger = logging.getLogger("externalsites.syncing.youtube")

CAPTION_TRACK_LINK_REL = ('http://gdata.youtube.com'
                          '/schemas/2007#video.captionTracks')

def _format_subs_for_youtube(subtitle_set):
    return babelsubs.to(subtitle_set, 'sbv').encode('utf-8')

class YoutubeAPIBridge(object):
    """YoutubeAPIBridge -- handles calls to the youtube client."""

    def __init__(self, access_token):
        self.client = YouTubeClient()
        token = OAuth2Token(
                         client_id=settings.YOUTUBE_CLIENT_ID,
                         client_secret=settings.YOUTUBE_CLIENT_SECRET,
                         scope='https://gdata.youtube.com',
                         user_agent='universal-subtitles',
                         access_token=access_token,)
        token.authorize(self.client)
        
    def get_caption_info(self, video_id):
        """ Retrieves the current caption data for a youtube video.

        :returns: dictionary with the format:
        {
            "lang_code": {
                   "url": [url for track]
                    "track": [track entry object, useful for other operations]
             }
        }
        """

        entry = self.client.GetVideoEntry(video_id=video_id)
        caption_track = entry.get_link(rel=CAPTION_TRACK_LINK_REL)

        if not caption_track:
            # No tracks were returned.  This video doesn't have any existing
            # captions.
            return {}

        captions_feed = self.client.get_feed(caption_track.href,
                                             desired_class=CaptionFeed)

        caption_info = {}

        for entry in captions_feed.entry:
            lang = entry.get_elements(tag="content")[0].lang
            url = entry.get_edit_media_link().href
            caption_info[lang] = {
                "url": url,
                "track": entry
            }

        return caption_info

    def get_youtube_language_code(self, language_code):
        """Convert the language for a SubtitleVersion to a youtube code
        """
        lc = unilangs.LanguageCode(language_code.lower(), "unisubs")
        return lc.encode("youtube")



    def create_track(self, video_id, title, language_code, content):
        self.client.create_track(video_id, title, language_code, content,
                                 settings.YOUTUBE_CLIENT_ID,
                                 settings.YOUTUBE_API_KEY)

    def delete_track(self, video_id, track):
        return self.client.delete_track(video_id, track,
                                        settings.YOUTUBE_CLIENT_ID,
                                        settings.YOUTUBE_API_KEY)

def update_subtitles(video_id, access_token, subtitle_version):
    """Push the subtitles for a language to YouTube """

    bridge = YoutubeAPIBridge(access_token)
    try:
        language_code = bridge.get_youtube_language_code(
            subtitle_version.subtitle_language.language_code)
    except KeyError:
        logger.error("Couldn't encode LC %s to youtube" % language_code)
        return

    subs = subtitle_version.get_subtitles()
    if should_add_credit_to_subtitles(subtitle_version, subs):
        add_credit_to_subtitles(subtitle_version, subs)
    content = _format_subs_for_youtube(subs)
    title = ""

    caption_info = bridge.get_caption_info(video_id)

    # We can't just update a subtitle track in place.  We need to delete
    # the old one and upload a new one.
    if language_code in caption_info:
        bridge.delete_track(video_id, caption_info[language_code]['track'])

    bridge.create_track(video_id, title, language_code, content)
    Meter('youtube.subs_pushed').inc()

def delete_subtitles(video_id, access_token, language_code):
    """Delete the subtitles for a language on YouTube """

    bridge = YoutubeAPIBridge(access_token)
    try:
        language_code = bridge.get_youtube_language_code(language_code)
    except KeyError:
        logger.error("Couldn't encode LC %s to youtube" % language_code)
        return

    caption_info = bridge.get_caption_info(video_id)
    if language_code in caption_info:
        bridge.delete_track(video_id, caption_info[language_code]['track'])
    else:
        logger.error("Couldn't find LC %s in youtube" % language_code)

def should_add_credit_to_subtitles(subtitle_version, subs):
    if len(subs) == 0 or not subs.fully_synced:
        return False
    if subtitle_version.video.get_team_video() is not None:
        return False
    if not subtitle_version.video.duration:
        return False
    return True

def add_credit_to_subtitles(subtitle_version, subs):
    with translation.override(subtitle_version.language_code):
        credit_text = translation.gettext(AMARA_CREDIT)

    duration = subtitle_version.video.duration * 1000

    last_sub = subs[-1]
    if last_sub.end_time is None or last_sub.end_time >= duration:
        return

    start_time = max(last_sub.end_time, duration - 3000)
    subs.append_subtitle(start_time, duration, credit_text)
