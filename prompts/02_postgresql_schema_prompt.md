# Prompt 2 — Generate the PostgreSQL Schema

Act as a senior PostgreSQL engineer.

Using the finalized database architecture below, generate production-quality PostgreSQL DDL.

This is for a future Django + React sauna QC tracking application, but this task is ONLY about PostgreSQL.

## Required tables

Create these four tables:

- products
- orders
- physical_units
- test_runs

Use lowercase snake_case column names.

## Table 1: products

Required business fields:

- product_id — primary key
- item_no — unique product/item code
- product_name
- voltage
- wattage
- supplier
- created_at
- updated_at

Requirements:

- `item_no` must be unique.
- voltage and wattage must be positive.
- voltage and wattage should use numeric/integer types appropriate for values such as 110, 220, 1840, 7664.
- Do not use floating point types for these fields.

## Table 2: orders

Required fields:

- order_id — primary key
- order_no
- product_id — FK to products
- item_no — snapshot/reference
- customer_no
- order_date
- sales_person
- quantity
- created_at
- updated_at

Requirements:

- A single customer order number may eventually appear on multiple product-line rows, so do NOT make `order_no` globally unique unless you explicitly justify it.
- Add a sensible composite uniqueness rule if appropriate.
- quantity must be >= 1.
- Keep item_no as a historical/business snapshot even though product_id exists.

## Table 3: physical_units

Required fields:

- unit_id — primary key
- item_serial_no
- product_id — FK to products
- item_no
- product_name
- order_id — nullable FK to orders
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

Requirements:

- `item_serial_no` must be unique.
- order_id must be nullable because inventory can exist before assignment.
- product_id is required.
- Keep item_no and product_name as snapshot fields.
- Keep order_no as a snapshot/reference.
- Implement unit_status using either:
  A. a PostgreSQL ENUM, or
  B. VARCHAR/TEXT plus CHECK constraint.

Choose the approach that works best with Django migrations and explain the choice.

Allowed unit statuses:

- IN_STOCK
- ASSIGNED
- SETUP
- TESTING
- QC_PASSED
- QC_FAILED
- ON_HOLD
- READY_TO_SHIP
- SHIPPED

Add sensible date consistency checks where they are safe and maintainable.

## Table 4: test_runs

Required fields:

- test_id — primary key
- unit_id — FK to physical_units
- product_id — FK to products
- order_id — nullable FK to orders
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

Requirements:

- One physical unit can have many test runs.
- Preserve historical snapshot fields:
  - item_serial_no
  - item_no
  - product_name
  - order_no
  - order_date
- Do not overwrite failed tests when a retest occurs.
- `test_pictures` should be JSONB.
- Default `test_pictures` to an empty JSON array.
- `test_report_s3_key` stores an AWS S3 object key, not a public URL.
- test_report fields may be nullable while a test is still in progress.
- order_id and order-related snapshots may be nullable if a test is performed before order assignment.
- Implement test_result in a Django-friendly manner.

Allowed test results:

- IN_PROGRESS
- PASS
- FAIL
- RETEST_REQUIRED
- CANCELLED

## Foreign-key behavior

Choose and explain appropriate FK behavior.

General preference:

- Never cascade-delete historical test runs just because a product or order is removed.
- Historical QC data should be protected.
- Prefer RESTRICT, PROTECT-style behavior, or SET NULL where appropriate.
- Product records referenced by historical QC should normally not be physically deleted.

## Indexing requirements

At minimum, consider indexes for:

- products.item_no
- orders.order_no
- orders.customer_no
- orders.order_date
- physical_units.item_serial_no
- physical_units.product_id
- physical_units.order_id
- physical_units.unit_status
- test_runs.unit_id
- test_runs.order_id
- test_runs.product_id
- test_runs.item_serial_no
- test_runs.order_no
- test_runs.test_date
- test_runs.test_result

Avoid redundant indexes that are automatically created by UNIQUE constraints.

## Timestamp behavior

Use timezone-aware timestamps:

```sql
TIMESTAMPTZ
```

Use reasonable defaults such as `CURRENT_TIMESTAMP`.

Explain how `updated_at` should be maintained. You may either:

- create a PostgreSQL trigger, or
- state that Django will maintain it.

Prefer the approach that best fits a Django-managed application.

## Output requirements

Return:

1. Complete executable PostgreSQL DDL.
2. Tables created in dependency-safe order.
3. All PK, FK, UNIQUE, NOT NULL, CHECK, and DEFAULT definitions.
4. Index creation statements.
5. Comments explaining important design choices.
6. A rollback/drop script in dependency-safe order.
7. A short section identifying any decisions Django migrations should own instead of raw PostgreSQL.

Do not generate frontend code.
Do not generate Django REST APIs.
Do not generate React code.
Do not silently add unrelated tables.
