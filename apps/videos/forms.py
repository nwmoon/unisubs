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
import babelsubs
import chardet
import re
from datetime import datetime

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode, DjangoUnicodeDecodeError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from videos.feed_parser import FeedParser
from videos.models import Video, VideoFeed, UserTestResult, VideoUrl
from videos.permissions import can_user_edit_video_urls
from teams.permissions import can_create_and_edit_subtitles
from videos.tasks import import_videos_from_feed
from videos.types import video_type_registrar, VideoTypeError
from utils.forms import AjaxForm, EmailListField, UsernameListField, StripRegexField, FeedURLField, ReCaptchaField
from utils import http
from utils.text import fmt
from utils.translation import get_language_choices, get_user_languages_from_request

KB_SIZELIMIT = 512

import logging
logger = logging.getLogger("videos-forms")

def language_choices_with_empty():
    choices = [
        ('', _('--Select language--'))
    ]
    choices.extend(get_language_choices())
    return choices

class CreateVideoUrlForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(CreateVideoUrlForm, self).__init__(*args, **kwargs)
        self.fields['video'].widget = forms.HiddenInput()

    class Meta:
        model = VideoUrl
        fields = ('url', 'video')

    def clean_url(self):
        url = self.cleaned_data['url']

        try:
            video_type = video_type_registrar.video_type_for_url(url)
        except VideoTypeError, e:
            raise forms.ValidationError(e)

        if not video_type:
            contact_link = fmt(
                _('<a href="mailto:%(email)s">contact us</a>'),
                email=settings.FEEDBACK_EMAIL)
            raise forms.ValidationError(mark_safe(fmt(
                _(u"""Amara does not support that website or video format.
If you'd like to us to add support for a new site or format, or if you
think there's been some mistake, %(contact_link)s!"""),
                contact_link=contact_link)))
        self._video_type = video_type
        return video_type.convert_to_video_url()

    def clean(self):
        data = super(CreateVideoUrlForm, self).clean()
        video = data.get('video')
        if video and not can_user_edit_video_urls(video, self.user):
            raise forms.ValidationError(_('You have not permission add video URL for this video'))

        return self.cleaned_data

    def save(self, commit=True):
        obj = super(CreateVideoUrlForm, self).save(False)
        obj.type = self._video_type.abbreviation
        obj.added_by = self.user
        obj.videoid = self._video_type.video_id or ''
        commit and obj.save()
        return obj

    def get_errors(self):
        output = {}
        for key, value in self.errors.items():
            output[key] = '/n'.join([force_unicode(i) for i in value])
        return output

class UserTestResultForm(forms.ModelForm):

    class Meta:
        model = UserTestResult
        exclude = ('browser',)

    def save(self, request):
        obj = super(UserTestResultForm, self).save(False)
        obj.browser = request.META.get('HTTP_USER_AGENT', 'empty HTTP_USER_AGENT')
        obj.save()
        return obj

class VideoForm(forms.Form):
    # url validation is within the clean method
    video_url = forms.URLField()

    def __init__(self, user=None, *args, **kwargs):
        if user and not user.is_authenticated():
            user = None
        self.user = user
        super(VideoForm, self).__init__(*args, **kwargs)
        self.fields['video_url'].widget.attrs['class'] = 'main_video_form_field'

    def clean_video_url(self):
        video_url = self.cleaned_data['video_url']

        if video_url:
            try:
                video_type = video_type_registrar.video_type_for_url(video_url)
            except VideoTypeError, e:
                raise forms.ValidationError(e)
            if not video_type:
                contact_link = fmt(
                    _('<a href="mailto:%(email)s">Contact us</a>'),
                    email=settings.FEEDBACK_EMAIL)
                for d in video_type_registrar.domains:
                    if d in video_url:
                        raise forms.ValidationError(mark_safe(fmt(
                            _(u"Please try again with a link to a video page.  "
                              "%(contact_link)s if there's a problem."),
                            contact_link=contact_link)))

                raise forms.ValidationError(mark_safe(fmt(
                    _(u"You must link to a video on a compatible site "
                      "(like YouTube) or directly to a video file that works "
                      "with HTML5 browsers. For example: "
                      "http://mysite.com/myvideo.ogg or "
                      "http://mysite.com/myipadvideo.m4v "
                      "%(contact_link)s if there's a problem"),
                    contact_link=contact_link)))

            else:
                self._video_type = video_type
                # we need to use the cannonical url as the user provided might need
                # redirection (i.e. youtu.be/fdaf/), and django's validator will
                # choke on redirection (urllib2 for python2.6), see https://unisubs.sifterapp.com/projects/12298/issues/427646/comments
                video_url = video_type.convert_to_video_url()

        return video_url

    def save(self):
        video_url = self.cleaned_data['video_url']
        obj, created = Video.get_or_create_for_url(video_url, self._video_type, self.user)
        self.created = created
        return obj

youtube_user_url_re = re.compile(r'^(http://)?(www.)?youtube.com/user/(?P<username>[a-zA-Z0-9]+)/?.*$')

class AddFromFeedForm(forms.Form, AjaxForm):
    VIDEOS_LIMIT = 10

    youtube_feed_url_pattern =  'https://gdata.youtube.com/feeds/api/users/%s/uploads'
    usernames = UsernameListField(required=False, label=_(u'Youtube usernames'), help_text=_(u'Enter usernames separated by comma.'))
    youtube_user_url = StripRegexField(youtube_user_url_re, required=False, label=_(u'Youtube page link.'),
                                       help_text=_(u'For example: http://www.youtube.com/user/username'))
    feed_url = FeedURLField(required=False, help_text=_(u'We support: rss 2.0 media feeds including Youtube, Vimeo, Dailymotion, and more.'))

    def __init__(self, user, *args, **kwargs):
        if not user.is_authenticated():
            user = None
        self.user = user
        super(AddFromFeedForm, self).__init__(*args, **kwargs)

        self.video_limit_routreach = False
        self.urls = []

    def clean_feed_url(self):
        url = self.cleaned_data.get('feed_url', '')

        if url:
            self.parse_feed_url(url)

        return url

    def clean_youtube_user_url(self):
        url = self.cleaned_data.get('youtube_user_url', '').strip()

        if url:
            username = youtube_user_url_re.match(url).groupdict()['username']
            url = self.youtube_feed_url_pattern % str(username)
            self.parse_feed_url(url)

        return url

    def clean_usernames(self):
        usernames = self.cleaned_data.get('usernames', [])

        for username in usernames:
            url = self.youtube_feed_url_pattern % str(username)
            self.parse_feed_url(url)

        return usernames

    def parse_feed_url(self, url):
        feed_parser = FeedParser(url)

        if not hasattr(feed_parser.feed, 'version') or not feed_parser.feed.version:
            raise forms.ValidationError(_(u'Sorry, we could not find a valid feed at the URL you provided. Please check the URL and try again.'))
        if url in self.urls:
            raise forms.ValidationError(fmt(
                _(u"Duplicate feed URL in form: %(url)s"),
                url=url))
        if VideoFeed.objects.filter(url=url).exists():
            raise forms.ValidationError(fmt(
                _(u'Feed for %(url)s already exists'),
                url=url))

        self.urls.append(url)

    def success_message(self):
        return _(u"The videos are being added in the background. "
                 u"If you are logged in, you will receive a message when it's done")

    def save(self):
        for url in self.urls:
            feed = self.make_feed(url)
            import_videos_from_feed.delay(feed.id)

    def make_feed(self, url):
        return VideoFeed.objects.create(user=self.user, url=url)

class FeedbackForm(forms.Form):
    email = forms.EmailField(required=False)
    message = forms.CharField(widget=forms.Textarea())
    error = forms.CharField(required=False, widget=forms.HiddenInput)
    captcha = ReCaptchaField(label=_(u'captcha'))

    def __init__(self, *args, **kwargs):
        hide_captcha = kwargs.pop('hide_captcha', False)
        super(FeedbackForm, self).__init__(*args, **kwargs)
        if hide_captcha:
            del self.fields['captcha']

    def send(self, request):
        email = self.cleaned_data['email']
        message = self.cleaned_data['message']
        error = self.cleaned_data['error']
        user_agent_data = u'User agent: %s' % request.META.get('HTTP_USER_AGENT')
        timestamp = u'Time: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        version = u'Version: %s' % settings.PROJECT_VERSION
        commit = u'Commit: %s' % settings.LAST_COMMIT_GUID
        url = u'URL: %s' % request.META.get('HTTP_REFERER', '')
        user = u'Logged in: %s' % (request.user.is_authenticated() and request.user or u'not logged in')
        message = u'%s\n\n%s\n%s\n%s\n%s\n%s\n%s' % (message, user_agent_data, timestamp, version, commit, url, user)
        if error in ['404', '500']:
            message += u'\nPage type: %s' % error
            feedback_emails = [settings.FEEDBACK_ERROR_EMAIL]
        else:
            feedback_emails = settings.FEEDBACK_EMAILS
        headers = {'Reply-To': email} if email else None
        bcc = getattr(settings, 'EMAIL_BCC_LIST', [])
        if email:
            subject = '%s (from %s)' % (settings.FEEDBACK_SUBJECT, email)
        else:
            subject = settings.FEEDBACK_SUBJECT
        EmailMessage(subject, message, email, \
                         feedback_emails, headers=headers, bcc=bcc).send()

        if email:
            headers = {'Reply-To': settings.FEEDBACK_RESPONSE_EMAIL}
            body = render_to_string(settings.FEEDBACK_RESPONSE_TEMPLATE, {})
            email = EmailMessage(settings.FEEDBACK_RESPONSE_SUBJECT, body, \
                         settings.FEEDBACK_RESPONSE_EMAIL, [email], headers=headers, bcc=bcc)
            email.content_subtype = 'html'
            email.send()

    def get_errors(self):
        from django.utils.encoding import force_unicode
        output = {}
        for key, value in self.errors.items():
            output[key] = '/n'.join([force_unicode(i) for i in value])
        return output

class EmailFriendForm(forms.Form):
    from_email = forms.EmailField(label='From')
    to_emails = EmailListField(label='To')
    subject = forms.CharField()
    message = forms.CharField(widget=forms.Textarea())

    def send(self):
        subject = self.cleaned_data['subject']
        message = self.cleaned_data['message']
        from_email = self.cleaned_data['from_email']
        to_emails = self.cleaned_data['to_emails']
        send_mail(subject, message, from_email, to_emails)

class ChangeVideoOriginalLanguageForm(forms.Form):
    language_code = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        self.fields['language_code'].choices = language_choices_with_empty()

class CreateSubtitlesFormBase(forms.Form):
    """Base class for forms to create new subtitle languages."""
    subtitle_language_code = forms.ChoiceField(label=_('Subtitle into:'))
    primary_audio_language_code = forms.ChoiceField(
                label=_('This video is in:'),
                help_text=_('Please double check the primary spoken '
                            'language. This step cannot be undone.'))

    def __init__(self, request, data=None):
        super(CreateSubtitlesFormBase, self).__init__(data=data)
        self.request = request
        self.user = request.user
        self.setup_subtitle_language_code()
        self.fields['primary_audio_language_code'].choices = language_choices_with_empty()

    def setup_subtitle_language_code(self):
        if self.user.is_authenticated():
            user_langs = self.user.get_languages()
        else:
            user_langs = get_user_languages_from_request(self.request)
        if not user_langs:
            user_langs = ['en']
        def sort_key(choice):
            code, label = choice
            if code in user_langs:
                return user_langs.index(code)
            else:
                return len(user_langs)
        field = self.fields['subtitle_language_code']
        field.choices = sorted(get_language_choices(), key=sort_key)

    def set_primary_audio_language(self):
        # Sometimes we are passed in a cached video, which can't be saved.
        # Make sure we have one from the DB.
        video = Video.objects.get(pk=self.get_video().pk)
        lang = self.cleaned_data['primary_audio_language_code']
        video.primary_audio_language_code = lang
        video.save()

    def editor_url(self):
        return reverse('subtitles:subtitle-editor', kwargs={
            'video_id': self.get_video().video_id,
            'language_code': self.cleaned_data['subtitle_language_code'],
        })

    def handle_post(self):
        self.set_primary_audio_language()
        return redirect(self.editor_url())

    def get_video(self):
        """Get the video that the user wants to create subtiltes for."""
        raise NotImplementedError()

    def clean(self):
        cleaned_data = super(CreateSubtitlesFormBase, self).clean()
        team_video = self.get_video().get_team_video()
        language_code = cleaned_data.get('subtitle_language_code')
        if (team_video is not None and
            not can_create_and_edit_subtitles(self.user, team_video,
                                              language_code)):
            raise forms.ValidationError("You don't have permissions to "
                                        "edit that video")
        return cleaned_data

class CreateSubtitlesForm(CreateSubtitlesFormBase):
    """Form to create subtitles for pages that display a single video.

    This form is generally put in a modal dialog.  See
    the video page for an example.
    """

    subtitle_language_code = forms.ChoiceField(label=_('Subtitle into:'))

    def __init__(self, request, video, data=None):
        self.video = video
        super(CreateSubtitlesForm, self).__init__(request, data=data)
        if not self.needs_primary_audio_language:
            del self.fields['primary_audio_language_code']

    def setup_subtitle_language_code(self):
        super(CreateSubtitlesForm, self).setup_subtitle_language_code()
        # remove languages that already have subtitles
        current_langs = set(self.video.languages_with_versions())
        field = self.fields['subtitle_language_code']
        field.choices = [choice for choice in field.choices
                         if choice[0] not in current_langs]

    def set_primary_audio_language(self):
        if self.needs_primary_audio_language:
            super(CreateSubtitlesForm, self).set_primary_audio_language()

    @property
    def needs_primary_audio_language(self):
        return not bool(self.video.primary_audio_language_code)

    def get_video(self):
        return self.video

class MultiVideoCreateSubtitlesForm(CreateSubtitlesFormBase):
    """Form to create subtitles for pages that display multiple videos.

    This form is normally used with some javascript that alters the form
    for a specific video.  This is done with a couple special things on the
    <A> tag:
        * Adding both the open-modal and multi-video-create-subtitles classes
        * The multi_video_create_subtitles_data_attrs template filter, which
          fills in a bunch of data attributes

    See the team dashboard page for an example.
    """
    video = forms.ModelChoiceField(queryset=Video.objects.none(),
                                   widget=forms.HiddenInput)

    def __init__(self, request, video_queryset, data=None):
        super(MultiVideoCreateSubtitlesForm, self).__init__(request, data=data)
        self.fields['video'].queryset = video_queryset

    def get_video(self):
        return self.cleaned_data['video']

    def clean(self):
        cleaned_data = super(MultiVideoCreateSubtitlesForm, self).clean()
        video = cleaned_data['video']
        lang_code = cleaned_data['subtitle_language_code']
        if video.subtitle_language(lang_code) is not None:
            lang = video.subtitle_language(lang_code)
            self._errors['subtitle_language_code'] = [
                forms.ValidationError('%s subtitles already created',
                                      params=lang.get_language_code_display())
            ]
            del cleaned_data['subtitle_language_code']
        return cleaned_data
