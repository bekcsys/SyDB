import django.db.models.deletion
from django.db import migrations, models

from sauna_data.control_panels import CONTROL_PANEL_NAMES, control_panel_name_for


def assign_control_panels(apps, schema_editor):
    ControlPanel = apps.get_model("sauna_data", "ControlPanel")
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    panels = {name: ControlPanel.objects.create(name=name) for name in CONTROL_PANEL_NAMES}
    for box in PowerBox.objects.all():
        panel_name = control_panel_name_for(box.name)
        if not panel_name:
            continue
        box.control_panel = panels[panel_name]
        box.save(update_fields=["control_panel"])


def clear_control_panels(apps, schema_editor):
    apps.get_model("sauna_data", "PowerBox").objects.update(control_panel=None)
    apps.get_model("sauna_data", "ControlPanel").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0015_product_power_box_alternatives"),
    ]

    operations = [
        migrations.CreateModel(
            name="ControlPanel",
            fields=[
                ("control_panel_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "control_panels",
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="powerbox",
            name="control_panel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="power_boxes",
                to="sauna_data.controlpanel",
            ),
        ),
        migrations.RunPython(assign_control_panels, clear_control_panels),
    ]
