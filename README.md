# 电商交易离线数仓（E-commerce Offline Data Warehouse）

一个完整的离线数仓实战项目：从业务数据造数 → ODS → DWD → DWS → ADS 四层建模，
用标准 SQL 完成清洗、去重、维度退化、主题聚合与核心指标计算，输出可视化报表。

**技术栈**：Python · SQL · MySQL 8.0（对标）· DuckDB（本地验证引擎）· Pandas · Matplotlib

---

## 一、整体架构

```
┌───────────────┐
│  业务系统模拟  │  Faker 造数（用户/商品/订单/明细/支付）→ CSV
└──────┬────────┘
       │ ① 全量同步（真实环境用 DataX / Sqoop，本项目 pandas 模拟）
┌──────▼────────┐
│  ODS 贴源层   │  保留业务原貌，追加 etl_date 分区字段
└──────┬────────┘
       │ ② 清洗 / 去重 / 维度退化（SQL）
┌──────▼────────┐
│  DWD 明细层   │  明细宽表（订单关联商品/支付，维度冗余）
└──────┬────────┘
       │ ③ 按日 / 按主题聚合（SQL）
┌──────▼────────┐
│  DWS 汇总层   │  交易主题 / 用户主题 / 商品主题
└──────┬────────┘
       │ ④ 核心指标计算（SQL）
┌──────▼────────┐
│  ADS 应用层   │  日交易指标 / 复购分析 / 热销 TOP10
└──────┬────────┘
       │ ⑤ 可视化
┌──────▼────────┐
│  报表 / 图表  │  Matplotlib 图表 + Markdown 日报
└───────────────┘
```

---

## 二、数仓分层设计

| 分层 | 职责 | 表 |
| --- | --- | --- |
| **ODS 贴源层** | 原始数据，保留业务原貌，追加 `etl_date` 分区字段 | `ods_user_info` `ods_product_info` `ods_order_info` `ods_order_detail` `ods_payment_info` |
| **DWD 明细层** | 清洗脏数据、去重、维度退化，产出明细宽表 | `dwd_user_info` `dwd_product_info` `dwd_order_info` `dwd_order_detail`（宽表）`dwd_payment_info` |
| **DWS 汇总层** | 按日 / 按主题做轻度汇总 | `dws_trade_topic_1d` `dws_user_topic_1d` `dws_product_topic_1d` |
| **ADS 应用层** | 面向报表的最终指标 | `ads_trade_day_stats` `ads_user_repurchase` `ads_product_top` |

**核心指标口径**（统一在 ADS 层定义，保证口径一致）：

- **GMV** = 已支付订单金额之和（`SUM(pay_amount)`，订单维度）
- **客单价** = GMV / 支付订单数
- **支付转化率** = 支付订单数 / 下单订单数
- **复购率** = 消费订单数 ≥ 2 的用户数 / 全部下单用户数

---

## 三、目录结构

```
ecommerce-data-warehouse/
├── config.py                  # 全局配置（路径/数据规模/引擎）
├── requirements.txt
├── sql/
│   ├── ddl.sql                # 四层建表 DDL
│   └── etl/
│       ├── dwd.sql            # ODS -> DWD 清洗转换
│       ├── dws.sql            # DWD -> DWS 聚合
│       └── ads.sql            # DWS -> ADS 指标
└── scripts/
    ├── 01_generate_data.py    # Faker 造数 -> CSV
    ├── 02_create_tables.py    # 执行 DDL
    ├── 03_etl_ods.py          # CSV -> ODS
    ├── 04_etl_dwd.py          # ODS -> DWD
    ├── 05_etl_dws.py          # DWD -> DWS
    ├── 06_etl_ads.py          # DWS -> ADS
    ├── 07_scheduler.py        # 按依赖顺序调度全流程
    └── 08_report.py           # 查询 ADS 生成报表/图表
```

---

## 四、快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 造数 + 建表
python scripts/01_generate_data.py
python scripts/02_create_tables.py

# 3. 一键跑完四层 ETL（等价于依次执行 03~06）
python scripts/07_scheduler.py

# 4. 生成报表与图表
python scripts/08_report.py
```

跑完后在 `output/` 目录查看 `report.md`（数据日报）与 `charts.png`（GMV 趋势 + 热销榜）。

---

## 五、核心设计点（面试亮点）

1. **分层解耦**：ODS/DWD/DWS/ADS 职责单一，上层只依赖紧邻下层，口径统一、易于回溯与复用。
2. **维度退化**：`dwd_order_detail` 把商品类目/品牌、订单状态、支付渠道冗余进明细宽表，减少下游 join，提升聚合性能。
3. **分区设计**：事实表按「业务发生日期」分区（`etl_date` 由业务时间戳推导），维度表按加载日期快照；支持按日增量/回溯重跑。
4. **幂等重跑**：每层 ETL 执行前先清空本层目标表，全量覆盖，重复执行不产生重复数据。
5. **指标口径统一**：GMV、客单价、转化率、复购率等只允许在 ADS 层定义（原子指标派生），避免各报表口径打架。
6. **明细重复计数规避**：交易/用户主题从「订单维度」聚合（`COUNT(DISTINCT order_id)`），而非从明细宽表聚合，避免一行订单多行明细导致的金额重复累加。
7. **窗口函数选型**：热销榜用 `ROW_NUMBER()` 保证每日期恰好 10 条；若需并列保留名次则用 `RANK()`/`DENSE_RANK()`。
8. **金额精度**：金额字段生产环境用 `DECIMAL(10,2)` 规避浮点误差（本地 DuckDB 验证用 `DOUBLE` 便于 pandas 对接）。

---

## 六、技术选型说明

- **本地验证引擎用 DuckDB**：免安装、OLAP 分析、标准 SQL，适合离线开发验证；生产/面试对标 **MySQL 8.0**。
- **切 MySQL**：`pip install pymysql` 后，把 `config.py` 中 `USE_MYSQL=True` 并填连接信息即可（DDL/ETL 均为标准 SQL，方言差异见下）。
- **方言差异点**：MySQL 建表用 `AUTO_INCREMENT` 自增主键、金额用 `DECIMAL`、日期函数用 `DATE_FORMAT`；Hive/Spark 用 `INSERT OVERWRITE` 分区表。本工程已尽量保持方言中立。

---

## 七、面试高频追问与答题要点

**Q1：为什么分这么多层？直接一步算指标不行吗？**
分层是为了解耦与复用：原始数据（ODS）和加工数据（DWD/DWS）分离，业务变更只影响对应层；汇总结果可被多个报表复用，避免重复计算；口径在 ADS 层统一，排查问题可逐层回溯定位。

**Q2：ODS 和 DWD 的区别？**
ODS 尽量贴源、不加工，只追加分区字段，方便追溯原始数据；DWD 做清洗（过滤脏数据）、去重、维度退化，把数据加工成规范明细。

**Q3：什么是维度退化？为什么建宽表？**
把常用的维度属性（类目、品牌、渠道）冗余到事实表明细行，牺牲少量存储换取查询时少 join、更快。适用于维度属性稳定、查询频繁的场景。

**Q4：怎么保证 ETL 幂等 / 可重跑？**
每层执行前先清空本层目标表（`DELETE`），再全量重算写入；或按分区日期 `INSERT OVERWRITE` 覆盖指定分区，避免重复累加。

**Q5：GMV 为什么从订单维度算，不从明细宽表算？**
一张订单含多行明细，若对明细宽表直接 `SUM(pay_amount)` 会把同一笔订单金额重复累加多份。应从订单/支付维度 `COUNT(DISTINCT order_id)` 聚合。

**Q6：金额为什么用 DECIMAL 不用 FLOAT/DOUBLE？**
浮点数是二进制近似，`0.1 + 0.2 != 0.3` 会产生精度误差；金额必须精确，用定点数 `DECIMAL(10,2)`。Hive/Spark 中也可用 `decimal` 或乘以 100 转整数存储。

**Q7：RANK / ROW_NUMBER / DENSE_RANK 区别？**
`ROW_NUMBER` 唯一序号无并列；`RANK` 并列同名次、后续名次跳号；`DENSE_RANK` 并列同名次、后续名次连续不跳号。

**Q8：数据量大了慢怎么办？**
加索引、分区裁剪（按 `etl_date` 只扫相关分区）、避免 `SELECT *`、用 `EXPLAIN` 看执行计划、大表 join 先过滤再关联、小表 broadcast。

**Q9：这套 SQL 迁移到 Hive/Spark 要改什么？**
`INSERT INTO` 改 `INSERT OVERWRITE TABLE ... PARTITION(dt)`；日期函数 `DATE`/`DATE_FORMAT` 对应 Hive 的 `to_date`/`date_format`；自增主键改为由数仓侧生成；`DECIMAL` 一致。

---

## 八、可扩展方向

- 引入 **Airflow / DolphinScheduler** 做真正的 DAG 定时调度
- 接入 **缓慢变化维（SCD Type 2）** 处理用户等级、商品价格的历史变化
- 迁移到 **Hive + Spark** 跑大数据量，验证分区与倾斜优化
- 增加 **Superset / FineBI** 做交互式可视化大屏
