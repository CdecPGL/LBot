# Generated by Django 2.0 on 2018-01-03 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0016_auto_20180103_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='valid_message_command_groups',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AddField(
            model_name='user',
            name='valid_message_command_groups',
            field=models.CharField(default='', max_length=256),
        ),
    ]
