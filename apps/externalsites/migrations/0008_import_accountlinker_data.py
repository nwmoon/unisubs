# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

VIDEO_TYPE_YOUTUBE = 'Y'

class Migration(DataMigration):
    
    def forwards(self, orm):
        "Write your forwards methods here."

        self.orm = orm

        self.import_account_rows()
        self.link_user_accounts()
        self.link_team_accounts()
        self.link_user_video_feeds()

    def import_account_rows(self):
        """Import rows from the accountlinker_thirdpartyaccount table."""
        exclude_ids = self.find_accounts_with_duplicate_channel_ids()

        # Notes:
        #  - We ignore accountlinker_thirdpartyaccount.type, since we never
        #    created another type than the youtube type
        #  - We make the id value the same for both tables which simplifies
        #    things when we're trying to link the new accounts to users/teams
        #  - For now we set type=owner_id to dummy values.  We will update
        #    them in link_user_accounts() and link_team_accounts()
        db.execute(
            "INSERT INTO externalsites_youtubeaccount "
            "(id, type, owner_id, channel_id, username, oauth_refresh_token) "
            "SELECT id, '', 0, channel_id, username, oauth_refresh_token "
            "FROM accountlinker_thirdpartyaccount tpa "
            "WHERE channel_id <> '' AND id NOT IN (%s)" %
           (','.join(exclude_ids),))

    def find_accounts_with_duplicate_channel_ids(self):
        """We can only import 1 account for a given channel ID

        Normally this is fine, but sometimes users can link their YT accounts
        and their G+ accounts, which results in different usernames, but the
        same channel id.

        This method returns the ids for accounts like this, except the first
        account, so we can exclude them from the migration.
        """
        rv = []
        rows = db.execute(
            'SELECT channel_id, MIN(id) '
            'FROM accountlinker_thirdpartyaccount '
            'WHERE channel_id <> "" '
            'GROUP BY channel_id '
            'HAVING COUNT(channel_id) > 1'
        )
        for channel_id, first_id in rows:
            rows2 = db.execute('SELECT id '
                              'FROM accountlinker_thirdpartyaccount '
                              'WHERE channel_id=%s AND id <> %s',
                              params=[channel_id, first_id])
            rv.extend(str(r[0]) for r in rows2)
        return rv

    def link_user_accounts(self):
        """Lookup third party accounts that were linked to users and update
        the externalsites_youtubeaccount table based on that.
        """

        # Note: the old accountlinker_thirdpartyaccount table could in theory
        # be linked to multiple user objects, although we prevented that from
        # the UI.  For the migration we take one and forget about the rest.
        db.execute("""\
UPDATE externalsites_youtubeaccount
SET type="U",
    owner_id = (SELECT MIN(customuser_id)
                FROM auth_customuser_third_party_accounts
                WHERE thirdpartyaccount_id = externalsites_youtubeaccount.id)
WHERE id IN (SELECT thirdpartyaccount_id
             FROM auth_customuser_third_party_accounts)""")

    def link_user_video_feeds(self):
        YouTubeAccount = self.orm['externalsites.YouTubeAccount']
        VideoFeed = self.orm['videos.VideoFeed']

        for account in YouTubeAccount.objects.filter(type='U'):
            username = account.username.replace(' ', '')
            feed_url = ("https://gdata.youtube.com/"
                        "feeds/api/users/%s/uploads" % username)
            try:
                feed = VideoFeed.objects.filter(
                    url=feed_url, user_id=account.owner_id)[:1].get()
            except VideoFeed.DoesNotExist:
                pass
            else:
                # for some reason we can't just set account.import_feed and
                # account.save().  Use a SQL update statement instead.
                db.execute("UPDATE externalsites_youtubeaccount "
                           "SET import_feed_id = %s "
                           "WHERE id = %s", (feed.id, account.id))

    def link_team_accounts(self):
        """Lookup third party accounts that were linked to teams and update
        the externalsites_youtubeaccount table based on that.
        """

        # Notes:
        #
        #  - We often would link rows in accountlinker_thirdpartyaccount to
        # multiple teams.  To migrate these, we set link the account to 1 of
        # the teams and add the others to sync_teams
        #  - If an account is linked both a user account and a team account,
        #    this code will overwrite the changes made in
        #    link_user_accounts().  This is good because we want the team
        #    account to take precendence.

        db.execute("""\
UPDATE externalsites_youtubeaccount
SET type="T",
    owner_id = (SELECT MIN(team_id)
                FROM teams_team_third_party_accounts
                WHERE thirdpartyaccount_id = externalsites_youtubeaccount.id)
WHERE id IN (SELECT thirdpartyaccount_id
             FROM teams_team_third_party_accounts)""")

        db.execute("""\
INSERT INTO externalsites_youtubeaccount_sync_teams
            (youtubeaccount_id, team_id)
SELECT m2m.thirdpartyaccount_id, m2m.team_id
FROM teams_team_third_party_accounts m2m
JOIN externalsites_youtubeaccount youtubeaccount
    ON m2m.thirdpartyaccount_id = youtubeaccount.id
WHERE m2m.team_id <> youtubeaccount.owner_id""")
    
    def backwards(self, orm):
        "Write your backwards methods here."
    
    models = {
        'auth.customuser': {
            'Meta': {'object_name': 'CustomUser', '_ormbases': ['auth.User']},
            'autoplay_preferences': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'award_points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'biography': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'can_send_messages': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '63', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'is_partner': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'notify_by_email': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'notify_by_message': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Partner']", 'null': 'True', 'blank': 'True'}),
            'pay_rate_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '3', 'blank': 'True'}),
            'picture': ('utils.amazon.fields.S3EnabledImageField', [], {'max_length': '100', 'blank': 'True'}),
            'preferred_language': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'}),
            'valid_email': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'videos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['videos.Video']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 26, 11, 6, 59, 946052)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 26, 11, 6, 59, 945971)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'externalsites.brightcoveaccount': {
            'Meta': {'unique_together': "[('type', 'owner_id')]", 'object_name': 'BrightcoveAccount'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_feed': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['videos.VideoFeed']", 'unique': 'True', 'null': 'True'}),
            'owner_id': ('django.db.models.fields.IntegerField', [], {}),
            'publisher_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'write_token': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'externalsites.creditedvideourl': {
            'Meta': {'object_name': 'CreditedVideoUrl'},
            'video_url': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.VideoUrl']", 'primary_key': 'True'})
        },
        'externalsites.kalturaaccount': {
            'Meta': {'unique_together': "[('type', 'owner_id')]", 'object_name': 'KalturaAccount'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner_id': ('django.db.models.fields.IntegerField', [], {}),
            'partner_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'externalsites.syncedsubtitleversion': {
            'Meta': {'unique_together': "(('account_type', 'account_id', 'video_url', 'language'),)", 'object_name': 'SyncedSubtitleVersion'},
            'account_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'account_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subtitles.SubtitleLanguage']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subtitles.SubtitleVersion']"}),
            'video_url': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.VideoUrl']"})
        },
        'externalsites.synchistory': {
            'Meta': {'object_name': 'SyncHistory'},
            'account_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'account_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'details': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subtitles.SubtitleLanguage']"}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subtitles.SubtitleVersion']", 'null': 'True', 'blank': 'True'}),
            'video_url': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.VideoUrl']"})
        },
        'externalsites.youtubeaccount': {
            'Meta': {'unique_together': "[('type', 'owner_id', 'channel_id')]", 'object_name': 'YouTubeAccount'},
            'sync_teams': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['teams.Team']", 'symmetrical': 'False'}),
            'channel_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_feed': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['videos.VideoFeed']", 'unique': 'True', 'null': 'True'}),
            'oauth_refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner_id': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'subtitles.subtitlelanguage': {
            'Meta': {'unique_together': "[('video', 'language_code')]", 'object_name': 'SubtitleLanguage'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'new_followed_languages'", 'blank': 'True', 'to': "orm['auth.CustomUser']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_forked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'official_signoff_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'pending_signoff_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'pending_signoff_expired_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'pending_signoff_unexpired_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'subtitles_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'unofficial_signoff_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'newsubtitlelanguage_set'", 'to': "orm['videos.Video']"}),
            'writelock_owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'writelocked_newlanguages'", 'null': 'True', 'to': "orm['auth.CustomUser']"}),
            'writelock_session_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'writelock_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'subtitles.subtitleversion': {
            'Meta': {'unique_together': "[('video', 'subtitle_language', 'version_number'), ('video', 'language_code', 'version_number')]", 'object_name': 'SubtitleVersion'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'newsubtitleversion_set'", 'to': "orm['auth.CustomUser']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'meta_1_content': ('videos.metadata.MetadataContentField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'meta_2_content': ('videos.metadata.MetadataContentField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'meta_3_content': ('videos.metadata.MetadataContentField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512', 'blank': 'True'}),
            'origin': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['subtitles.SubtitleVersion']", 'symmetrical': 'False', 'blank': 'True'}),
            'rollback_of_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'serialized_lineage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'serialized_subtitles': ('django.db.models.fields.TextField', [], {}),
            'subtitle_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'subtitle_language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subtitles.SubtitleLanguage']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'newsubtitleversion_set'", 'to': "orm['videos.Video']"}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '10'}),
            'visibility_override': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'blank': 'True'})
        },
        'teams.application': {
            'Meta': {'unique_together': "(('team', 'user', 'status'),)", 'object_name': 'Application'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'history': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'applications'", 'to': "orm['teams.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'team_applications'", 'to': "orm['auth.CustomUser']"})
        },
        'teams.partner': {
            'Meta': {'object_name': 'Partner'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'managed_partners'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.CustomUser']"}),
            'can_request_paid_captions': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'teams.project': {
            'Meta': {'unique_together': "(('team', 'name'), ('team', 'slug'))", 'object_name': 'Project'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2048', 'null': 'True', 'blank': 'True'}),
            'guidelines': ('django.db.models.fields.TextField', [], {'max_length': '2048', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Team']"}),
            'workflow_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'teams.team': {
            'Meta': {'object_name': 'Team'},
            'applicants': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'applicated_teams'", 'symmetrical': 'False', 'through': "orm['teams.Application']", 'to': "orm['auth.CustomUser']"}),
            'application_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'auth_provider_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '24', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'header_html_text': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'highlight': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_moderated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'last_notification_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'logo': ('utils.amazon.fields.S3EnabledImageField', [], {'default': "''", 'max_length': '100', 'thumb_sizes': '[(280, 100), (100, 100)]', 'blank': 'True'}),
            'max_tasks_per_member': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'membership_policy': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'notify_interval': ('django.db.models.fields.CharField', [], {'default': "'D'", 'max_length': '1'}),
            'page_content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'teams'", 'null': 'True', 'to': "orm['teams.Partner']"}),
            'points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'projects_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'square_logo': ('utils.amazon.fields.S3EnabledImageField', [], {'default': "''", 'max_length': '100', 'thumb_sizes': '[(100, 100), (48, 48)]', 'blank': 'True'}),
            'subtitle_policy': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'task_assign_policy': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'task_expiration': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'translate_policy': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'through': "orm['teams.TeamMember']", 'to': "orm['auth.CustomUser']"}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'intro_for_teams'", 'null': 'True', 'to': "orm['videos.Video']"}),
            'video_policy': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'videos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['videos.Video']", 'through': "orm['teams.TeamVideo']", 'symmetrical': 'False'}),
            'workflow_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'teams.teammember': {
            'Meta': {'unique_together': "(('team', 'user'),)", 'object_name': 'TeamMember'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "'contributor'", 'max_length': '16', 'db_index': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'members'", 'to': "orm['teams.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'team_members'", 'to': "orm['auth.CustomUser']"})
        },
        'teams.teamvideo': {
            'Meta': {'unique_together': "(('team', 'video'),)", 'object_name': 'TeamVideo'},
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']", 'null': 'True'}),
            'all_languages': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'partner_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Project']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Team']"}),
            'thumbnail': ('utils.amazon.fields.S3EnabledImageField', [], {'max_length': '100', 'null': 'True', 'thumb_sizes': '((288, 162), (120, 90))', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['videos.Video']", 'unique': 'True'})
        },
        'videos.video': {
            'Meta': {'object_name': 'Video'},
            'allow_community_edits': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'allow_video_urls_edit': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'complete_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'edited': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'featured': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'followed_videos'", 'blank': 'True', 'to': "orm['auth.CustomUser']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_subtitled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'languages_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'meta_1_content': ('videos.metadata.MetadataContentField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'meta_1_type': ('videos.metadata.MetadataTypeField', [], {'null': 'True', 'blank': 'True'}),
            'meta_2_content': ('videos.metadata.MetadataContentField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'meta_2_type': ('videos.metadata.MetadataTypeField', [], {'null': 'True', 'blank': 'True'}),
            'meta_3_content': ('videos.metadata.MetadataContentField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'meta_3_type': ('videos.metadata.MetadataTypeField', [], {'null': 'True', 'blank': 'True'}),
            'moderated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'moderating'", 'null': 'True', 'to': "orm['teams.Team']"}),
            'primary_audio_language_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '16', 'blank': 'True'}),
            's3_thumbnail': ('utils.amazon.fields.S3EnabledImageField', [], {'max_length': '100', 'thumb_sizes': '((288, 162), (120, 90))', 'blank': 'True'}),
            'small_thumbnail': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']", 'null': 'True', 'blank': 'True'}),
            'video_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'was_subtitled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'writelock_owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'writelock_owners'", 'null': 'True', 'to': "orm['auth.CustomUser']"}),
            'writelock_session_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'writelock_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'videos.videofeed': {
            'Meta': {'object_name': 'VideoFeed'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Team']", 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']", 'null': 'True', 'blank': 'True'})
        },
        'videos.videourl': {
            'Meta': {'object_name': 'VideoUrl'},
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'owner_username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'primary': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '255'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.Video']"}),
            'videoid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        }
    }
    
    complete_apps = ['externalsites']
