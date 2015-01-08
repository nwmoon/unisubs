# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'SubtitleLanguage'
        db.create_table('subtitles_subtitlelanguage', (
            ('writelock_owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='writelocked_newlanguages', null=True, to=orm['auth.CustomUser'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('writelock_session_key', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('writelock_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(related_name='newsubtitlelanguage_set', to=orm['videos.Video'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('subtitles', ['SubtitleLanguage'])

        # Adding unique constraint on 'SubtitleLanguage', fields ['video', 'language_code']
        db.create_unique('subtitles_subtitlelanguage', ['video_id', 'language_code'])

        # Adding M2M table for field collaborators on 'SubtitleLanguage'
        db.create_table('subtitles_subtitlelanguage_collaborators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('subtitlelanguage', models.ForeignKey(orm['subtitles.subtitlelanguage'], null=False)),
            ('customuser', models.ForeignKey(orm['auth.customuser'], null=False))
        ))
        db.create_unique('subtitles_subtitlelanguage_collaborators', ['subtitlelanguage_id', 'customuser_id'])

        # Adding M2M table for field followers on 'SubtitleLanguage'
        db.create_table('subtitles_subtitlelanguage_followers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('subtitlelanguage', models.ForeignKey(orm['subtitles.subtitlelanguage'], null=False)),
            ('customuser', models.ForeignKey(orm['auth.customuser'], null=False))
        ))
        db.create_unique('subtitles_subtitlelanguage_followers', ['subtitlelanguage_id', 'customuser_id'])

        # Adding model 'SubtitleVersion'
        db.create_table('subtitles_subtitleversion', (
            ('version_number', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='newsubtitleversion_set', to=orm['auth.CustomUser'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=2048, blank=True)),
            ('serialized_lineage', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('visibility', self.gf('django.db.models.fields.CharField')(default='public', max_length=10)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('serialized_subtitles', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['videos.Video'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('subtitle_language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['subtitles.SubtitleLanguage'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('subtitles', ['SubtitleVersion'])

        # Adding unique constraint on 'SubtitleVersion', fields ['video', 'language_code', 'version_number']
        db.create_unique('subtitles_subtitleversion', ['video_id', 'language_code', 'version_number'])

        # Adding M2M table for field parents on 'SubtitleVersion'
        db.create_table('subtitles_subtitleversion_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_subtitleversion', models.ForeignKey(orm['subtitles.subtitleversion'], null=False)),
            ('to_subtitleversion', models.ForeignKey(orm['subtitles.subtitleversion'], null=False))
        ))
        db.create_unique('subtitles_subtitleversion_parents', ['from_subtitleversion_id', 'to_subtitleversion_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'SubtitleLanguage'
        db.delete_table('subtitles_subtitlelanguage')

        # Removing unique constraint on 'SubtitleLanguage', fields ['video', 'language_code']
        db.delete_unique('subtitles_subtitlelanguage', ['video_id', 'language_code'])

        # Removing M2M table for field collaborators on 'SubtitleLanguage'
        db.delete_table('subtitles_subtitlelanguage_collaborators')

        # Removing M2M table for field followers on 'SubtitleLanguage'
        db.delete_table('subtitles_subtitlelanguage_followers')

        # Deleting model 'SubtitleVersion'
        db.delete_table('subtitles_subtitleversion')

        # Removing unique constraint on 'SubtitleVersion', fields ['video', 'language_code', 'version_number']
        db.delete_unique('subtitles_subtitleversion', ['video_id', 'language_code', 'version_number'])

        # Removing M2M table for field parents on 'SubtitleVersion'
        db.delete_table('subtitles_subtitleversion_parents')
    
    
    models = {
        'accountlinker.thirdpartyaccount': {
            'Meta': {'unique_together': "(('type', 'username'),)", 'object_name': 'ThirdPartyAccount'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'oauth_access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'oauth_refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
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
            'partner': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'picture': ('utils.amazon.fields.S3EnabledImageField', [], {'thumb_options': "{'upscale': True, 'crop': 'smart'}", 'max_length': '100', 'blank': 'True'}),
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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
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
        'subtitles.subtitlelanguage': {
            'Meta': {'unique_together': "[('video', 'language_code')]", 'object_name': 'SubtitleLanguage'},
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'collab_newlanguages'", 'blank': 'True', 'to': "orm['auth.CustomUser']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'followed_newlanguages'", 'blank': 'True', 'to': "orm['auth.CustomUser']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'newsubtitlelanguage_set'", 'to': "orm['videos.Video']"}),
            'writelock_owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'writelocked_newlanguages'", 'null': 'True', 'to': "orm['auth.CustomUser']"}),
            'writelock_session_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'writelock_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'subtitles.subtitleversion': {
            'Meta': {'unique_together': "[('video', 'language_code', 'version_number')]", 'object_name': 'SubtitleVersion'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'newsubtitleversion_set'", 'to': "orm['auth.CustomUser']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['subtitles.SubtitleVersion']", 'symmetrical': 'False'}),
            'serialized_lineage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'serialized_subtitles': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'subtitle_language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['subtitles.SubtitleLanguage']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.Video']"}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'public'", 'max_length': '10'})
        },
        'teams.application': {
            'Meta': {'unique_together': "(('team', 'user'),)", 'object_name': 'Application'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'applications'", 'to': "orm['teams.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'team_applications'", 'to': "orm['auth.CustomUser']"})
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
            'logo': ('utils.amazon.fields.S3EnabledImageField', [], {'thumb_options': "{'upscale': True, 'autocrop': True}", 'max_length': '100', 'blank': 'True'}),
            'max_tasks_per_member': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'membership_policy': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'page_content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'projects_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'subtitle_policy': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'task_assign_policy': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'task_expiration': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'third_party_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'tseams'", 'symmetrical': 'False', 'to': "orm['accountlinker.ThirdPartyAccount']"}),
            'translate_policy': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'teams'", 'symmetrical': 'False', 'through': "orm['teams.TeamMember']", 'to': "orm['auth.CustomUser']"}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'intro_for_teams'", 'null': 'True', 'to': "orm['videos.Video']"}),
            'video_policy': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'videos': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['videos.Video']", 'through': "orm['teams.TeamVideo']", 'symmetrical': 'False'}),
            'workflow_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'teams.teammember': {
            'Meta': {'unique_together': "(('team', 'user'),)", 'object_name': 'TeamMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "'contributor'", 'max_length': '16', 'db_index': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'members'", 'to': "orm['teams.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'team_members'", 'to': "orm['auth.CustomUser']"})
        },
        'teams.teamvideo': {
            'Meta': {'unique_together': "(('team', 'video'),)", 'object_name': 'TeamVideo'},
            'added_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']"}),
            'all_languages': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'completed_languages': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['videos.SubtitleLanguage']", 'symmetrical': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'partner_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Project']"}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Team']"}),
            'thumbnail': ('utils.amazon.fields.S3EnabledImageField', [], {'max_length': '100', 'thumb_options': "{'upscale': True, 'crop': 'smart'}", 'null': 'True', 'thumb_sizes': '((290, 165), (120, 90))', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['videos.Video']", 'unique': 'True'})
        },
        'videos.subtitlelanguage': {
            'Meta': {'unique_together': "(('video', 'language', 'standard_language'),)", 'object_name': 'SubtitleLanguage'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'followed_languages'", 'blank': 'True', 'to': "orm['auth.CustomUser']"}),
            'had_version': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'has_version': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_forked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_original': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'percent_done': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'standard_language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.SubtitleLanguage']", 'null': 'True', 'blank': 'True'}),
            'subtitle_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'subtitles_fetched_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['videos.Video']"}),
            'writelock_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']", 'null': 'True', 'blank': 'True'}),
            'writelock_session_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'writelock_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
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
            'moderated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'moderating'", 'null': 'True', 'to': "orm['teams.Team']"}),
            's3_thumbnail': ('utils.amazon.fields.S3EnabledImageField', [], {'thumb_options': "{'upscale': True, 'crop': 'smart'}", 'max_length': '100', 'thumb_sizes': '((290, 165), (120, 90))', 'blank': 'True'}),
            'small_thumbnail': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'subtitles_fetched_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'thumbnail': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.CustomUser']", 'null': 'True', 'blank': 'True'}),
            'video_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'was_subtitled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'widget_views_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'writelock_owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'writelock_owners'", 'null': 'True', 'to': "orm['auth.CustomUser']"}),
            'writelock_session_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'writelock_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }
    
    complete_apps = ['subtitles']
