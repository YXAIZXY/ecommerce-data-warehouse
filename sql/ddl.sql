-- ============================================================
-- 电商交易离线数仓 建表 DDL（四层：ODS / DWD / DWS / ADS）
-- 说明：
--   * 本地离线验证引擎为 DuckDB，SQL 为标准 SQL；
--   * 生产/面试对标 MySQL 8.0 与 Hive，方言差异点已注释标注；
--   * 金额字段本地用 DOUBLE 便于 pandas 对接，生产环境建议 DECIMAL(10,2)，
--     以规避浮点精度问题（见 README「技术选型」）。
-- ============================================================

-- ============ 一、ODS 贴源层（原始数据，保留业务原貌，追加 etl_date 分区字段） ============

CREATE TABLE IF NOT EXISTS ods_user_info (
    user_id        BIGINT,
    user_name      VARCHAR,
    gender         VARCHAR,
    age            INT,
    city           VARCHAR,
    register_time  TIMESTAMP,
    user_level     VARCHAR,
    etl_date       DATE
);

CREATE TABLE IF NOT EXISTS ods_product_info (
    product_id    BIGINT,
    product_name  VARCHAR,
    category      VARCHAR,
    brand         VARCHAR,
    price         DOUBLE,
    cost          DOUBLE,
    etl_date      DATE
);

CREATE TABLE IF NOT EXISTS ods_order_info (
    order_id      BIGINT,
    user_id       BIGINT,
    order_status  VARCHAR,
    order_time    TIMESTAMP,
    total_amount  DOUBLE,
    pay_type      VARCHAR,
    etl_date      DATE
);

CREATE TABLE IF NOT EXISTS ods_order_detail (
    id           BIGINT,
    order_id     BIGINT,
    product_id   BIGINT,
    quantity     INT,
    price        DOUBLE,
    discount     DOUBLE,
    etl_date     DATE
);

CREATE TABLE IF NOT EXISTS ods_payment_info (
    payment_id   BIGINT,
    order_id     BIGINT,
    user_id      BIGINT,
    pay_amount   DOUBLE,
    pay_time     TIMESTAMP,
    pay_channel  VARCHAR,
    etl_date     DATE
);

-- ============ 二、DWD 明细层（清洗 / 去重 / 维度退化，明细宽表） ============

-- 用户明细：去重 + 剔除脏数据（年龄非法、姓名为空）
CREATE TABLE IF NOT EXISTS dwd_user_info (
    user_id        BIGINT,
    user_name      VARCHAR,
    gender         VARCHAR,
    age            INT,
    city           VARCHAR,
    register_time  TIMESTAMP,
    user_level     VARCHAR,
    etl_date       DATE
);

-- 商品明细：去重 + 剔除价格为负/空记录
CREATE TABLE IF NOT EXISTS dwd_product_info (
    product_id    BIGINT,
    product_name  VARCHAR,
    category      VARCHAR,
    brand         VARCHAR,
    price         DOUBLE,
    cost          DOUBLE,
    etl_date      DATE
);

-- 订单明细（清洗）：剔除金额为负、用户缺失的脏数据
CREATE TABLE IF NOT EXISTS dwd_order_info (
    order_id      BIGINT,
    user_id       BIGINT,
    order_status  VARCHAR,
    order_time    TIMESTAMP,
    total_amount  DOUBLE,
    pay_type      VARCHAR,
    etl_date      DATE
);

-- 订单明细宽表：order_detail 关联 商品(类目/品牌)、订单(状态/支付方式)、
-- 支付(金额/渠道)，将维度冗余到明细行（维度退化），支撑下游聚合查询
CREATE TABLE IF NOT EXISTS dwd_order_detail (
    id            BIGINT,
    order_id      BIGINT,
    user_id       BIGINT,
    product_id    BIGINT,
    category      VARCHAR,
    brand         VARCHAR,
    order_status  VARCHAR,
    order_time    TIMESTAMP,
    quantity      INT,
    price         DOUBLE,
    discount      DOUBLE,
    pay_amount    DOUBLE,
    pay_channel   VARCHAR,
    etl_date      DATE
);

-- 支付明细：仅保留已支付订单的支付记录（清洗掉未支付订单的脏支付数据）
CREATE TABLE IF NOT EXISTS dwd_payment_info (
    payment_id   BIGINT,
    order_id     BIGINT,
    user_id      BIGINT,
    pay_amount   DOUBLE,
    pay_time     TIMESTAMP,
    pay_channel  VARCHAR,
    etl_date     DATE
);

-- ============ 三、DWS 汇总层（按日 / 按主题聚合） ============

-- 交易主题日汇总（订单维度，避免明细行重复计数）
CREATE TABLE IF NOT EXISTS dws_trade_topic_1d (
    dt               DATE,
    order_count      BIGINT,   -- 下单订单数
    order_user_count BIGINT,   -- 下单用户数
    pay_order_count  BIGINT,   -- 支付订单数
    pay_user_count   BIGINT,   -- 支付用户数
    gmv              DOUBLE,   -- 成交总额（已支付金额）
    avg_order_amount DOUBLE    -- 客单价 = gmv / 支付订单数
);

-- 用户主题日汇总
CREATE TABLE IF NOT EXISTS dws_user_topic_1d (
    dt           DATE,
    user_id      BIGINT,
    order_count  BIGINT,
    pay_amount   DOUBLE
);

-- 商品主题日汇总
CREATE TABLE IF NOT EXISTS dws_product_topic_1d (
    dt            DATE,
    product_id    BIGINT,
    category      VARCHAR,
    brand         VARCHAR,
    sale_quantity BIGINT,
    sale_amount   DOUBLE,
    buyer_count   BIGINT
);

-- ============ 四、ADS 应用层（面向报表的核心指标） ============

-- 每日交易核心指标
CREATE TABLE IF NOT EXISTS ads_trade_day_stats (
    dt                  DATE,
    gmv                 DOUBLE,
    order_count         BIGINT,
    pay_user_count      BIGINT,
    avg_order_amount    DOUBLE,
    pay_conversion_rate DOUBLE
);

-- 用户复购分析（累计消费用户中复购人数 / 复购率）
CREATE TABLE IF NOT EXISTS ads_user_repurchase (
    dt               DATE,
    total_buyer      BIGINT,
    repurchase_buyer BIGINT,
    repurchase_rate  DOUBLE
);

-- 商品热销 TOP 榜
CREATE TABLE IF NOT EXISTS ads_product_top (
    dt            DATE,
    top_rank      BIGINT,
    product_id    BIGINT,
    product_name  VARCHAR,
    category      VARCHAR,
    sale_quantity BIGINT,
    sale_amount   DOUBLE
);
