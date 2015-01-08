# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'ThirdPartyAccount.channel_id'
        db.add_column('accountlinker_thirdpartyaccount', 'channel_id', self.gf('django.db.models.fields.CharField')(default='', max_length=255, db_index=True, blank=True), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Deleting field 'ThirdPartyAccount.channel_id'
        db.delete_column('accountlinker_thirdpartyaccount', 'channel_id')
    
    
    models = {
        'accountlinker.thirdpartyaccount': {
            'Meta': {'unique_together': "(('type', 'username'),)", 'object_name': 'ThirdPartyAccount'},
            'channel_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'db_index': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
