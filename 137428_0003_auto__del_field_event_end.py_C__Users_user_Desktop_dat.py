# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Event.end'
        db.delete_column('events_event', 'end')


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'Event.end'
        raise RuntimeError("Cannot reverse this migration. 'Event.end' and its values cannot be restored.")


    models = {
        'events.event': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Event'},
            'address': ('django.db.models.fields.TextField', [], {'max_length': '250', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        }
    }

    complete_apps = ['events']
