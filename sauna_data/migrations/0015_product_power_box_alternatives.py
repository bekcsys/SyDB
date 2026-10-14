from django.db import migrations, models


REDFIT_ROOM_BOXES = ("CS-Li", "RFR-Wang")


def link_redfit_room_choices(apps, schema_editor):
    Product = apps.get_model("sauna_data", "Product")
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Membership = apps.get_model("sauna_data", "PowerBoxProduct")
    boxes = {
        box.name: box
        for box in PowerBox.objects.filter(name__in=REDFIT_ROOM_BOXES)
    }
    if len(boxes) != len(REDFIT_ROOM_BOXES):
        return
    products = Product.objects.filter(product_name__iexact="Redfit Room")
    for product in products:
        for box in boxes.values():
            Membership.objects.get_or_create(power_box=box, product=product)


def unlink_redfit_room_choices(apps, schema_editor):
    Membership = apps.get_model("sauna_data", "PowerBoxProduct")
    Membership.objects.filter(
        power_box__name="RFR-Wang",
        product__product_name__iexact="Redfit Room",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0014_power_boxes"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="powerboxproduct",
            name="power_box_products_one_box",
        ),
        migrations.AddConstraint(
            model_name="powerboxproduct",
            constraint=models.UniqueConstraint(
                fields=("power_box", "product"),
                name="power_box_products_unique_pair",
            ),
        ),
        migrations.RunPython(link_redfit_room_choices, unlink_redfit_room_choices),
    ]
