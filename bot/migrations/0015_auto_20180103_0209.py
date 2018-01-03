# Generated by Django 2.0 on 2018-01-02 17:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0014_task_importance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='groups',
        ),
        migrations.AddField(
            model_name='task',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='bot.Group'),
        ),
    ]