# Generated by Django 2.0.1 on 2018-05-21 15:00

import autoslug.fields
import courselib.json_fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('coredata', '0021_new_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(choices=[('PERS', 'Me personally'), ('ROLE', 'All people with role'), ('INST', 'Me when teaching a specific course')], max_length=4, verbose_name='Who gets reminded?')),
                ('date_type', models.CharField(choices=[('YEAR', 'Annually on a month/day'), ('SEM', 'Semesterly on a week/weekday')], max_length=4)),
                ('title', models.CharField(help_text='Title for the reminder/subject for the reminder email', max_length=100)),
                ('content', models.TextField(help_text='Text for the reminder')),
                ('status', models.CharField(choices=[('A', 'Active'), ('D', 'Deleted')], default='A', max_length=1)),
                ('role', models.CharField(blank=True, choices=[('ADVS', 'Advisor'), ('FAC', 'Faculty Member'), ('SESS', 'Sessional Instructor'), ('COOP', 'Co-op Staff'), ('INST', 'Other Instructor'), ('SUPV', 'Additional Supervisor'), ('DISC', 'Discipline Case Administrator'), ('DICC', 'Discipline Case Filer (email CC)'), ('ADMN', 'Departmental Administrator'), ('TAAD', 'TA Administrator'), ('TADM', 'Teaching Administrator'), ('GRAD', 'Grad Student Administrator'), ('GRPD', 'Graduate Program Director'), ('FUND', 'Grad Funding Administrator'), ('FDCC', 'Grad Funding Reminder CC'), ('TECH', 'Tech Staff'), ('GPA', 'GPA conversion system admin'), ('OUTR', 'Outreach Administrator'), ('INV', 'Inventory Administrator'), ('FACR', 'Faculty Viewer'), ('REPV', 'Report Viewer'), ('FACA', 'Faculty Administrator'), ('RELA', 'Relationship Database User'), ('SPAC', 'Space Administrator'), ('FORM', 'Form Administrator'), ('SYSA', 'System Administrator'), ('NONE', 'none')], max_length=4, null=True)),
                ('month', models.CharField(blank=True, choices=[('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')], max_length=1, null=True)),
                ('day', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('week', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('weekday', models.CharField(blank=True, choices=[('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday')], max_length=1, null=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='autoslug', unique=True)),
                ('config', courselib.json_fields.JSONField(default=dict)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coredata.Course')),
                ('person', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coredata.Person')),
                ('unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coredata.Unit')),
            ],
        ),
    ]