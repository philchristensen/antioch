# Generated by Django 2.1.10 on 2019-07-21 17:12

import antioch.core.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20190602_1951'),
    ]

    operations = [
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField()),
                ('url', antioch.core.models.URLField(max_length=255)),
            ],
            options={
                'db_table': 'repository',
            },
        ),
        migrations.AddField(
            model_name='verb',
            name='ref',
            field=models.CharField(default='master', max_length=255),
        ),
        migrations.AddField(
            model_name='verb',
            name='repo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.Repository'),
        ),
    ]