# Generated by Django 5.0.6 on 2024-09-10 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_agrosavvy', '0004_alter_barangay_brgy_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AI_Recommendations',
            fields=[
                ('reco_id', models.AutoField(primary_key=True, serialize=False)),
                ('basic_output', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='address',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
