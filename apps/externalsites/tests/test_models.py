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

from django.test import TestCase
from django.core.exceptions import PermissionDenied
from gdata.client import RequestError
from nose.tools import *

from externalsites.exceptions import YouTubeAccountExistsError
from externalsites.models import (BrightcoveAccount, YouTubeAccount,
                                  get_sync_accounts, account_models,
                                  SyncHistory, SyncedSubtitleVersion)
from subtitles import pipeline
from teams.models import TeamMember
from videos.models import VideoFeed
from utils import test_utils
from utils.factories import *

class GetSyncAccountTest(TestCase):
    def check_get_sync_accounts(self, video, account):
        self.assertEquals(get_sync_accounts(video), [
            (account, video.get_primary_videourl_obj())
        ])

    def test_team_account(self):
        video = BrightcoveVideoFactory()
        team_video = TeamVideoFactory(video=video)
        account = BrightcoveAccountFactory(team=team_video.team)
        self.check_get_sync_accounts(video, account)

    def test_user_account(self):
        user = UserFactory()
        video = BrightcoveVideoFactory(user=user)
        account = BrightcoveAccountFactory(user=user)
        self.check_get_sync_accounts(video, account)

    def test_is_for_video_url(self):
        user = UserFactory()
        video = BrightcoveVideoFactory(user=user)
        account = BrightcoveAccountFactory(user=user)
        self.assertTrue(account.should_sync_video_url(
            video, video.get_primary_videourl_obj()))

        video2 = YouTubeVideoFactory(user=user)
        self.assertFalse(account.should_sync_video_url(
            video2, video2.get_primary_videourl_obj()))

class YouTubeGetSyncAccountTestBase(TestCase):
    def check_get_sync_account_matches_account(self, video):
        video_url = video.get_primary_videourl_obj()
        self.assertEquals(get_sync_accounts(video), [
            (self.account, video_url),
        ])
        # also check should_sync_video_url
        self.assertTrue(self.account.should_sync_video_url(video, video_url))

    def check_get_sync_account_doesnt_match_account(self, video):
        video_url = video.get_primary_videourl_obj()
        self.assertEquals(get_sync_accounts(video), [])
        # also check should_sync_video_url
        self.assertFalse(self.account.should_sync_video_url(video, video_url))

class YouTubeTeamGetSyncAccountTest(YouTubeGetSyncAccountTestBase):
    # Test get_sync_accounts with team YouTube accounts
    #
    # In this case, get_sync_accounts should find accounts that:
    #   - match the channel id
    #   - are owned by the same team that the team video is for, or are owned
    #   by a team in the sync_teams set

    def setUp(self):
        self.team = TeamFactory()
        self.account = YouTubeAccountFactory(channel_id='channel',
                                             team=self.team)

    def make_youtube_team_video(self, team, channel_id):
        video = YouTubeVideoFactory(channel_id=channel_id)
        TeamVideoFactory(team=team, video=video)
        return video

    def test_everything_matches(self):
        video = self.make_youtube_team_video(self.team,
                                             self.account.channel_id)
        self.check_get_sync_account_matches_account(video)

    def test_wrong_channel_id(self):
        video = self.make_youtube_team_video(self.team, 'other-channel-id')
        self.check_get_sync_account_doesnt_match_account(video)

    def test_wrong_team(self):
        other_team = TeamFactory()
        video = self.make_youtube_team_video(other_team,
                                             self.account.channel_id)
        self.check_get_sync_account_doesnt_match_account(video)

    def test_non_team_video(self):
        video = YouTubeVideoFactory(channel_id=self.account.channel_id)
        self.check_get_sync_account_doesnt_match_account(video)

    def test_sync_teams(self):
        other_team = TeamFactory()
        other_team2 = TeamFactory()
        self.account.sync_teams = [other_team, other_team2]

        video = self.make_youtube_team_video(other_team,
                                             self.account.channel_id)
        self.check_get_sync_account_matches_account(video)

        video = self.make_youtube_team_video(other_team2,
                                             self.account.channel_id)
        self.check_get_sync_account_matches_account(video)

        video = self.make_youtube_team_video(self.team,
                                             self.account.channel_id)
        self.check_get_sync_account_matches_account(video)

    def test_1686(self):
        # Test the corner case from 1686 -- we're syncing another team's
        # videos but the the channel id doesn't match

        other_team = TeamFactory()
        self.account.sync_teams = [other_team]
        video = self.make_youtube_team_video(other_team, 'other-channel')
        self.check_get_sync_account_doesnt_match_account(video)

class YouTubeUserGetSyncAccountTest(YouTubeGetSyncAccountTestBase):
    # Test get_sync_accounts with user YouTube accounts
    #
    # In this case, get_sync_accounts should find accounts that match the
    # channel id.  It doesn't matter what user owns the video, or what team
    # the video is a part of.

    def setUp(self):
        self.user = UserFactory()
        self.account = YouTubeAccountFactory(channel_id='channel',
                                             user=self.user)

    def check_normal_video_match(self):
        video = YouTubeVideoFactory(user=self.user,
                                    channel_id=self.account.channel_id)
        self.check_get_sync_account_matches_account(video)

    def check_video_not_owned_by_user(self):
        video = YouTubeVideoFactory(user=UserFactory(),
                                    channel_id=self.account.channel_id)
        self.check_get_sync_account_matches_account(video)

    def check_team_video(self):
        video = YouTubeVideoFactory(user=UserFactory(),
                                    channel_id=self.account.channel_id)
        TeamVideoFactory(video=video)
        self.check_get_sync_account_matches_account(video)

    def check_wrong_channel_id(self):
        video = YouTubeVideoFactory(user=self.user,
                                    channel_id='other-channel_id')
        self.check_get_sync_account_doesnt_match_account(video)

class YouTubeSyncTeamsTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        teams = [TeamFactory() for i in xrange(5)]
        for team in teams:
            TeamMemberFactory(user=self.user, team=team,
                              role=TeamMember.ROLE_ADMIN)
        self.team = teams[0]
        self.account = YouTubeAccountFactory(team=self.team)
        self.other_teams = teams[1:]

    def test_set_sync_teams(self):
        self.account.set_sync_teams(self.user, self.other_teams[:2])
        self.assertEquals(set(self.account.sync_teams.all()),
                          set(self.other_teams[:2]))
        # try setting teams again to check removing in addition at adding
        # teams to the set
        self.account.set_sync_teams(self.user, self.other_teams[1:3])
        self.assertEquals(set(self.account.sync_teams.all()),
                          set(self.other_teams[1:3]))

    def test_set_sync_teams_requires_admin(self):
        # set_sync_teams() can only be used to set teams that the user is an
        # admin for
        account_for_other_team = YouTubeAccountFactory(team=TeamFactory())
        self.assertRaises(PermissionDenied,
                          account_for_other_team.set_sync_teams,
                          self.user, self.other_teams)

    def test_set_sync_teams_forbids_own_team(self):
        # set_sync_teams() cant set a team as its own sync team
        self.assertRaises(ValueError, self.account.set_sync_teams,
                          self.user, [self.team])

    def test_set_sync_teams_for_user_account(self):
        # set_sync_teams() can't be called for user accounts
        user_account = YouTubeAccountFactory(user=self.user)
        self.assertRaises(ValueError, user_account.set_sync_teams,
                          self.user, [self.team])


class BrightcoveAccountTest(TestCase):
    def setUp(self):
        self.team = TeamFactory()
        self.account = BrightcoveAccountFactory.create(team=self.team,
                                                       publisher_id='123')
        self.player_id = '456'

    def check_feed(self, feed_url):
        self.assertEquals(self.account.import_feed.url, feed_url)
        self.assertEquals(self.account.import_feed.user, None)
        self.assertEquals(self.account.import_feed.team, self.team)

    def test_make_feed(self):
        self.assertEquals(self.account.import_feed, None)
        self.account.make_feed(self.player_id)
        self.check_feed(
            'http://link.brightcove.com/services/mrss/player456/123/new')
        self.account.make_feed(self.player_id, ['cats', 'dogs'])
        self.check_feed(
            'http://link.brightcove.com/services/mrss/player456/123/tags/cats/dogs')
        # test with chars that need to be quoted
        self.account.make_feed(self.player_id, ['~cats and dogs'])
        self.check_feed(
            'http://link.brightcove.com/services/mrss/player456/123/tags/%7Ecats+and+dogs')

    def test_make_feed_again(self):
        # test calling make feed twice.  We should use the same VideoFeed
        # object and change its URL.
        self.assertEquals(self.account.import_feed, None)
        self.account.make_feed(self.player_id)
        first_import_feed_id = self.account.import_feed.id
        self.account.make_feed(self.player_id, ['cats'])
        self.assertEquals(self.account.import_feed.id, first_import_feed_id)

    def test_remove_feed(self):
        self.account.make_feed(self.player_id)
        self.account.remove_feed()
        self.assertEquals(self.account.import_feed, None)

    def test_feed_info(self):
        self.assertEquals(self.account.feed_info(), None)

        self.account.make_feed(self.player_id)
        self.assertEquals(self.account.feed_info(), (self.player_id, None))

        self.account.make_feed(self.player_id, ['cats', 'dogs'])
        self.assertEquals(self.account.feed_info(),
                          (self.player_id, ('cats', 'dogs')))

    def test_feed_removed_externally(self):
        # test what happens if the feed is deleted not through
        # BrightcoveAccount.remove_feed()
        self.account.make_feed(self.player_id)
        self.account.import_feed.delete()

        account = BrightcoveAccount.objects.get(id=self.account.id)
        self.assertEquals(account.import_feed, None)

class YoutubeAccountTest(TestCase):
    def test_revoke_token_on_delete(self):
        account = YouTubeAccountFactory(user=UserFactory())
        account.delete()
        self.assertEquals(test_utils.youtube_revoke_auth_token.call_count, 1)
        test_utils.youtube_revoke_auth_token.assert_called_with(
            account.oauth_refresh_token)

    def test_create_or_update(self):
        # if there are no other accounts for a channel_id, create_or_update()
        # should create the account and return it
        user = UserFactory()
        auth_info = {
            'username': 'YouTubeUser',
            'channel_id': 'test-channel-id',
            'oauth_refresh_token':
            'test-refresh-token',
        }
        assert_equals(YouTubeAccount.objects.all().count(), 0)
        account = YouTubeAccount.objects.create_or_update(user=user,
                                                          **auth_info)
        assert_equals(YouTubeAccount.objects.all().count(), 1)

        # Now that there is an account, it should update the existing account
        # and throw a YouTubeAccountExistsError
        team = TeamFactory()
        auth_info['oauth_refresh_token'] = 'test-refresh-token2'
        with assert_raises(YouTubeAccountExistsError) as cm:
            YouTubeAccount.objects.create_or_update(team=team, **auth_info)
        assert_equals(cm.exception.other_account, account)
        assert_equals(YouTubeAccount.objects.all().count(), 1)
        account = YouTubeAccount.objects.all().get()
        assert_equals(account.oauth_refresh_token, 'test-refresh-token2')

class SyncRetryTest(TestCase):
    @test_utils.patch_for_test('externalsites.syncing.youtube.update_subtitles')
    def setUp(self, mock_update_subtitles):
        self.mock_update_subtitles = mock_update_subtitles
        self.account = YouTubeAccountFactory(user=UserFactory())
        video = YouTubeVideoFactory()
        self.vurl = video.get_primary_videourl_obj()
        self.version = pipeline.add_subtitles(video, 'en', None)
        self.language = self.version.subtitle_language

    def check_retry_flag(self, error, correct_retry_value):
        self.mock_update_subtitles.side_effect = error
        self.account.update_subtitles(self.vurl, self.language)
        qs = SyncHistory.objects.get_for_language(self.language)
        last_sync_history = qs[0]
        assert_equal(last_sync_history.retry, correct_retry_value)

    def make_quota_error(self):
        error = RequestError('Simulated Quota Error')
        error.status = 403
        error.body = "<?xmlversion='1.0'encoding='UTF-8'?><errors><error><domain>yt:quota</domain><code>too_many_recent_calls</code></error></errors>"
        return error

    def make_non_quota_error(self):
        error = RequestError('Simulated Auth Error')
        error.status = 403
        error.body = "Authentication error"
        return error

    def test_set_retry_on_quota_error(self):
        # If update_subtitles() results in a quota error, we should set the
        # retry flag
        self.check_retry_flag(self.make_quota_error(), True)

    def test_dont_set_retry_on_other_error(self):
        # If update_subtitles() results in a non-quota error, we shouldn't set
        # retry
        self.check_retry_flag(self.make_non_quota_error(), False)

    def test_success_clears_retry(self):
        # If update_subtitles() results in a success, we should clear any
        # retry flags from previous history entries.
        SyncHistory.objects.create_for_error(
            self.make_quota_error(), account=self.account,
            video_url=self.vurl, language=self.language,
            version=self.version, action=SyncHistory.ACTION_UPDATE_SUBTITLES,
            retry=True)
        # simulate update_subtitles() running without error.  We should clear
        # the retry flag from the prevous sync history entry
        assert_true(SyncHistory.objects.filter(retry=True).exists())
        self.mock_update_subtitles.side_effect = None
        self.account.update_subtitles(self.vurl, self.language)
        assert_false(SyncHistory.objects.filter(retry=True).exists())

class YoutubeAccountFeedTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user_account = YouTubeAccountFactory(channel_id='user-channel',
                                                  user=self.user)

        self.team = TeamFactory()
        self.team_account = YouTubeAccountFactory(channel_id='team-channel',
                                                  team=self.team)

    def feed_url(self, account):
        return ('https://gdata.youtube.com/'
                'feeds/api/users/%s/uploads' % account.channel_id)

    def check_create_feed(self, account):
        account.create_feed()
        self.assertEquals(account.import_feed.url, self.feed_url(account))
        self.assertEquals(account.import_feed.user, account.user)
        self.assertEquals(account.import_feed.team, account.team)

    def test_create_feed_for_user(self):
        self.check_create_feed(self.user_account)

    def test_create_feed_for_team(self):
        self.check_create_feed(self.team_account)

    def test_create_feed_twice_raises_error(self):
        self.user_account.create_feed()
        self.assertRaises(ValueError, self.user_account.create_feed)

    def test_existing_feed_for_user(self):
        # if there already is an youtube feed created by the user, we should
        # link it to the youtube account.

        feed = VideoFeedFactory(url=self.feed_url(self.user_account),
                                user=self.user)
        self.user_account.create_feed()
        self.assertEquals(self.user_account.import_feed.pk, feed.pk)

    def test_existing_feed_for_other_user(self):
        # if there already is an youtube feed created by a different user, we
        # should raise an error
        feed = VideoFeedFactory(url=self.feed_url(self.user_account),
                                user=UserFactory())
        self.assertRaises(ValueError, self.user_account.create_feed)

    def test_existing_feed_for_team(self):
        # if there already is an youtube feed created by the team, we should
        # link it to the youtube account.
        feed = VideoFeedFactory(url=self.feed_url(self.team_account),
                                team=self.team)
        self.team_account.create_feed()
        self.assertEquals(self.team_account.import_feed.pk, feed.pk)

    def test_existing_feed_for_other_team(self):
        # if there already is an youtube feed created by a different team, we
        # should raise an error
        feed = VideoFeedFactory(url=self.feed_url(self.team_account),
                                team=TeamFactory())
        self.assertRaises(ValueError, self.team_account.create_feed)

    @test_utils.patch_for_test('videos.tasks.update_video_feed')
    def test_schedule_update_for_new_feed(self, mock_update_video_feed):
        self.user_account.create_feed()
        self.assertEquals(mock_update_video_feed.delay.call_count, 1)
        mock_update_video_feed.delay.assert_called_with(
            self.user_account.import_feed.id)

    @test_utils.patch_for_test('videos.tasks.update_video_feed')
    def test_no_update_for_existing_feeds(self, mock_update_video_feed):
        feed = VideoFeedFactory(url=self.feed_url(self.user_account),
                                user=self.user)
        self.user_account.create_feed()
        self.assertEquals(mock_update_video_feed.delay.call_count, 0)

    def test_delete_feed_on_account_delete(self):
        account = YouTubeAccountFactory(user=UserFactory(),
                                        channel_id='test-channel-id')
        account.create_feed()
        self.assertEqual(VideoFeed.objects.count(), 1)
        account.delete()
        self.assertEqual(VideoFeed.objects.count(), 0)

class DeleteAccountRelatedModelTest(TestCase):
    # Test that we delete our related objects when we delete our account.
    # This test is important because we don't use an actual foreign key in the
    # DB table.
    def setUp(self):
        self.account = YouTubeAccountFactory(user=UserFactory(),
                                        channel_id='test-channel-id')
        self.video = YouTubeVideoFactory()
        self.video_url = self.video.get_primary_videourl_obj()
        self.version = pipeline.add_subtitles(self.video, 'en',
                                              SubtitleSetFactory())
        self.language = self.version.subtitle_language

    def test_synced_subtitle_version(self):
        SyncedSubtitleVersion.objects.set_synced_version(
            self.account, self.video_url, self.language, self.version)
        self.account.delete()
        assert_equal(SyncedSubtitleVersion.objects.all().count(), 0)

    def test_sync_history(self):
        sync_history_values = {
            'account': self.account,
            'video_url': self.video_url,
            'language': self.language,
            'action': SyncHistory.ACTION_UPDATE_SUBTITLES,
            'version': self.version,
        }
        SyncHistory.objects.create_for_error(ValueError(),
                                             **sync_history_values)
        SyncHistory.objects.create_for_success(**sync_history_values)
        self.account.delete()
        assert_equal(SyncHistory.objects.all().count(), 0)
