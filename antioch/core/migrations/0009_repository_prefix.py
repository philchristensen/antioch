# Generated by Django 2.1.10 on 2019-07-28 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20190728_1001'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='prefix',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]