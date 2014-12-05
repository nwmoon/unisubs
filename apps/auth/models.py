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

from django.contrib.auth.models import UserManager, User as BaseUser
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
import urllib
import hashlib
import hmac
import uuid
try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.sha
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.http import urlquote
from django.core.exceptions import MultipleObjectsReturned
from utils.amazon import S3EnabledImageField
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils.hashcompat import sha_constructor
from utils.metrics import Meter
from random import random
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from tastypie.models import ApiKey

from caching import CacheGroup, ModelCacheManager
from utils.tasks import send_templated_email_async

ALL_LANGUAGES = [(val, _(name))for val, name in settings.ALL_LANGUAGES]
EMAIL_CONFIRMATION_DAYS = getattr(settings, 'EMAIL_CONFIRMATION_DAYS', 3)

class AnonymousUserCacheGroup(CacheGroup):
    def __init__(self):
        super(AnonymousUserCacheGroup, self).__init__('user:anon',
                                                      cache_pattern='user')

class CustomUser(BaseUser):
    AUTOPLAY_ON_BROWSER = 1
    AUTOPLAY_ON_LANGUAGES = 2
    DONT_AUTOPLAY = 3
    AUTOPLAY_CHOICES = (
        (AUTOPLAY_ON_BROWSER,
         'Autoplay subtitles based on browser preferred languages'),
        (AUTOPLAY_ON_LANGUAGES, 'Autoplay subtitles in languages I know'),
        (DONT_AUTOPLAY, 'Don\'t autoplay subtitles')
    )
    homepage = models.URLField(blank=True)
    preferred_language = models.CharField(
        max_length=16, choices=ALL_LANGUAGES, blank=True)
    picture = S3EnabledImageField(blank=True, upload_to='pictures/')
    valid_email = models.BooleanField(default=False)

    # if true, items that end on the user activity stream will also be
    # sent as email
    notify_by_email= models.BooleanField(default=True)
    # if true, items that end on the user activity stream will also be
    # sent as a message
    notify_by_message = models.BooleanField(default=True)
    biography = models.TextField('Bio', blank=True)
    autoplay_preferences = models.IntegerField(
        choices=AUTOPLAY_CHOICES, default=AUTOPLAY_ON_BROWSER)
    award_points = models.IntegerField(default=0)
    last_ip = models.IPAddressField(blank=True, null=True)
    # videos witch are related to user. this is for quicker queries
    videos = models.ManyToManyField('videos.Video', blank=True)
    # for some login backends we end up with a full name but not
    # a first name, last name pair.
    full_name = models.CharField(max_length=63, blank=True, default='')
    partner = models.ForeignKey('teams.Partner', blank=True, null=True)
    is_partner = models.BooleanField(default=False)
    pay_rate_code = models.CharField(max_length=3, blank=True, default='')
    can_send_messages = models.BooleanField(default=True)

    objects = UserManager()

    cache = ModelCacheManager(default_cache_pattern='user')

    class Meta:
        verbose_name = 'User'

    def __unicode__(self):
        if not self.is_active:
            return ugettext('Retired user')

        if self.first_name:
            if self.last_name:
                return self.get_full_name()
            else:
                return self.first_name
        if self.full_name:
            return self.full_name
        return self.username

    def save(self, *args, **kwargs):
        send_confirmation = False

        if not self.email:
            self.valid_email = False
        elif self.pk:
            try:
                before_save = self.__class__._default_manager.get(pk=self.pk)
                send_confirmation = before_save.email != self.email
            except models.ObjectDoesNotExist:
                send_confirmation = True
        elif self.email:
            send_confirmation = True

        if send_confirmation:
            self.valid_email = False

        send_email_confirmation = kwargs.pop('send_email_confirmation', True)
        super(CustomUser, self).save(*args, **kwargs)

        if send_confirmation and send_email_confirmation:
            EmailConfirmation.objects.send_confirmation(self)

    def unread_messages(self, hidden_meassage_id=None):
        from messages.models import Message

        qs = Message.objects.for_user(self).filter(read=False)

        try:
            if hidden_meassage_id:
                qs = qs.filter(pk__gt=hidden_meassage_id)
        except (ValueError, TypeError):
            pass

        return qs

    def unread_messages_count(self, hidden_meassage_id=None):
        return self.unread_messages(hidden_meassage_id).count()

    @classmethod
    def video_followers_change_handler(cls, sender, instance, action, reverse, model, pk_set, **kwargs):
        from videos.models import SubtitleLanguage

        if reverse and action == 'post_add':
            #instance is User
            for video_pk in pk_set:
                cls.videos.through.objects.get_or_create(video__pk=video_pk, customuser=instance, defaults={'video_id': video_pk})
        elif reverse and action == 'post_remove':
            #instance is User
            for video_pk in pk_set:
                if not SubtitleLanguage.objects.filter(followers=instance, video__pk=video_pk).exists():
                    instance.videos.remove(video_pk)
        elif not reverse and action == 'post_add':
            #instance is Video
            for user_pk in pk_set:
                cls.videos.through.objects.get_or_create(video=instance, customuser__pk=user_pk, defaults={'customuser_id': user_pk})
        elif not reverse and action == 'post_remove':
            #instance is Video
            for user_pk in pk_set:
                if not SubtitleLanguage.objects.filter(followers__pk=user_pk, video=instance).exists():
                    instance.customuser_set.remove(user_pk)
        elif reverse and action == 'post_clear':
            #instance is User
            cls.videos.through.objects.filter(customuser=instance) \
                .exclude(video__subtitlelanguage__followers=instance).delete()
        elif not reverse and action == 'post_clear':
            #instance is Video
            cls.videos.through.objects.filter(video=instance) \
                .exclude(customuser__followed_languages__video=instance).delete()

    @classmethod
    def sl_followers_change_handler(cls, sender, instance, action, reverse, model, pk_set, **kwargs):
        from videos.models import Video, SubtitleLanguage

        if reverse and action == 'post_add':
            #instance is User
            for sl_pk in pk_set:
                sl = SubtitleLanguage.objects.get(pk=sl_pk)
                cls.videos.through.objects.get_or_create(video=sl.video, customuser=instance)
        elif reverse and action == 'post_remove':
            #instance is User
            for sl_pk in pk_set:
                if not Video.objects.filter(followers=instance, subtitlelanguage__pk=sl_pk).exists():
                    sl = SubtitleLanguage.objects.get(pk=sl_pk)
                    instance.videos.remove(sl.video)
        elif not reverse and action == 'post_add':
            #instance is SubtitleLanguage
            for user_pk in pk_set:
                cls.videos.through.objects.get_or_create(video=instance.video, customuser__pk=user_pk, defaults={'customuser_id': user_pk})
        elif not reverse and action == 'post_remove':
            #instance is SubtitleLanguage
            for user_pk in pk_set:
                if not Video.objects.filter(followers__pk=user_pk, subtitlelanguage=instance).exists():
                    instance.video.customuser_set.remove(user_pk)
        elif reverse and action == 'post_clear':
            #instance is User
            cls.videos.through.objects.filter(customuser=instance) \
                .exclude(video__subtitlelanguage__followers=instance).delete()
        elif not reverse and action == 'post_clear':
            #instance is SubtitleLanguage
            cls.videos.through.objects.filter(video=instance) \
                .exclude(customuser__followed_languages__video=instance.video).delete()

    def get_languages(self):
        """
        Just to control this query
        """
        return self.cache.get_or_calc("languages", self.calc_languages)

    def calc_languages(self):
        return list(self.userlanguage_set.values_list('language', flat=True))

    def speaks_language(self, language_code):
        return language_code in [l.language for l in self.get_languages()]

    def is_team_manager(self):
        cached_value = self.cache.get('is-manager')
        if cached_value is not None:
            return cached_value
        is_manager = self.managed_teams().exists()
        self.cache.set('is-manager', is_manager)
        return is_manager

    def managed_teams(self, include_manager=True):
        from teams.models import TeamMember
        possible_roles = [TeamMember.ROLE_OWNER, TeamMember.ROLE_ADMIN]
        if include_manager:
            possible_roles.append(TeamMember.ROLE_MANAGER)
        return self.teams.filter(members__role__in=possible_roles)

    def messageable_teams(self):
        from teams.models import Team
        from teams.permissions import can_message_all_members

        teams = self.teams.all()
        messageable_team_ids = [t.id for t in teams if can_message_all_members(t, self)]

        partners = self.managed_partners.all()
        teams = [list(p.teams.all()) for p in partners]
        partner_teams_ids = [team.id for qs in teams for team in qs]

        messageable_team_ids = messageable_team_ids + partner_teams_ids
        return Team.objects.filter(id__in=messageable_team_ids)

    def open_tasks(self):
        from teams.models import Task
        return Task.objects.incomplete().filter(assignee=self)

    def _get_gravatar(self, size):
        url = "http://www.gravatar.com/avatar/" + hashlib.md5(self.email.lower().encode('utf-8')).hexdigest() + "?"
        url += urllib.urlencode({'d': 'mm', 's':str(size)})
        return url

    def _get_avatar_by_size(self, size):
        if self.picture:
            return self.picture.thumb_url(size, size)
        else:
            return self._get_gravatar(size)
    def avatar(self):
        return self._get_avatar_by_size(100)

    def small_avatar(self):
        return self._get_avatar_by_size(50)

    @models.permalink
    def get_absolute_url(self):
        return ('profiles:profile', [urlquote(self.username)])

    @property
    def language(self):
        return self.get_preferred_language_display()

    def guess_best_lang(self, request=None):

        if self.preferred_language:
            return self.preferred_language

        user_languages = list(self.userlanguage_set.all())
        if user_languages:
            return user_languages[0].language

        from utils.translation import get_user_languages_from_request

        if request:
            languages = get_user_languages_from_request(request)
            if languages:
                return languages[0]

        return 'en'

    def guess_is_rtl(self, request=None):
        from utils.translation import is_rtl
        return is_rtl(self.guess_best_lang(request))

    @models.permalink
    def profile_url(self):
        return ('profiles:profile', [self.pk])

    def hash_for_video(self, video_id):
        return hashlib.sha224(settings.SECRET_KEY+str(self.pk)+video_id).hexdigest()

    @classmethod
    def get_anonymous(cls):
        user, created = cls.objects.get_or_create(
            pk=settings.ANONYMOUS_USER_ID,
            defaults={'username': 'anonymous'})
        return user

    @property
    def is_anonymous(self):
        return self.pk == settings.ANONYMOUS_USER_ID

    def get_api_key(self):
        return ApiKey.objects.get_or_create(user=self)[0].key

def create_custom_user(sender, instance, created, **kwargs):
    if created:
        values = {}
        for field in sender._meta.local_fields:
            values[field.attname] = getattr(instance, field.attname)
        user = CustomUser(**values)
        user.save()

post_save.connect(create_custom_user, BaseUser)

class Awards(models.Model):
    COMMENT = 1
    START_SUBTITLES = 2
    START_TRANSLATION = 3
    EDIT_SUBTITLES = 4
    EDIT_TRANSLATION = 5
    RATING = 6
    TYPE_CHOICES = (
        (COMMENT, _(u'Add comment')),
        (START_SUBTITLES, _(u'Start subtitles')),
        (START_TRANSLATION, _(u'Start translation')),
        (EDIT_SUBTITLES, _(u'Edit subtitles')),
        (EDIT_TRANSLATION, _(u'Edit translation'))
    )
    points = models.IntegerField()
    type = models.IntegerField(choices=TYPE_CHOICES)
    user = models.ForeignKey(CustomUser, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def _set_points(self):
        if self.type == self.COMMENT:
            self.points = 10
        elif self.type == self.START_SUBTITLES:
            self.points = 100
        elif self.type == self.START_TRANSLATION:
            self.points = 100
        elif self.type == self.EDIT_SUBTITLES:
            self.points = 50
        elif self.type == self.EDIT_TRANSLATION:
            self.points = 50
        else:
            self.points = 0

    def save(self, *args, **kwrags):
        self.points or self._set_points()
        if not self.pk:
            CustomUser.objects.filter(pk=self.user.pk).update(award_points=models.F('award_points')+self.points)
        return super(Awards, self).save(*args, **kwrags)

    @classmethod
    def on_comment_save(cls, sender, instance, created, **kwargs):
        if created:
            try:
                cls.objects.get_or_create(user=instance.user, type = cls.COMMENT)
            except MultipleObjectsReturned:
                pass

    @classmethod
    def on_subtitle_version_save(cls, sender, instance, created, timestamp=None, **kwargs):
        if not instance.user:
            return

        if created and instance.version_no == 0:
            if instance.language.is_original:
                type = cls.START_SUBTITLES
            else:
                type = cls.START_TRANSLATION
        else:
            if instance.language.is_original:
                type = cls.EDIT_SUBTITLES
            else:
                type = cls.EDIT_TRANSLATION
        try:
            cls.objects.get_or_create(user=instance.user, type=type)
        except MultipleObjectsReturned:
            pass

class UserLanguage(models.Model):
    PROFICIENCY_CHOICES = (
        (1, _('understand enough')),
        (2, _('understand 99%')),
        (3, _('write like a native')),
    )
    user = models.ForeignKey(CustomUser)
    language = models.CharField(max_length=16, choices=ALL_LANGUAGES, verbose_name='languages')
    proficiency = models.IntegerField(choices=PROFICIENCY_CHOICES, default=1)
    follow_requests = models.BooleanField(verbose_name=_('follow requests in language'))

    class Meta:
        unique_together = ['user', 'language']

    def save(self, *args, **kwargs):
        super(UserLanguage, self).save(*args, **kwargs)
        cache.delete('user_languages_%s' % self.user_id)

    def delete(self, *args, **kwargs):
        cache.delete('user_languages_%s' % self.user_id)
        return super(UserLanguage, self).delete(*args, **kwargs)

class Announcement(models.Model):
    content = models.CharField(max_length=500)
    created = models.DateTimeField(help_text=_(u'This is date when start to display announcement. And only the last will be displayed.'))
    hidden = models.BooleanField(default=False)

    cache_key = 'last_accouncement'
    hide_cookie_name = 'hide_accouncement'
    cookie_date_format = '%d/%m/%Y %H:%M:%S'

    class Meta:
        ordering = ['-created']

    @classmethod
    def clear_cache(cls):
        cache.delete(cls.cache_key)

    def save(self, *args, **kwargs):
        super(Announcement, self).save(*args, **kwargs)
        self.clear_cache()

    def delete(self, *args, **kwargs):
        return super(Announcement, self).delete(*args, **kwargs)
        self.clear_cache()

    @classmethod
    def last(cls, hidden_date=None):
        last = cache.get(cls.cache_key)
        if last == 0:
            return None

        if last is None:
            try:
                qs = cls.objects.filter(created__lte=datetime.today()) \
                    .filter(hidden=False)
                last = qs[0:1].get()
            except cls.DoesNotExist:
                last = 0
            cache.set(cls.cache_key, last, 60*60)

        if hidden_date and last and last.created < hidden_date:
            return None

        return last

class EmailConfirmationManager(models.Manager):

    def confirm_email(self, confirmation_key):
        try:
            confirmation = self.get(confirmation_key=confirmation_key)
        except self.model.DoesNotExist:
            return None
        if not confirmation.key_expired():
            from messages import tasks as notifier
            user = confirmation.user
            user.valid_email = True
            user.save()
            notifier.email_confirmed.delay(user.pk)
            return user

    def send_confirmation(self, user):
        assert user.email
        from messages.models import Message

        self.filter(user=user).delete()

        salt = sha_constructor(str(random())+settings.SECRET_KEY).hexdigest()[:5]
        confirmation_key = sha_constructor(salt + user.email.encode('utf-8')).hexdigest()
        try:
            current_site = Site.objects.get_current()
        except Site.DoesNotExist:
            return
        path = reverse("auth:confirm_email", args=[confirmation_key])
        activate_url = u"http://%s%s" % (unicode(current_site.domain), path)
        context = {
            "user": user,
            "activate_url": activate_url,
            "current_site": current_site,
            "confirmation_key": confirmation_key,
        }
        subject = u'Please confirm your email address for %s' % current_site.name
        Meter('templated-emails-sent-by-type.email-address-confirmation').inc()
        send_templated_email_async(user, subject, "messages/email/email-confirmation.html", context)
        return self.create(
            user=user,
            sent=datetime.now(),
            confirmation_key=confirmation_key)

    def delete_expired_confirmations(self):
        d = datetime.now() - timedelta(days=EMAIL_CONFIRMATION_DAYS)
        self.filter(sent__lt=d).delete()

class EmailConfirmation(models.Model):

    user = models.ForeignKey(CustomUser)
    sent = models.DateTimeField()
    confirmation_key = models.CharField(max_length=40)

    objects = EmailConfirmationManager()

    def __unicode__(self):
        return u"confirmation for %s" % self.user.email

    class Meta:
        verbose_name = _("e-mail confirmation")
        verbose_name_plural = _("e-mail confirmations")

    def key_expired(self):
        expiration_date = self.sent + timedelta(days=EMAIL_CONFIRMATION_DAYS)
        return expiration_date <= datetime.now()
    key_expired.boolean = True

class LoginTokenManager(models.Manager):
    def get_expired(self):
        expires_in = datetime.now() - LoginToken.EXPIRES_IN
        return self.filter(created__lt=expires_in)

    def generate_token(self, user):
        new_uuid = uuid.uuid4()
        return hmac.new("%s%s" % (user.pk, str(new_uuid)), digestmod=sha1).hexdigest()

    def for_user(self, user, updates=True):
        try:
           lt = self.get(user=user)
           if updates:
               lt.token = self.generate_token(user)
               lt.created = datetime.now()
               lt.save()
        except LoginToken.DoesNotExist:
            lt = self.create(user=user, token=self.generate_token(user))
        return lt

class LoginToken(models.Model):
    """
    Links a user account to a secret, this allows a user to be logged in
    just by clicking on a URL. Mostly 3rd parties need this when creating
    content on a user's behalf and then redirecting them to our website.
    The url should expire, just to avoid the security hazard of having those
    lying around indefinitely.

    When creating new instances, client code should use
    LoginToken.objects.get_for_user(user)
    This avoids breaking unique constrainst and badly formed tokens.
    """

    EXPIRES_IN = timedelta(minutes=120) # minutes
    user = models.OneToOneField(CustomUser, related_name="login_token")
    token = models.CharField(max_length=40, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = LoginTokenManager()

    @property
    def is_expired(self):
        return self.created + LoginToken.EXPIRES_IN <  datetime.now()

    def __unicode__(self):
        return u"LoginToken for %s" %(self.user)
