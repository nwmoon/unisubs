# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'ThirdPartyAccount.full_name'
        db.add_column('accountlinker_thirdpartyaccount', 'full_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

    def backwards(self, orm):
        
        # Deleting field 'ThirdPartyAccount.full_name'
        db.delete_column('accountlinker_thirdpartyaccount', 'full_name')

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
