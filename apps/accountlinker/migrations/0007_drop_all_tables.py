# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    depends_on = (
        ("externalsites", "0008_import_accountlinker_data"),
        ("auth", "0034_remove_third_party_accounts_table"),
        ("teams", "0140_remove_third_party_accounts_table"),
    )
    
    def forwards(self, orm):
        
        # Deleting model 'ThirdPartyAccount'
        db.delete_table('accountlinker_thirdpartyaccount')

        # Deleting model 'YoutubeSyncRule'
        db.delete_table('accountlinker_youtubesyncrule')
    
    
    def backwards(self, orm):
        
        # Adding model 'ThirdPartyAccount'
        db.create_table('accountlinker_thirdpartyaccount', (
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('oauth_refresh_token', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('channel_id', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True, db_index=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('oauth_access_token', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('accountlinker', ['ThirdPartyAccount'])

        # Adding model 'YoutubeSyncRule'
        db.create_table('accountlinker_youtubesyncrule', (
            ('team', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('video', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('user', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('accountlinker', ['YoutubeSyncRule'])
    
    
    models = {
        
    }
    
    complete_apps = ['accountlinker']
