# Amara, universalsubtitles.org
#
# Copyright (C) 2014 Participatory Culture Foundation
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

"""accountlinker.newyoutube -- New youtube code

This comes from utils.youtube in the gh-1488 branch.  We need to to get
channel_ids in preparation of our migration.
"""

from collections import namedtuple
import json
import logging
import urllib
import re

from django.conf import settings
from django.utils.translation import ugettext as _
import requests

from utils.text import fmt

class APIError(StandardError):
    """Error communicating with YouTube's API."""
    pass

class OAuthError(APIError):
    """Error handling YouTube's OAuth."""
    pass

OAuthCallbackData = namedtuple('OAuthCallbackData', [
    'refresh_token', 'access_token', 'channel_id', 'username', 'state'
])
VideoInfo = namedtuple('VideoInfo',
                       'channel_id title description duration thumbnail_url')

logger = logging.getLogger('utils.youtube')

def request_token_url(redirect_uri, state):
    """Get the URL to for the request token

    We should redirect the user's browser to this URL when trying to initiate
    OAuth authentication.

    The basic flow is that we send the user's browser to request_token_url,
    then youtube does it's OAuth stuff and sends the browser back to
    redirect_uri.  Then the calling code calls handle_callback() to process
    the OAuth data sent with the request to redirect_uri.

    :param redirect_uri: URI to redirect the user to after youtube
    authentication is complete
    :param state: dict of state info.  This will get returned back from
    handle_callback()
    """

    params = {
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid https://www.googleapis.com/auth/youtube",
        "state": json.dumps(state),
        "response_type": "code",
        "approval_prompt": "force",
        "access_type": "offline",
    }

    return ("https://accounts.google.com/o/oauth2/auth?" + 
            urllib.urlencode(params))

def _oauth_token_post(**params):
    params["client_id"] = settings.YOUTUBE_CLIENT_ID
    params["client_secret"] = settings.YOUTUBE_CLIENT_SECRET

    response = requests.post("https://accounts.google.com/o/oauth2/token",
                             data=params, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })

    if response.status_code != 200:
        logger.error("Error requesting Youtube OAuth token", extra={
                    "data": {
                        "sent_data": params,
                        "response": response.content
                    },
                })
        raise OAuthError('Authentication error')

    if response.json.get('error', None):
        logger.error("Error on requesting Youtube OAuth token", extra={
                    "data": {
                        "sent_data": params,
                        "response": response.content
                    },
                })
        raise OAuthError(response.json['error'])

    return response

def handle_callback(request, redirect_uri):
    """Handle the youtube oauth callback.

    :param request: djongo Request object
    :redirect_uri: same URI as as passed to request_token_url()

    :returns: OAuthCallbackData object
    """

    code = request.GET.get('code')
    error = request.GET.get('error')
    state = request.GET.get('state')

    if error is not None:
        raise OAuthError(fmt(_('Youtube error: %(error)s'), error=error))

    if code is None:
        logger.warn("handle_callback: no authorization code (%s)" %
                    request.GET)
        raise OAuthError(_('Error while linking.  Please try again.'))

    if state is not None:
        state = json.loads(state)

    # exchange the auth code for refresh/access tokens
    response = _oauth_token_post(code=code, grant_type='authorization_code',
                                 redirect_uri=redirect_uri)


    user_info = get_user_info(response.json['access_token'])

    return OAuthCallbackData(
        response.json['refresh_token'],
        response.json['access_token'],
        user_info[0],
        user_info[1],
        state,
    )

def get_new_access_token(refresh_token):
    response = _oauth_token_post(grant_type='refresh_token',
                                 refresh_token=refresh_token)
    return response.json['access_token']

def revoke_auth_token(refresh_token):
    requests.get('https://accounts.google.com/o/oauth2/revoke',
                 params={'token': refresh_token})

YOUTUBE_REQUEST_URL_BASE = 'https://www.googleapis.com/youtube/v3/'
def _make_api_request(method, access_token, url_path, data=None, params=None,
                      headers=None):
    """Make a youtube API request

    :param method: HTTP method to use
    :param access_token: access token to use, or None for APIs that don't
    need authentication
    :param url_path: url path relative to YOUTUBE_REQUEST_URL_BASE
    :param data: data to send to the server
    :param params: params to add to the URL
    :param headers: headers to send to the server
    """
    if access_token is not None:
        if headers is None:
            headers = {}
        headers['Authorization'] = 'Bearer %s' % access_token
    else:
        headers = None
        if params is None:
            params = {}
        params['key'] = settings.YOUTUBE_API_KEY
    url = YOUTUBE_REQUEST_URL_BASE + url_path
    response = requests.request(method, url, data=data, params=params,
                                headers=headers)
    if response.status_code != 200:
        try:
            errors = response.json['error']['errors']
            message = ' '.join(e['reason'] for e in errors)
        except StandardError, e:
            logger.error("%s parsing youtube response: %s" % (
                e, response.content))
            message = 'Unkown error'
        raise APIError(message)
    return response

def channel_get(access_token, part, mine='true'):
    return _make_api_request('get', access_token, 'channels', params={
        'part': ','.join(part),
        'mine': mine,
    })

def video_get(access_token, video_id, part):
    return _make_api_request('get', access_token, 'videos', params={
        'id': video_id,
        'part': ','.join(part),
    })

def video_put(access_token, video_id, **data):
    part = '.'.join(data.keys())
    data['id'] = video_id
    return _make_api_request('put', access_token, 'videos', params={
        'part': part,
    }, data=json.dumps(data), headers={
        'content-type': 'application/json'
    })

def get_user_info(access_token):
    """Get info about a user logged in with access_token

    google/youtube have this concept of "channel IDs" which uniquely identify
    users across youtube, google+, and presumably new services that get added.
    Alongside the channel ID is the channel title, which is a human-friendly
    name to display to the user.

    :returns: (channel_id, display_name) tuple
    """
    response = channel_get(access_token, part=['id','snippet'])
    channel = response.json['items'][0]
    return channel['id'], channel['snippet']['title']

def _parse_8601_duration(duration):
    """Convert a duration in iso 8601 format to seconds as an integer."""
    match = re.match(r'PT((\d+)M)?(\d+)S', duration)
    if match is None:
        return None
    rv = int(match.group(3))
    if match.group(2):
        rv += int(match.group(2)) * 60
    return rv

def get_video_info(video_id):
    response = video_get(None, video_id, ['snippet', 'contentDetails'])
    snippet = response.json['items'][0]['snippet']
    content_details = response.json['items'][0]['contentDetails']

    return VideoInfo(snippet['channelId'],
                     snippet['title'],
                     snippet['description'],
                     _parse_8601_duration(content_details['duration']),
                     snippet['thumbnails']['high']['url'])

def update_video_description(video_id, access_token, description):
    # get the current snippet for the video
    response = video_get(access_token, video_id, ['snippet'])
    snippet = response.json['items'][0]['snippet']
    # send back the snippet with the new description
    snippet['description'] = description
    video_put(access_token, video_id, snippet=snippet)
