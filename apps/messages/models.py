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

from django.db import models
from django.core.cache import cache
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils import simplejson as json
from django.db.models.signals import post_save
from django.core.urlresolvers import reverse
from django.utils.html import escape, urlize

from auth.models import CustomUser as User

MESSAGE_MAX_LENGTH = getattr(settings,'MESSAGE_MAX_LENGTH', 1000)

class MessageManager(models.Manager):
    use_for_related_fields = True

    def for_user(self, user):
        return self.get_query_set().filter(user=user).exclude(deleted_for_user=True)

    def for_author(self, user):
        return self.get_query_set().filter(author=user).exclude(deleted_for_author=True)

    def unread(self):
        return self.get_query_set().filter(read=False)

    def bulk_create(self, object_list, **kwargs):
        super(MessageManager, self).bulk_create(object_list, **kwargs)
        for user_id in set(m.user_id for m in object_list):
            User.cache.invalidate_by_pk(user_id)

class Message(models.Model):
    user = models.ForeignKey(User)
    subject = models.CharField(max_length=100, blank=True)
    content = models.TextField(blank=True, max_length=MESSAGE_MAX_LENGTH)
    author = models.ForeignKey(User, blank=True, null=True, related_name='sent_messages')
    read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    deleted_for_user = models.BooleanField(default=False)
    deleted_for_author = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, blank=True, null=True,
            related_name="content_type_set_for_%(class)s")
    object_pk = models.TextField('object ID', blank=True, null=True)
    object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    objects = MessageManager()

    hide_cookie_name = 'hide_new_messages'

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        if self.subject and not u' ' in self.subject:
            return self.subject[:40]+u'...'
        return self.subject or ugettext('[no subject]')

    def get_reply_url(self):
        return '%s?reply=%s' % (reverse('messages:inbox'), self.pk)

    def delete_for_user(self, user):
        if self.user == user:
            self.deleted_for_user = True
            self.save()
        elif self.author == user:
            self.deleted_for_author = True
            self.save()

    def json_data(self):
        data = {
            'id': self.pk,
            'author-avatar': self.author and self.author.small_avatar() or '',
            'author-username': self.author and unicode(self.author) or '',
            'author-id': self.author and self.author.pk or '',
            'user-avatar': self.user and self.user.small_avatar() or '',
            'user-username': self.user and unicode(self.user) or '',
            'user-id': self.user and self.user.pk or '',
            'message-content': self.get_content(),
            'message-subject': self.subject,
            'message-subject-display': unicode(self),
            'is-read': self.read,
            'can-reply': bool(self.author_id)
        }
        if self.object and hasattr(self.object, 'message_json_data'):
            data = self.object.message_json_data(data, self)
        return json.dumps(data)

    def get_content(self):
        content = []

        if self.content:
            content.append(urlize(self.content).replace('\n', '<br />'))
            content.append('\n')

        if self.object and hasattr(self.object, 'render_message'):
            added_content = self.object.render_message(self)
            content.append(added_content)

        return ''.join(content)

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.subject and not self.content and not self.object:
            raise ValidationError(_(u'You should enter subject or message.'))

    def save(self, *args, **kwargs):
        """
        If the receipient (user) has opted out completly of receiving site
        messages we mark the message as read, but still stored in the database
        """
        if not self.user.notify_by_message:
            self.read = True

        if not getattr(settings, "MESSAGES_DISABLED", False):
            super (Message, self).save(*args, **kwargs)
        
    @classmethod
    def on_delete(cls, sender, instance, **kwargs):
        ct = ContentType.objects.get_for_model(sender)
        cls.objects.filter(content_type__pk=ct.pk, object_pk=instance.pk).delete()

