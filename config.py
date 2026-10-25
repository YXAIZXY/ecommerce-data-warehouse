"""项目全局配置：路径、数据规模、引擎选择。

设计说明：
- 本地离线验证使用 DuckDB（免服务器、OLAP 分析引擎、标准 SQL）
- 生产/面试对标 MySQL 8.0，本工程 SQL 均按标准 SQL 编写，
  除建表自增主键、个别日期函数外与 MySQL 方言基本一致，可平滑迁移。
"""
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据源目录（模拟业务库导出的 CSV）
RAW_DIR = BASE_DIR / "data" / "raw"
# 数仓本地库文件（DuckDB）
WAREHOUSE_DB = BASE_DIR / "data" / "warehouse.duckdb"
# SQL 目录
SQL_DIR = BASE_DIR / "sql"
# 报表输出目录
OUTPUT_DIR = BASE_DIR / "output"

# 数据规模（造数规模，可按需调整）
N_USERS = 300          # 用户数
N_PRODUCTS = 60        # 商品数
N_ORDERS = 3000        # 订单数
DATE_START = "2026-07-01"   # 业务数据起始日期
DATE_END = "2026-09-30"     # 业务数据结束日期

# ETL 运行日期（业务分区）
ETL_DATE = "2026-09-30"

# 数据库连接：优先 MySQL，未配置则回退 DuckDB
# 切 MySQL 时：pip install pymysql 后，将 USE_MYSQL 置 True 并填下方连接串
# 默认 False（DuckDB 免安装，克隆即跑）；本机已装 MySQL 时可置 True（已实测跑通）
USE_MYSQL = False
MYSQL_CONF = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root123",
    "database": "ecommerce_dw",
}


def ensure_dirs() -> None:
    for d in (RAW_DIR, OUTPUT_DIR, BASE_DIR / "data"):
        d.mkdir(parents=True, exist_ok=True)
