# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MonitoredModel'
        db.create_table('lizard_history_monitoredmodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('app_label', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('lizard_history', ['MonitoredModel'])

        # Adding unique constraint on 'MonitoredModel', fields ['app_label', 'model']
        db.create_unique('lizard_history_monitoredmodel', ['app_label', 'model'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'MonitoredModel', fields ['app_label', 'model']
        db.delete_unique('lizard_history_monitoredmodel', ['app_label', 'model'])

        # Deleting model 'MonitoredModel'
        db.delete_table('lizard_history_monitoredmodel')


    models = {
        'lizard_history.monitoredmodel': {
            'Meta': {'ordering': "('app_label', 'model')", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'MonitoredModel'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['lizard_history']
