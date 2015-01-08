# encoding: utf-8
import time
import atom
from south.db import db
from south.v2 import DataMigration
import logging

class Migration(DataMigration):
    # there used to be a migration here, but it depended on the
    # YouTubeApiBridge in the videos.types.youtube module.  Since that class
    # is no longer around, this migration fails.  As a hack, let's just make
    # it a no-op
    
    def forwards(self, orm):
        pass
    
    def backwards(self, orm):
        pass
    
    models = {
        'accountlinker.thirdpartyaccount': {
            'Meta': {'unique_together': "(('type', 'username'),)", 'object_name': 'ThirdPartyAccount'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'oauth_access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'oauth_refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'accountlinker.youtubesyncrule': {
            'Meta': {'object_name': 'YoutubeSyncRule'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'team': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'user': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'video': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        }
    }
    
    complete_apps = ['accountlinker']
