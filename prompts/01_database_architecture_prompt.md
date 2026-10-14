# Prompt 1 — Design the PostgreSQL Database Architecture

You are a senior PostgreSQL database architect designing the data layer for a sauna manufacturing / QC tracking web application.

The future application stack will be:

- Backend: Django + Django REST Framework
- Frontend: React
- Database: PostgreSQL
- File storage: AWS S3
- Deployment: to be decided later

For this task, focus ONLY on the PostgreSQL database architecture. Do not build the React frontend yet. Do not build Django views or APIs yet.

## Business workflow

The company receives customer orders for sauna products.

Typical workflow:

1. A customer order is received.
2. One or more physical sauna units are selected or assigned to the order.
3. Each physical sauna has a unique serial number.
4. The sauna is set up for QC/testing.
5. One or more test runs can be performed on the same physical sauna.
6. A test run can PASS, FAIL, require RETEST, or still be IN PROGRESS.
7. A scanned QC test report is stored as a PDF in AWS S3.
8. Test photographs are also stored in AWS S3.
9. Failed units may be repaired and tested again.
10. When a unit passes QC, it can move to READY_TO_SHIP and later SHIPPED.
11. Historical test records must remain accurate even if product data changes later.

## Core entities

For version 1, use these four core tables:

1. products
2. orders
3. physical_units
4. test_runs

Do not add extra business tables unless there is a strong technical reason. If you recommend an additional table, explain why before including it.

## Existing product data structure

Products currently contain:

- productID
- itemNo
- productName
- voltage
- wattage
- supplier

Example product records include:

- 310203-01-wang / Pro5.1 / 110 V / 1840 W / Global
- 310203-02-wang / Pro5.2 / 110 V / 1940 W / Global
- 310203-03-wang / Pro5.3 / 220 V / 2390 W / Global
- 310203-04-wang / Pro5.4 / 220 V / 2440 W / Global
- 310203-06-wang / Pro5.6 / 220 V / 3940 W / Global
- 310211-02-wang / CS.2 / 220 V / 2956 W / Global
- 310211-04-wang / CS.4 / 220 V / 3840 W / Global
- 310211-06-wang / CS.6 / 220 V / 6064 W / Global
- 310211-08-wang / CS.8 / 220 V / 7664 W / Global
- 310211-02-Luis / CS.2 / 220 V / 2956 W / Global
- 310211-04-Luis / CS.4 / 220 V / 3840 W / Global
- 310211-06-Luis / CS.6 / 220 V / 6064 W / Global
- 310211-08-Luis / CS.8 / 220 V / 7664 W / Global
- 310211-06-EVR-Li / CS.6-EVR1 / 220 V / 5264 W / Global
- 310211-08-EVR-Li / CS.8-EVR1 / 220 V / 6864 W / Global
- 310207-01GC-wang / Redfit Room / 220 V / 6823 W / Global
- 310207-01GC-Li / Redfit Room / 220 V / 6823 W / Global
- 310208-C-Luis / Redfit iGym / 220 V / 5584 W / Global
- 310208-C-wang / Redfit iGym / 220 V / 5584 W / Global

## Existing order data structure

Orders currently contain:

- orderID
- orderNo
- itemNo
- customerNo
- orderDate
- salesPerson

Example:

- orderID: 1
- orderNo: 175899
- itemNo: 310211-06-EVR-Li
- customerNo: 44-ANY0083
- orderDate: 2026-07-27
- salesPerson: AKT

For version 1, assume one order row represents one ordered product line. Add `quantity` so the system knows how many physical units are expected for that order row.

If the future system needs multiple different product lines under one customer order number, explain how this model could later evolve into `orders` + `order_items`, but do not redesign version 1 around that unless necessary.

## Physical unit requirements

A physical unit represents an actual sauna with a serial number.

Recommended fields include:

- unitID
- itemSerialNo
- productID
- itemNo
- productName
- orderID
- orderNo
- unitStatus
- dateReceived
- dateAssigned
- dateTestStarted
- dateTestCompleted
- shipDate
- location
- notes
- createdAt
- updatedAt

Important rules:

- `itemSerialNo` should uniquely identify the physical sauna.
- A physical unit may exist before being assigned to an order.
- `orderID` must therefore be nullable.
- `productID` links to products.
- Keep `itemNo` and `productName` as snapshot fields for historical traceability.
- `orderNo` may also be kept as a snapshot/reference field.
- The physical unit has a current lifecycle status.

Suggested unit statuses:

- IN_STOCK
- ASSIGNED
- SETUP
- TESTING
- QC_PASSED
- QC_FAILED
- ON_HOLD
- READY_TO_SHIP
- SHIPPED

## Test run requirements

Existing Test Runs fields:

- testID
- itemSerialNo
- itemNo
- productName
- orderNo
- orderDate
- testDate
- testPerson
- testReportFile
- testPictures
- testNotes

Improve the design while preserving the useful historical fields.

Recommended Test Runs fields:

- testID
- unitID
- productID
- orderID
- itemSerialNo
- itemNo
- productName
- orderNo
- orderDate
- testDate
- testPerson
- testResult
- testReportFileName
- testReportS3Key
- testReportBucket
- testPictures
- testNotes
- createdAt
- updatedAt

Suggested test results:

- IN_PROGRESS
- PASS
- FAIL
- RETEST_REQUIRED
- CANCELLED

Important rules:

- One physical unit can have many test runs.
- A failed test must not overwrite an earlier or later test.
- Historical test data should remain unchanged.
- Keep `itemNo`, `productName`, `itemSerialNo`, `orderNo`, and `orderDate` in test_runs as snapshots, even though some are technically redundant.
- `testReportS3Key` should store the S3 object key, not a permanent public URL.
- The S3 bucket should remain private.
- The application can later generate presigned URLs.
- For version 1, `testPictures` may be stored as PostgreSQL JSONB containing an array of S3 object metadata. Example:

```json
[
  {
    "file_name": "front.jpg",
    "s3_key": "qc-pictures/2026/09/73204-3010/test-1001/front.jpg"
  },
  {
    "file_name": "control-panel.jpg",
    "s3_key": "qc-pictures/2026/09/73204-3010/test-1001/control-panel.jpg"
  }
]
```

## What I want from you

Design the PostgreSQL architecture and return:

1. A clear explanation of the four tables and their responsibilities.
2. Primary keys.
3. Foreign keys.
4. UNIQUE constraints.
5. NOT NULL decisions.
6. CHECK constraints.
7. Recommended PostgreSQL data types.
8. Recommended indexes.
9. Relationship cardinalities.
10. Delete/update behavior for foreign keys.
11. Which fields are normalized references versus historical snapshot fields.
12. Any assumptions or risks.
13. A text ER diagram.
14. A final proposed schema table showing every column, data type, nullable status, default, and purpose.

Use PostgreSQL naming conventions with lowercase snake_case names.

Prefer PostgreSQL identity columns such as:

```sql
BIGINT GENERATED BY DEFAULT AS IDENTITY
```

or explain if UUID primary keys would be better.

Do not generate Django code yet. Do not generate React code yet. The goal of this prompt is to finalize the database design before implementation.
