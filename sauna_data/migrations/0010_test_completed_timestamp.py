from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0009_qc_status_options"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="physicalunit",
            name="physical_units_test_dates_ok",
        ),
        migrations.RemoveConstraint(
            model_name="physicalunit",
            name="physical_units_ship_date_ok",
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="physicalunit",
                    name="date_test_completed",
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE physical_units
                    ALTER COLUMN date_test_completed TYPE timestamp with time zone
                    USING (
                        CASE
                            WHEN date_test_completed IS NULL THEN NULL
                            ELSE date_test_completed::timestamp AT TIME ZONE 'America/Chicago'
                        END
                    );
                    """,
                    reverse_sql="""
                    ALTER TABLE physical_units
                    ALTER COLUMN date_test_completed TYPE date
                    USING (date_test_completed AT TIME ZONE 'America/Chicago')::date;
                    """,
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="physicalunit",
            constraint=models.CheckConstraint(
                condition=models.Q(date_test_completed__isnull=True)
                | models.Q(date_test_started__isnull=True)
                | models.Q(date_test_completed__date__gte=models.F("date_test_started")),
                name="physical_units_test_dates_ok",
            ),
        ),
        migrations.AddConstraint(
            model_name="physicalunit",
            constraint=models.CheckConstraint(
                condition=models.Q(ship_date__isnull=True)
                | models.Q(date_test_completed__isnull=True)
                | models.Q(date_test_completed__date__lte=models.F("ship_date")),
                name="physical_units_ship_date_ok",
            ),
        ),
    ]
