# -*- coding: utf-8 -*-

__author__ = 'rotoudjimaye'

from django.db import models

class BlobField(models.Field):
    description = "Blob"

    def db_type(self):
        return 'blob'


BlobField = models.TextField

class JobDetail(models.Model):
    sched_name = models.CharField(max_length=120)
    job_name = models.CharField(max_length=200)
    job_group = models.CharField(max_length=200)
    description = models.CharField(max_length=250)
    is_durable = models.CharField(max_length=1)
    is_nonconcurrent = models.CharField(max_length=1)
    is_update_data = models.CharField(max_length=1)
    requests_recovery = models.CharField(max_length=1)
    job_data = BlobField()

    class Meta:
        db_table = "jyquartz_job_details"
        unique_together = ("sched_name", "job_name", "job_group")


class Trigger(models.Model):
    sched_name = models.CharField(max_length=120)
    trigger_name = models.CharField(max_length=200)
    trigger_group = models.CharField(max_length=200)
    job_name = models.CharField(max_length=200)
    job_group = models.CharField(max_length=200)
    description = models.CharField(max_length=250)
    next_fire_time = models.IntegerField() #BIGINT(13)
    previous_fire_time = models.IntegerField() #BIGINT(13)
    priority = models.IntegerField(blank=True, null=True) #INTEGER
    trigger_state = models.CharField(max_length=16)
    trigger_type = models.CharField(max_length=8)
    start_time = models.IntegerField() #BIGINT(13)
    end_time = models.IntegerField() #BIGINT(13)
    calendar_name = models.CharField(max_length=200)
    misfire_instr = models.IntegerField() #SMALLINT(2)
    job_data = BlobField()

    class Meta:
        db_table = "jyquartz_triggers"
        unique_together = ("sched_name", "trigger_name", "trigger_group")


class SimpleTrigger(models.Model):
    sched_name = models.CharField(max_length=120)
    trigger_name = models.CharField(max_length=200)
    trigger_group = models.CharField(max_length=200)
    repeat_count = models.IntegerField() #BIGINT(7)
    repeat_interval = models.IntegerField() #BIGINT(12)
    times_triggered = models.IntegerField() #BIGINT(10)

    class Meta:
        db_table = "jyquartz_simple_triggers"
        unique_together = ("sched_name", "trigger_name", "trigger_group")


class CronTrigger(models.Model):
    sched_name = models.CharField(max_length=120)
    trigger_name = models.CharField(max_length=200)
    trigger_group = models.CharField(max_length=200)
    cron_expression = models.CharField(max_length=200)
    time_zone_id = models.CharField(max_length=80)

    class Meta:
        db_table = "jyquartz_cron_triggers"
        unique_together = ("sched_name", "trigger_name", "trigger_group")


class SimpropTrigger(models.Model):
    sched_name = models.CharField(max_length=120)
    trigger_name = models.CharField(max_length=200)
    trigger_group = models.CharField(max_length=200)
    str_prop_1 = models.CharField(max_length=510)
    str_prop_2 = models.CharField(max_length=510)
    str_prop_3 = models.CharField(max_length=510)
    int_prop_1 = models.IntegerField()
    int_prop_2 = models.IntegerField()
    long_prop_1 = models.IntegerField() # bigint
    long_prop_2 = models.IntegerField() # bigint
    dec_prop_1 = models.DecimalField(max_digits=13, decimal_places=4)
    dec_prop_2 = models.DecimalField(max_digits=13, decimal_places=4)
    bool_prop_1 = models.CharField(max_length=1)
    bool_prop_2 = models.CharField(max_length=1)

    class Meta:
        db_table = "jyquartz_simprop_triggers"
        unique_together = ("sched_name", "trigger_name", "trigger_group")


class BlobTrigger(models.Model):
    sched_name = models.CharField(max_length=120)
    trigger_name = models.CharField(max_length=200)
    trigger_group = models.CharField(max_length=200)
    blob_data = BlobField()

    class Meta:
        db_table = "jyquartz_blob_triggers"
        unique_together = ("sched_name", "trigger_name", "trigger_group")


class Calendar(models.Model):
    sched_name = models.CharField(max_length=120)
    calendar_name = models.CharField(max_length=200)
    calendar = BlobField()

    class Meta:
        db_table = "jyquartz_calendars"
        unique_together = ("sched_name", "calendar_name")


class PausedTriggerGrps(models.Model):
    sched_name = models.CharField(max_length=120)
    trigger_group = models.CharField(max_length=200)

    class Meta:
        db_table = "jyquartz_paused_trigger_grps"
        unique_together = ("sched_name", "trigger_group")


class FiredTrigger(models.Model):
    sched_name = models.CharField(max_length=120)
    entry_id = models.CharField(max_length=95)
    trigger_name = models.CharField(max_length=200)
    trigger_group = models.CharField(max_length=200)
    instance_name = models.CharField(max_length=200)
    fired_time = models.IntegerField()   #BIGINT
    priority = models.IntegerField()
    state = models.CharField(max_length=16)
    job_name = models.CharField(max_length=200)
    job_group = models.CharField(max_length=200)
    is_nonconcurrent = models.CharField(max_length=1)
    requests_recovery = models.CharField(max_length=1)

    class Meta:
        db_table = "jyquartz_fired_triggers"
        unique_together = ("sched_name", "entry_id")


class SchedulerState(models.Model):
    sched_name = models.CharField(max_length=120)
    instance_name = models.CharField(max_length=200)
    last_checkin_time = models.IntegerField() #BIGINT
    checkin_interval = models.IntegerField()  #BIGINT

    class Meta:
        db_table = "jyquartz_scheduler_state"
        unique_together = ("sched_name", "instance_name")


class Lock(models.Model):
    sched_name = models.CharField(max_length=120)
    lock_name = models.CharField(max_length=40)

    class Meta:
        db_table = "jyquartz_locks"
        unique_together = ("sched_name", "lock_name")




