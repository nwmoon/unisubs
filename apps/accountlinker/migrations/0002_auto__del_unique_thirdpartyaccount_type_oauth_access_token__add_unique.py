# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Removing unique constraint on 'ThirdPartyAccount', fields ['type', 'oauth_access_token']
        db.delete_unique('accountlinker_thirdpartyaccount', ['type', 'oauth_access_token'])

        # Adding unique constraint on 'ThirdPartyAccount', fields ['username', 'type']
        db.create_unique('accountlinker_thirdpartyaccount', ['username', 'type'])
    
    
    def backwards(self, orm):
        
        # Adding unique constraint on 'ThirdPartyAccount', fields ['type', 'oauth_access_token']
        db.create_unique('accountlinker_thirdpartyaccount', ['type', 'oauth_access_token'])

        # Removing unique constraint on 'ThirdPartyAccount', fields ['username', 'type']
        db.delete_unique('accountlinker_thirdpartyaccount', ['username', 'type'])
    
    
    models = {
        'accountlinker.thirdpartyaccount': {
            'Meta': {'unique_together': "(('type', 'username'),)", 'object_name': 'ThirdPartyAccount'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'oauth_access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'oauth_refresh_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        }
    }
    
    complete_apps = ['accountlinker']
