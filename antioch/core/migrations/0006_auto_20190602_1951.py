# Generated by Django 2.1.8 on 2019-06-02 23:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20190602_1403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verb',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.Object'),
        ),
    ]