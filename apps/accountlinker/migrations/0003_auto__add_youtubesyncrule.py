# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'YoutubeSyncRule'
        db.create_table('accountlinker_youtubesyncrule', (
            ('user', self.gf('django.db.models.fields.TextField')()),
            ('video', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('team', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('accountlinker', ['YoutubeSyncRule'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'YoutubeSyncRule'
        db.delete_table('accountlinker_youtubesyncrule')
    
    
    models = {
        'accountlinker.thirdpartyaccount': {
            'Meta': {'unique_together': "(('type', 'username'),)", 'object_name': 'ThirdPartyAccount'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'oauth_access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'oauth_refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'accountlinker.youtubesyncrule': {
            'Meta': {'object_name': 'YoutubeSyncRule'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'team': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.TextField', [], {}),
            'video': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['accountlinker']
