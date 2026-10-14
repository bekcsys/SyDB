# Prompt 4 — Validate, Seed, and Test the Sauna QC Database

Act as a database reviewer and Django/PostgreSQL test engineer.

A PostgreSQL database and Django models have now been created for a sauna QC tracking application.

Your task is to validate the design, create realistic seed data, and create database-level/model-level tests before API or frontend development begins.

Do not build React.
Do not build REST API endpoints yet.

## Expected core tables/models

- products / Product
- orders / Order
- physical_units / PhysicalUnit
- test_runs / TestRun

## Business workflow to validate

1. Customer order is created.
2. Product is associated with the order.
3. One or more physical sauna units are assigned to the order.
4. Each physical unit has a unique serial number.
5. A unit may have multiple test runs.
6. Test #1 may fail.
7. The same unit may be repaired.
8. Test #2 may pass.
9. Both test records must remain in history.
10. PDF QC reports are represented by AWS S3 metadata.
11. Test pictures are represented by JSONB/JSONField metadata.
12. A passed unit can transition toward READY_TO_SHIP and SHIPPED.
13. Historical snapshot fields must not change if master Product or Order records are later edited.

## Seed product data

Create seed records for at least these products:

| item_no | product_name | voltage | wattage | supplier |
|---|---|---:|---:|---|
| 310203-01-wang | Pro5.1 | 110 | 1840 | Global |
| 310203-02-wang | Pro5.2 | 110 | 1940 | Global |
| 310203-03-wang | Pro5.3 | 220 | 2390 | Global |
| 310203-04-wang | Pro5.4 | 220 | 2440 | Global |
| 310203-06-wang | Pro5.6 | 220 | 3940 | Global |
| 310211-02-wang | CS.2 | 220 | 2956 | Global |
| 310211-04-wang | CS.4 | 220 | 3840 | Global |
| 310211-06-wang | CS.6 | 220 | 6064 | Global |
| 310211-08-wang | CS.8 | 220 | 7664 | Global |
| 310211-02-Luis | CS.2 | 220 | 2956 | Global |
| 310211-04-Luis | CS.4 | 220 | 3840 | Global |
| 310211-06-Luis | CS.6 | 220 | 6064 | Global |
| 310211-08-Luis | CS.8 | 220 | 7664 | Global |
| 310211-06-EVR-Li | CS.6-EVR1 | 220 | 5264 | Global |
| 310211-08-EVR-Li | CS.8-EVR1 | 220 | 6864 | Global |
| 310207-01GC-wang | Redfit Room | 220 | 6823 | Global |
| 310207-01GC-Li | Redfit Room | 220 | 6823 | Global |
| 310208-C-Luis | Redfit iGym | 220 | 5584 | Global |
| 310208-C-wang | Redfit iGym | 220 | 5584 | Global |

## Seed order

Create at least:

```text
order_no: 175899
item_no: 310211-06-EVR-Li
customer_no: 44-ANY0083
order_date: 2026-07-27
sales_person: AKT
quantity: 1
```

Associate it to the correct Product.

## Seed physical unit

Create at least:

```text
item_serial_no: 73204-3010
product: 310211-06-EVR-Li / CS.6-EVR1
order: 175899
item_no snapshot: 310211-06-EVR-Li
product_name snapshot: CS.6-EVR1
order_no snapshot: 175899
unit_status: TESTING
```

Use reasonable dates for assignment/testing.

## Seed test history

Create at least two test runs for serial number `73204-3010`.

### Test 1

Example:

```text
test_date: 2026-09-24
test_person: QC User
test_result: FAIL
test_notes: Temperature did not meet QC requirement.
```

Include example S3 metadata such as:

```text
test_report_file_name:
73204-3010_QC_2026-09-24.pdf

test_report_s3_key:
qc-reports/2026/09/73204-3010/test-1/73204-3010_QC_2026-09-24.pdf
```

### Test 2

Example:

```text
test_date: 2026-09-25
test_person: QC User
test_result: PASS
test_notes: Retest completed after corrective action.
```

Include a different report S3 key and at least two test picture metadata entries.

## Required validation tests

Create tests proving:

1. Duplicate product item numbers are rejected.
2. Duplicate physical-unit serial numbers are rejected.
3. quantity < 1 is rejected.
4. voltage <= 0 is rejected.
5. wattage <= 0 is rejected.
6. Invalid unit status is rejected.
7. Invalid test result is rejected.
8. A physical unit can exist without an order.
9. One physical unit can have multiple test runs.
10. A failed test and later passing retest can coexist.
11. Deleting or changing related master data does not destroy historical QC records.
12. Snapshot fields remain unchanged after Product name/item information changes.
13. Snapshot fields remain unchanged after Order information changes.
14. JSON test picture metadata is stored and retrieved correctly.
15. S3 keys are stored as strings and no binary file is stored in PostgreSQL.
16. Queries for the latest test return the correct record.
17. Queries for all failed tests in a date range return the correct records.
18. Queries for units ready to ship return only the correct status.
19. FK behaviors work as intended.
20. Indexes exist for the high-use search fields.

## Test framework

If using Django:

- use Django TestCase or pytest-django
- use PostgreSQL for integration tests where PostgreSQL-specific behavior matters
- avoid relying only on SQLite because JSONB/index/constraint behavior can differ

## Seed-data implementation

Provide one recommended approach:

- Django data migration
- Django management command
- fixture
- factory

For long-term maintainability, prefer a management command or factories unless there is a strong reason otherwise.

## Review the schema critically

Before writing tests, inspect the schema for:

- accidental cascade deletes
- missing indexes
- redundant indexes
- nullable fields that should be required
- required fields that should be nullable during workflow
- unsafe status modeling
- invalid date assumptions
- inconsistent snapshot logic
- S3 URL misuse
- mutable historical test records
- duplicate or unnecessary columns

If you find a serious issue, explain it and propose a migration to fix it.

## Output

Return:

1. Schema review findings.
2. Seed-data strategy.
3. Django management command or equivalent seed script.
4. Model/database tests.
5. PostgreSQL verification SQL.
6. Sample queries demonstrating the seeded workflow.
7. Expected results for the important tests.
8. A final checklist saying whether the database is ready for the next phase: Django REST API development.

Do not build the frontend.
Do not build API endpoints.
Do not change the fundamental four-table business model unless a serious data-integrity issue requires it.
