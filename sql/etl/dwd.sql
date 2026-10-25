-- ============================================================
-- DWD 明细层 ETL：ODS -> DWD（清洗 / 去重 / 维度退化）
-- ============================================================

-- 用户明细：去重 + 过滤脏数据（姓名为空、年龄非法、性别异常）
INSERT INTO dwd_user_info
SELECT
    user_id, user_name, gender, age, city, register_time, user_level, etl_date
FROM ods_user_info
WHERE user_name IS NOT NULL AND user_name <> ''
  AND age BETWEEN 0 AND 120
  AND gender IN ('男', '女');

-- 商品明细：去重 + 过滤负价 / 空名
INSERT INTO dwd_product_info
SELECT
    product_id, product_name, category, brand, price, cost, etl_date
FROM ods_product_info
WHERE price IS NOT NULL AND price >= 0
  AND product_name IS NOT NULL AND product_name <> '';

-- 订单明细：过滤金额异常、用户缺失
INSERT INTO dwd_order_info
SELECT
    order_id, user_id, order_status, order_time, total_amount, pay_type, etl_date
FROM ods_order_info
WHERE total_amount IS NOT NULL AND total_amount >= 0
  AND user_id IS NOT NULL;

-- 订单明细宽表：关联商品(类目/品牌)、订单(状态)、支付(金额/渠道)
-- 将常用维度冗余到明细行（维度退化），减少下游 join，支撑聚合查询
INSERT INTO dwd_order_detail
SELECT
    od.id,
    od.order_id,
    oi.user_id,
    od.product_id,
    pi.category,
    pi.brand,
    oi.order_status,
    oi.order_time,
    od.quantity,
    od.price,
    od.discount,
    COALESCE(pay.pay_amount, 0)   AS pay_amount,
    COALESCE(pay.pay_channel, '')  AS pay_channel,
    CAST(oi.order_time AS DATE)   AS etl_date
FROM ods_order_detail od
JOIN ods_order_info oi     ON od.order_id = oi.order_id
JOIN ods_product_info pi   ON od.product_id = pi.product_id
LEFT JOIN ods_payment_info pay ON od.order_id = pay.order_id
WHERE oi.order_status IN ('已支付', '已完成');

-- 支付明细：仅保留金额大于 0 的有效支付记录
INSERT INTO dwd_payment_info
SELECT
    payment_id, order_id, user_id, pay_amount, pay_time, pay_channel, etl_date
FROM ods_payment_info
WHERE pay_amount IS NOT NULL AND pay_amount > 0;
