# Generated by Django 2.1.8 on 2019-06-02 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20190602_1402'),
    ]

    operations = [
        migrations.AlterField(
            model_name='object',
            name='observers',
            field=models.ManyToManyField(blank=True, related_name='observing', through='core.Observation', to='core.Object'),
        ),
        migrations.AlterField(
            model_name='object',
            name='parents',
            field=models.ManyToManyField(blank=True, related_name='children', through='core.Relationship', to='core.Object'),
        ),
    ]
