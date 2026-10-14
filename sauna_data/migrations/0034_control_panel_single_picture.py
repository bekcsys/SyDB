from django.db import migrations, models


def copy_first_picture(apps, schema_editor):
    ControlPanel = apps.get_model("sauna_data", "ControlPanel")
    slots = (
        ("front_picture", "front_picture_name"),
        ("front_picture_2", "front_picture_2_name"),
        ("back_picture", "back_picture_name"),
        ("back_picture_2", "back_picture_2_name"),
    )
    for panel in ControlPanel.objects.all():
        for content_field, name_field in slots:
            content = getattr(panel, content_field)
            name = getattr(panel, name_field) or ""
            if not content or not name:
                continue
            suffix = name[name.rfind("."):].lower() if "." in name else ""
            panel.picture = content
            panel.picture_name = f"picture{suffix}" if suffix else "picture"
            panel.save(update_fields=["picture", "picture_name"])
            break


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0033_product_supplier_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="picture",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="picture_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(copy_first_picture, migrations.RunPython.noop),
        migrations.RemoveField(model_name="controlpanel", name="front_picture"),
        migrations.RemoveField(model_name="controlpanel", name="front_picture_name"),
        migrations.RemoveField(model_name="controlpanel", name="front_picture_2"),
        migrations.RemoveField(model_name="controlpanel", name="front_picture_2_name"),
        migrations.RemoveField(model_name="controlpanel", name="back_picture"),
        migrations.RemoveField(model_name="controlpanel", name="back_picture_name"),
        migrations.RemoveField(model_name="controlpanel", name="back_picture_2"),
        migrations.RemoveField(model_name="controlpanel", name="back_picture_2_name"),
    ]
