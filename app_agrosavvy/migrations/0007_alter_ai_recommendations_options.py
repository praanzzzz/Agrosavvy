# Generated by Django 5.0.6 on 2024-09-11 02:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_agrosavvy', '0006_ai_recommendations_nitrogen_ai_recommendations_ph_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ai_recommendations',
            options={'ordering': ['-reco_id']},
        ),
    ]
