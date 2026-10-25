-- ============================================================
-- ADS 应用层 ETL：DWS -> ADS（面向报表的核心指标）
-- ============================================================

-- 每日交易核心指标（含支付转化率）
INSERT INTO ads_trade_day_stats
SELECT
    dt,
    gmv,
    order_count,
    pay_user_count,
    avg_order_amount,
    CASE WHEN order_count > 0
         THEN pay_order_count * 1.0 / order_count
         ELSE 0 END AS pay_conversion_rate
FROM dws_trade_topic_1d;

-- 用户复购分析：全量维度下，消费订单数 >= 2 视为复购
INSERT INTO ads_user_repurchase
SELECT
    DATE '2026-09-30'                                AS dt,
    COUNT(DISTINCT user_id)                          AS total_buyer,
    COUNT(DISTINCT CASE WHEN order_count >= 2 THEN user_id END) AS repurchase_buyer,
    CASE WHEN COUNT(DISTINCT user_id) > 0
         THEN COUNT(DISTINCT CASE WHEN order_count >= 2 THEN user_id END) * 1.0
              / COUNT(DISTINCT user_id)
         ELSE 0 END                                  AS repurchase_rate
FROM (
    SELECT user_id, SUM(order_count) AS order_count
    FROM dws_user_topic_1d
    GROUP BY user_id
) t;

-- 商品热销 TOP 榜（每日销量前 10，用 ROW_NUMBER 保证每日期恰好 10 条）
-- 注：RANK/DENSE_RANK 遇并列会超 10 条，此处用 ROW_NUMBER 保证榜单长度固定
INSERT INTO ads_product_top
SELECT
    dt, rn, product_id, product_name, category, sale_quantity, sale_amount
FROM (
    SELECT
        s.dt,
        ROW_NUMBER() OVER (PARTITION BY s.dt ORDER BY s.sale_quantity DESC, s.product_id) AS rn,
        s.product_id,
        p.product_name,
        p.category,
        s.sale_quantity,
        s.sale_amount
    FROM dws_product_topic_1d s
    LEFT JOIN dwd_product_info p ON s.product_id = p.product_id
    WHERE s.sale_quantity > 0
) t
WHERE rn <= 10;
