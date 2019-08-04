# Generated by Django 2.1.8 on 2019-06-02 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20190602_1323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='object',
            name='observers',
            field=models.ManyToManyField(blank=True, null=True, related_name='observing', through='core.Observation', to='core.Object'),
        ),
        migrations.AlterField(
            model_name='object',
            name='parents',
            field=models.ManyToManyField(blank=True, null=True, related_name='children', through='core.Relationship', to='core.Object'),
        ),
    ]