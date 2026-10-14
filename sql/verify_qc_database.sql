-- Run after seed_qc_data. Expected: products, order 175899,
-- serial 73204-3010.

SELECT item_no, product_name, voltage, wattage
FROM products
ORDER BY item_no;

SELECT i.order_no, i.item_no, i.serial_no, i.date_received, i.container_batch, p.product_name
FROM product_items i
JOIN products p ON p.product_id = i.product_id;

SELECT i.serial_no, i.item_no, i.product_name, i.order_no, q.qc_status, q.qc_approved
FROM product_items i
JOIN qc_records q ON q.product_item_id = i.product_item_id
WHERE i.serial_no = '73204-3010';

SELECT i.serial_no, q.qc_status
FROM product_items i
JOIN qc_records q ON q.product_item_id = i.product_item_id
WHERE q.qc_status = 'QC_PASSED';

SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('products', 'product_items', 'qc_records')
ORDER BY tablename, indexname;
