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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.forms import CharField
from django.test import TestCase
from nose.tools import *
from urllib import quote_plus
import mock

from externalsites import forms
from externalsites import models
from videos.models import VideoFeed
from utils import test_utils
from utils.factories import *

class AccountFormTest(TestCase):
    # Test the base AccountForm class.
    class TestAccountForm(forms.AccountForm):
        class Meta:
            model = models.KalturaAccount
            fields = ['partner_id', 'secret']

    def make_valid_data(self):
        return {
            'enabled': True,
            'partner_id': 'abc',
            'secret': 'def'
        }

    def test_disabled_is_always_valid(self):
        team = TeamFactory()
        form = self.TestAccountForm(team, {})
        # since enabled is not present in the data, we ignore the fact that
        # required fields are not present.
        assert_true(form.is_valid())
        assert_equal(form.errors, {})

    def test_enabled_initial_value(self):
        # enabled should have its initial value True if there is an account
        team = TeamFactory()
        form = self.TestAccountForm(team)
        assert_false(form.fields['enabled'].initial)

        account = KalturaAccountFactory(team=team)
        form = self.TestAccountForm(team)
        assert_true(form.fields['enabled'].initial)

    def test_lookup_instance(self):
        # we should lookup our account during form creating and set the
        # instance object from that
        team = TeamFactory()
        form = self.TestAccountForm(team)
        assert_equal(form.instance.pk, None)

        account = KalturaAccountFactory(team=team)
        form = self.TestAccountForm(team)
        assert_equal(form.instance, account)

    def test_disabled_save_deletes_instance(self):
        # if enabled is not checked, then the save() method should delete the
        # instance object
        team = TeamFactory()
        account = KalturaAccountFactory(team=team)
        form = self.TestAccountForm(team, data={})
        # enabled is not present, so save() should delete the account
        form.save()
        assert_equal(models.KalturaAccount.objects.count(), 0)
        # try re-submitting the form.  Check that we don't throw an exception
        # when there is no object to delete
        form = self.TestAccountForm(team, data={})
        form.save()

    def test_save_with_team(self):
        team = TeamFactory()
        form = self.TestAccountForm(team, self.make_valid_data())
        assert_true(form.is_valid())
        account = form.save()
        assert_equal(account.team, team)
        assert_equal(account.user, None)

    def test_save_with_user(self):
        user = UserFactory()
        form = self.TestAccountForm(user, self.make_valid_data())
        assert_true(form.is_valid())
        account = form.save()
        assert_equal(account.user, user)
        assert_equal(account.team, None)

class BrightcoveFormTest(TestCase):
    def setUp(self):
        self.team = TeamFactory()
        self.publisher_id = '123'
        self.player_id = '456'
        self.write_token = '789'

    def test_no_feed(self):
        form = forms.BrightcoveAccountForm(self.team, {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
        })
        assert_true(form.is_valid(), form.errors.as_text())
        account = form.save()
        self.assertEquals(account.publisher_id, self.publisher_id)
        self.assertEquals(account.write_token, self.write_token)
        self.assertEquals(account.team, self.team)
        self.assertEquals(account.import_feed, None)

    def test_disable_deletes_account(self):
        # test enabled being false when we have an account.  In this case
        # save() should delete the account
        account = BrightcoveAccountFactory(team=self.team)
        assert_equal(models.BrightcoveAccount.objects.count(), 1)
        form = forms.BrightcoveAccountForm(self.team, { })
        assert_true(form.is_valid(), form.errors.as_text())
        form.save()
        assert_equal(models.BrightcoveAccount.objects.count(), 0)

    def test_disable_no_account(self):
        # test enabled being false when there's no account to delete.  In this
        # case save() should be a no-op
        form = forms.BrightcoveAccountForm(self.team, { })
        assert_true(form.is_valid(), form.errors.as_text())
        form.save()

    def feed_url(self, *tags):
        if tags:
            return ('http://link.brightcove.com'
                    '/services/mrss/player%s/%s/tags/%s') % (
                        self.player_id, self.publisher_id,
                        '/'.join(quote_plus(t) for t in tags))
        else:
            return ('http://link.brightcove.com'
                    '/services/mrss/player%s/%s/new') % (
                        self.player_id, self.publisher_id,
                    )

    def test_feed_all_new(self):
        form = forms.BrightcoveAccountForm(self.team, {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
            'feed_enabled': '1',
            'player_id': self.player_id,
            'feed_type': forms.BrightcoveAccountForm.FEED_ALL_NEW,
            'feed_tags': '',
        })
        self.assert_(form.is_valid(), form.errors.as_text())
        account = form.save()
        self.assertNotEquals(account.import_feed, None)
        self.assertEquals(account.import_feed.url, self.feed_url())
        test_utils.import_videos_from_feed.delay.assert_called_with(
            account.import_feed.id)

    def test_feed_with_tags(self):
        # feed tags should be a comma separated list of tags.  If there are
        # spaces inside the tag we should preserve them
        form = forms.BrightcoveAccountForm(self.team, {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
            'feed_enabled': '1',
            'player_id': self.player_id,
            'feed_type': forms.BrightcoveAccountForm.FEED_WITH_TAGS,
            'feed_tags': 'cats, cute pets,dogs  ',
        })
        self.assert_(form.is_valid(), form.errors.as_text())
        account = form.save()
        self.assertNotEquals(account.import_feed, None)
        self.assertEquals(account.import_feed.url,
                          self.feed_url('cats', 'cute pets', 'dogs'))
        test_utils.import_videos_from_feed.delay.assert_called_with(
            account.import_feed.id)

    def test_feed_exists(self):
        # test that we set initial values for the feed inputs for accounts
        # with feeds created.

        # create an account with an import feed
        account = models.BrightcoveAccount.objects.create(
            team=self.team, publisher_id=self.publisher_id,
            write_token=self.write_token)
        account.make_feed(self.player_id)
        form = forms.BrightcoveAccountForm(self.team)
        self.assertEquals(form.fields['player_id'].initial, self.player_id)
        self.assertEquals(form.fields['feed_type'].initial,
                          forms.BrightcoveAccountForm.FEED_ALL_NEW)
        self.assertEquals(form.fields['feed_tags'].initial, '')

        # try again when using tags
        account.make_feed(self.player_id, ['cats', 'dogs'])
        form = forms.BrightcoveAccountForm(self.team)
        self.assertEquals(form.fields['player_id'].initial, self.player_id)
        self.assertEquals(form.fields['feed_type'].initial,
                          forms.BrightcoveAccountForm.FEED_WITH_TAGS)
        self.assertEquals(form.fields['feed_tags'].initial, 'cats, dogs')

    def test_change_feed(self):
        # test saving a form when we already have an import feed

        # create an account with an import feed
        account = models.BrightcoveAccount.objects.create(
            team=self.team, publisher_id=self.publisher_id,
            write_token=self.write_token)
        account.make_feed(self.player_id, ['cats'])
        first_feed = account.import_feed
        # test saving a form with different feed tags.  We should update the
        # feed URL, but not make a new feed object
        data = {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
            'feed_enabled': '1',
            'player_id': self.player_id,
            'feed_type': forms.BrightcoveAccountForm.FEED_WITH_TAGS,
            'feed_tags': 'cats, dogs',
        }
        form = forms.BrightcoveAccountForm(self.team, data)
        account = form.save()
        self.assertEquals(account.import_feed.id, first_feed.id)
        test_utils.import_videos_from_feed.delay.assert_called_with(
            account.import_feed.id)
        # test saving the form with the same tags.  We should import videos
        # for this save
        form = forms.BrightcoveAccountForm(self.team, data)
        account = form.save()
        self.assertEquals(account.import_feed.id, first_feed.id)
        self.assertEquals(test_utils.import_videos_from_feed.delay.call_count,
                          1)

    def test_player_id_required_with_feed(self):
        form = forms.BrightcoveAccountForm(self.team, {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
            'feed_enabled': '1',
            'player_id': '',
            'feed_type': forms.BrightcoveAccountForm.FEED_ALL_NEW,
            'feed_tags': '',
        })
        self.assertEquals(form.is_valid(), False)
        self.assertEquals(form.errors.keys(), ['player_id'])

    def test_tags_required_with_feed_with_tags(self):
        form = forms.BrightcoveAccountForm(self.team, {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
            'feed_enabled': '1',
            'player_id': self.player_id,
            'feed_type': forms.BrightcoveAccountForm.FEED_WITH_TAGS,
            'feed_tags': '',
        })
        self.assertEquals(form.is_valid(), False)
        self.assertEquals(form.errors.keys(), ['feed_tags'])

    def test_remove_feed(self):
        account = models.BrightcoveAccount.objects.create(
            team=self.team, publisher_id=self.publisher_id,
            write_token=self.write_token)
        account.make_feed(self.player_id)
        old_import_feed = account.import_feed

        form = forms.BrightcoveAccountForm(self.team, {
            'enabled': '1',
            'publisher_id': self.publisher_id,
            'write_token': self.write_token,
            'player_id': self.player_id,
            'feed_type': forms.BrightcoveAccountForm.FEED_ALL_NEW,
            'feed_tags': '',
        })
        account = form.save()
        self.assertEquals(account.import_feed, None)
        self.assert_(not VideoFeed.objects.filter(id=old_import_feed.id))

class AddYoutubeAccountFormTest(TestCase):
    def test_add_with_team(self):
        team = TeamFactory()
        form = forms.AddYoutubeAccountForm(team, data={
            'add_button': '1',
        })
        assert_true(form.is_valid())
        # save doesn't do anything, but call it just to make sure it doesn't
        # throw an exception
        form.save()
        path = reverse('externalsites:youtube-add-account')
        assert_equal(form.redirect_path(),
                     '%s?team_slug=%s' % (path, team.slug))

    def test_add_with_user(self):
        user = UserFactory()
        form = forms.AddYoutubeAccountForm(user, data={
            'add_button': '1',
        })
        assert_true(form.is_valid())
        # save doesn't do anything, but call it just to make sure it doesn't
        # throw an exception
        form.save()
        path = reverse('externalsites:youtube-add-account')
        assert_equal(form.redirect_path(),
                     '%s?username=%s' % (path, user.username))

    def test_no_add(self):
        team = TeamFactory()
        form = forms.AddYoutubeAccountForm(team, data={})
        assert_true(form.is_valid())
        assert_equal(form.redirect_path(), None)

class YouTubeAccountTest(TestCase):
    def test_remove(self):
        user = UserFactory()
        team = TeamFactory(admin=user)
        account = YouTubeAccountFactory(team=team)
        assert_equal(models.YouTubeAccount.objects.count(), 1)
        form = forms.YoutubeAccountForm(user, account, {
            'remove_button': True,
        })
        form.save()
        assert_equal(models.YouTubeAccount.objects.count(), 0)

    def test_no_remove(self):
        user = UserFactory()
        team = TeamFactory(admin=user)
        account = YouTubeAccountFactory(team=team)
        assert_equal(models.YouTubeAccount.objects.count(), 1)
        form = forms.YoutubeAccountForm(user, account, {})
        form.save()
        assert_equal(models.YouTubeAccount.objects.count(), 1)

    def test_sync_teams(self):
        # test the sync_teams field
        user = UserFactory()
        account_team = TeamFactory(admin=user, name='Account Team')
        account = YouTubeAccountFactory(team=account_team)
        correct_choices = []
        correct_initial = []
        # make some random teams that the user isn't an admin for and aren't
        # currently synced.  We shouldn't include these.
        for i in xrange(5):
            TeamFactory(name='Other team %s' % i)
        # by default, the choices sync_teams should include all teams the user
        # is an admin for
        for i in xrange(5):
            team = TeamFactory(admin=user, name='Related team %s' % i)
            correct_choices.append((team.id, unicode(team)))
            # add one of the teams to the sync_teams set so that we check that
            # the initial value is correct.
            if i == 0:
                account.sync_teams.add(team)
                correct_initial.append(team.id)
        # it also should include teams that are currently synced, but the user
        # isn't an admin for
        team = TeamFactory(name='Synced team')
        account.sync_teams.add(team)
        correct_choices.append((team.id, unicode(team)))
        correct_initial.append(team.id)
        form = forms.YoutubeAccountForm(user, account)
        assert_items_equal(form['sync_teams'].field.choices, correct_choices)
        assert_items_equal(form['sync_teams'].field.initial, correct_initial)

    def test_save_sync_teams(self):
        user = UserFactory()
        account_team = TeamFactory(admin=user)
        account = YouTubeAccountFactory(team=account_team)
        teams = [TeamFactory(admin=user) for i in xrange(5)]
        account.sync_teams = teams[:2]

        form = forms.YoutubeAccountForm(user, account, {
            'sync_teams': [t.id for t in teams[3:]],
        })
        form.save()
        account = models.YouTubeAccount.objects.get(id=account.id)
        assert_items_equal(account.sync_teams.all(), teams[3:])

class AccountFormsetTest(TestCase):
    def test_forms(self):
        user = UserFactory()
        team = TeamFactory(admin=user)
        account = YouTubeAccountFactory(team=team, id=1)
        account2 = YouTubeAccountFactory(team=team, id=2)
        formset = forms.AccountFormset(user, team)
        assert_equal(set(formset.keys()), set([
            'brightcove',
            'kaltura',
            'add_youtube',
            'youtube_1',
            'youtube_2',
        ]))
        assert_equal(type(formset['brightcove']), forms.BrightcoveAccountForm)
        assert_equal(type(formset['kaltura']), forms.KalturaAccountForm)
        assert_equal(type(formset['add_youtube']), forms.AddYoutubeAccountForm)
        assert_equal(type(formset['youtube_1']),
                     forms.YoutubeAccountForm)
        assert_equal(type(formset['youtube_2']),
                     forms.YoutubeAccountForm)

        assert_equal(set(formset.youtube_forms()),
                     set([formset['youtube_1'], formset['youtube_2']]))

