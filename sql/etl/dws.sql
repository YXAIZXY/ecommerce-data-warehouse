-- ============================================================
-- DWS 汇总层 ETL：DWD -> DWS（按日 / 按主题聚合）
-- ============================================================

-- 交易主题日汇总（订单维度，避免明细行重复计数）
INSERT INTO dws_trade_topic_1d
SELECT
    o.etl_date                            AS dt,
    COUNT(DISTINCT o.order_id)            AS order_count,
    COUNT(DISTINCT o.user_id)             AS order_user_count,
    COUNT(DISTINCT p.order_id)            AS pay_order_count,
    COUNT(DISTINCT p.user_id)             AS pay_user_count,
    COALESCE(SUM(p.pay_amount), 0)        AS gmv,
    CASE WHEN COUNT(DISTINCT p.order_id) > 0
         THEN SUM(p.pay_amount) / COUNT(DISTINCT p.order_id)
         ELSE 0 END                       AS avg_order_amount
FROM dwd_order_info o
LEFT JOIN dwd_payment_info p
    ON o.order_id = p.order_id
GROUP BY o.etl_date;

-- 用户主题日汇总（订单维度聚合用户消费行为）
INSERT INTO dws_user_topic_1d
SELECT
    o.etl_date                            AS dt,
    o.user_id,
    COUNT(DISTINCT o.order_id)            AS order_count,
    COALESCE(SUM(p.pay_amount), 0)        AS pay_amount
FROM dwd_order_info o
LEFT JOIN dwd_payment_info p
    ON o.order_id = p.order_id
GROUP BY o.etl_date, o.user_id;

-- 商品主题日汇总（明细维度逐行汇总，无重复计数）
INSERT INTO dws_product_topic_1d
SELECT
    etl_date                   AS dt,
    product_id,
    MAX(category)              AS category,
    MAX(brand)                 AS brand,
    SUM(quantity)              AS sale_quantity,
    SUM(price * quantity - discount) AS sale_amount,
    COUNT(DISTINCT user_id)    AS buyer_count
FROM dwd_order_detail
GROUP BY etl_date, product_id;
