# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BlogRoll'
        db.create_table('core_blogroll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('order', self.gf('django.db.models.fields.SmallIntegerField')(default=5)),
        ))
        db.send_create_signal('core', ['BlogRoll'])


    def backwards(self, orm):
        
        # Deleting model 'BlogRoll'
        db.delete_table('core_blogroll')


    models = {
        'core.blogroll': {
            'Meta': {'ordering': "('order',)", 'object_name': 'BlogRoll'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {'default': '5'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['core']
