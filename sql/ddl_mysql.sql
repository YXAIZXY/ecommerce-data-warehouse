-- ============================================================
-- 电商交易离线数仓 建表 DDL（MySQL 8.0 版）
-- 与 sql/ddl.sql（DuckDB 本地验证版）逻辑一致，差异点：
--   * 金额字段用 DECIMAL(12,2) 规避浮点误差（DuckDB 版用 DOUBLE 便于 pandas 对接）
--   * 字符串列显式指定 VARCHAR(n)
--   * 时间戳用 DATETIME（避免 TIMESTAMP 的 2038 问题）
--   * 引擎 InnoDB + utf8mb4，主键 + 关联/过滤列建索引
-- ============================================================

-- ============ 一、ODS 贴源层 ============

CREATE TABLE IF NOT EXISTS ods_user_info (
    user_id        BIGINT PRIMARY KEY,
    user_name      VARCHAR(50),
    gender         VARCHAR(10),
    age            INT,
    city           VARCHAR(50),
    register_time  DATETIME,
    user_level     VARCHAR(20),
    etl_date       DATE,
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ods_product_info (
    product_id    BIGINT PRIMARY KEY,
    product_name  VARCHAR(100),
    category      VARCHAR(20),
    brand         VARCHAR(50),
    price         DECIMAL(12,2),
    cost          DECIMAL(12,2),
    etl_date      DATE,
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ods_order_info (
    order_id      BIGINT PRIMARY KEY,
    user_id       BIGINT,
    order_status  VARCHAR(20),
    order_time    DATETIME,
    total_amount  DECIMAL(12,2),
    pay_type      VARCHAR(20),
    etl_date      DATE,
    KEY idx_user (user_id),
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ods_order_detail (
    id           BIGINT PRIMARY KEY,
    order_id     BIGINT,
    product_id   BIGINT,
    quantity     INT,
    price        DECIMAL(12,2),
    discount     DECIMAL(12,2),
    etl_date     DATE,
    KEY idx_order (order_id),
    KEY idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ods_payment_info (
    payment_id   BIGINT PRIMARY KEY,
    order_id     BIGINT,
    user_id      BIGINT,
    pay_amount   DECIMAL(12,2),
    pay_time     DATETIME,
    pay_channel  VARCHAR(20),
    etl_date     DATE,
    KEY idx_order (order_id),
    KEY idx_user (user_id),
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============ 二、DWD 明细层 ============

CREATE TABLE IF NOT EXISTS dwd_user_info (
    user_id        BIGINT PRIMARY KEY,
    user_name      VARCHAR(50),
    gender         VARCHAR(10),
    age            INT,
    city           VARCHAR(50),
    register_time  DATETIME,
    user_level     VARCHAR(20),
    etl_date       DATE,
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dwd_product_info (
    product_id    BIGINT PRIMARY KEY,
    product_name  VARCHAR(100),
    category      VARCHAR(20),
    brand         VARCHAR(50),
    price         DECIMAL(12,2),
    cost          DECIMAL(12,2),
    etl_date      DATE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dwd_order_info (
    order_id      BIGINT PRIMARY KEY,
    user_id       BIGINT,
    order_status  VARCHAR(20),
    order_time    DATETIME,
    total_amount  DECIMAL(12,2),
    pay_type      VARCHAR(20),
    etl_date      DATE,
    KEY idx_user (user_id),
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dwd_order_detail (
    id            BIGINT PRIMARY KEY,
    order_id      BIGINT,
    user_id       BIGINT,
    product_id    BIGINT,
    category      VARCHAR(20),
    brand         VARCHAR(50),
    order_status  VARCHAR(20),
    order_time    DATETIME,
    quantity      INT,
    price         DECIMAL(12,2),
    discount      DECIMAL(12,2),
    pay_amount    DECIMAL(12,2),
    pay_channel   VARCHAR(20),
    etl_date      DATE,
    KEY idx_order (order_id),
    KEY idx_user (user_id),
    KEY idx_product (product_id),
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dwd_payment_info (
    payment_id   BIGINT PRIMARY KEY,
    order_id     BIGINT,
    user_id      BIGINT,
    pay_amount   DECIMAL(12,2),
    pay_time     DATETIME,
    pay_channel  VARCHAR(20),
    etl_date     DATE,
    KEY idx_order (order_id),
    KEY idx_user (user_id),
    KEY idx_etl_date (etl_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============ 三、DWS 汇总层 ============

CREATE TABLE IF NOT EXISTS dws_trade_topic_1d (
    dt               DATE PRIMARY KEY,
    order_count      BIGINT,
    order_user_count BIGINT,
    pay_order_count  BIGINT,
    pay_user_count   BIGINT,
    gmv              DECIMAL(14,2),
    avg_order_amount DECIMAL(12,2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dws_user_topic_1d (
    dt           DATE,
    user_id      BIGINT,
    order_count  BIGINT,
    pay_amount   DECIMAL(14,2),
    PRIMARY KEY (dt, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dws_product_topic_1d (
    dt            DATE,
    product_id    BIGINT,
    category      VARCHAR(20),
    brand         VARCHAR(50),
    sale_quantity BIGINT,
    sale_amount   DECIMAL(14,2),
    buyer_count   BIGINT,
    PRIMARY KEY (dt, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============ 四、ADS 应用层 ============

CREATE TABLE IF NOT EXISTS ads_trade_day_stats (
    dt                  DATE PRIMARY KEY,
    gmv                 DECIMAL(14,2),
    order_count         BIGINT,
    pay_user_count      BIGINT,
    avg_order_amount    DECIMAL(12,2),
    pay_conversion_rate DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ads_user_repurchase (
    dt               DATE PRIMARY KEY,
    total_buyer      BIGINT,
    repurchase_buyer BIGINT,
    repurchase_rate  DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ads_product_top (
    dt            DATE,
    top_rank      BIGINT,
    product_id    BIGINT,
    product_name  VARCHAR(100),
    category      VARCHAR(20),
    sale_quantity BIGINT,
    sale_amount   DECIMAL(14,2),
    PRIMARY KEY (dt, top_rank)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
