# Prompt 3 — Translate the PostgreSQL Design into Django Models and Migrations

Act as a senior Django backend engineer with strong PostgreSQL experience.

The database has been designed for a sauna QC tracking system. The future application will use Django + Django REST Framework + React, but this task is focused ONLY on the Django data model and PostgreSQL-compatible migrations.

Do not build React components, serializers, views, or API endpoints yet.

## Core models

Create Django models for:

- Product
- Order
- PhysicalUnit
- TestRun

Use PostgreSQL as the database.

## Product

Fields:

- id
- item_no
- product_name
- voltage
- wattage
- supplier
- created_at
- updated_at

Rules:

- item_no unique
- voltage > 0
- wattage > 0

## Order

Fields:

- id
- order_no
- product
- item_no
- customer_no
- order_date
- sales_person
- quantity
- created_at
- updated_at

Rules:

- product is FK to Product
- quantity >= 1
- item_no is deliberately retained as a snapshot/business field
- do not assume order_no is globally unique because one order number may later contain multiple product lines
- propose a sensible UniqueConstraint if appropriate

## PhysicalUnit

Fields:

- id
- item_serial_no
- product
- item_no
- product_name
- order
- order_no
- unit_status
- date_received
- date_assigned
- date_test_started
- date_test_completed
- ship_date
- location
- notes
- created_at
- updated_at

Rules:

- item_serial_no unique
- product required
- order nullable and blankable
- item_no/product_name are snapshots
- order_no is a snapshot/reference field
- use Django TextChoices for unit_status

Statuses:

```text
IN_STOCK
ASSIGNED
SETUP
TESTING
QC_PASSED
QC_FAILED
ON_HOLD
READY_TO_SHIP
SHIPPED
```

## TestRun

Fields:

- id
- unit
- product
- order
- item_serial_no
- item_no
- product_name
- order_no
- order_date
- test_date
- test_person
- test_result
- test_report_file_name
- test_report_s3_key
- test_report_bucket
- test_pictures
- test_notes
- created_at
- updated_at

Rules:

- unit FK to PhysicalUnit
- product FK to Product
- order nullable FK to Order
- one unit can have many tests
- use Django TextChoices for test_result
- test_pictures should use models.JSONField(default=list, blank=True)
- report file fields may be blank/null while test is incomplete
- snapshot fields must be retained
- do not overwrite old tests when a retest is performed

Test results:

```text
IN_PROGRESS
PASS
FAIL
RETEST_REQUIRED
CANCELLED
```

## Historical-data requirement

The system must preserve QC history.

Choose appropriate `on_delete` behavior.

Strong preference:

- Product references: PROTECT where deletion would damage history
- PhysicalUnit → TestRun: PROTECT or another history-safe behavior
- Order references may use SET_NULL where historical snapshot fields allow the test/unit record to remain meaningful

Explain every `on_delete` choice.

## Snapshot behavior

The following values should be copied into a PhysicalUnit or TestRun so the historical record does not change if master data changes later:

PhysicalUnit snapshots:

- item_no
- product_name
- order_no

TestRun snapshots:

- item_serial_no
- item_no
- product_name
- order_no
- order_date

Design a safe implementation strategy.

For example, consider whether snapshots should be populated:

- in model `save()`
- in a service layer
- in database triggers
- at object creation only

Recommend the cleanest Django approach and explain the tradeoffs.

Do NOT make a design that automatically rewrites old snapshot fields every time the related Product or Order changes.

## AWS S3 requirement

The scanned QC report PDF and test pictures are stored in AWS S3.

For this database phase:

- store only file metadata/object keys in PostgreSQL
- do not store binary files in PostgreSQL
- do not store permanent public URLs
- `test_report_s3_key` represents the S3 object key
- `test_report_bucket` stores the bucket name if needed
- `test_pictures` contains JSON metadata for multiple image objects

Example:

```json
[
  {
    "file_name": "front.jpg",
    "s3_key": "qc-pictures/2026/09/73204-3010/test-1001/front.jpg"
  }
]
```

Do not implement S3 upload code yet.

## Database constraints and indexes

Use Django:

- UniqueConstraint
- CheckConstraint
- indexes
- db_index only where appropriate

Ensure PostgreSQL receives useful constraints for:

- positive voltage
- positive wattage
- quantity >= 1
- serial number uniqueness
- status/result validity through TextChoices and database constraints where appropriate

Add indexes for common searches:

- order number
- customer number
- order date
- serial number
- product FK
- order FK
- unit status
- test date
- test result

## Output

Return:

1. `models.py`
2. any custom model managers only if actually useful
3. recommended migration strategy
4. the expected first migration
5. explanation of constraints and indexes
6. explanation of snapshot handling
7. example Django ORM queries for:
   - all tests for one serial number
   - latest test for one physical unit
   - all failed tests in a date range
   - all units assigned to an order
   - all units ready to ship
8. notes about compatibility with PostgreSQL

Do not create serializers.
Do not create APIs.
Do not create React code.
Do not add authentication yet.
