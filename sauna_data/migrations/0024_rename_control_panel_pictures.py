from pathlib import Path

from django.db import migrations


def rename_control_panel_pictures(apps, schema_editor):
    ControlPanel = apps.get_model("sauna_data", "ControlPanel")
    slots = (
        ("front_picture_name", "front_1"),
        ("front_picture_2_name", "front_2"),
        ("back_picture_name", "back_1"),
        ("back_picture_2_name", "back_2"),
    )
    for panel in ControlPanel.objects.all():
        changed = []
        for field_name, stem in slots:
            current = getattr(panel, field_name)
            if not current:
                continue
            renamed = f"{stem}{Path(current).suffix.lower()}"
            if current == renamed:
                continue
            setattr(panel, field_name, renamed)
            changed.append(field_name)
        if changed:
            panel.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0023_control_panel_second_pictures"),
    ]

    operations = [
        migrations.RunPython(rename_control_panel_pictures, migrations.RunPython.noop),
    ]
