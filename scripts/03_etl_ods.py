"""03 ODS 加载：模拟数据接入层，将业务库 CSV 全量同步到 ODS 贴源层。

真实数仓中此步通常由 DataX / Sqoop / Flume / Canal 等工具完成，
本项目用 pandas 读 CSV 模拟"从业务库全量同步"。

分区策略：事实表按「业务发生日期」分区（etl_date 由业务时间戳推导），
维度表 / 无时间戳的表按「加载日期」快照分区。
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config
from db import get_conn, row_count, truncate_tables

# 每张源表 -> (csv, ODS 表, 时间戳列, 收窄 INT 列, 业务日期列)
TABLES = {
    "user_info": {
        "csv": "user_info.csv", "table": "ods_user_info",
        "ts_cols": ["register_time"], "int_cols": ["age"],
        "date_col": "register_time",
    },
    "product_info": {
        "csv": "product_info.csv", "table": "ods_product_info",
        "ts_cols": [], "int_cols": [], "date_col": None,
    },
    "order_info": {
        "csv": "order_info.csv", "table": "ods_order_info",
        "ts_cols": ["order_time"], "int_cols": [], "date_col": "order_time",
    },
    "order_detail": {
        "csv": "order_detail.csv", "table": "ods_order_detail",
        "ts_cols": [], "int_cols": ["quantity"], "date_col": None,
    },
    "payment_info": {
        "csv": "payment_info.csv", "table": "ods_payment_info",
        "ts_cols": ["pay_time"], "int_cols": [], "date_col": "pay_time",
    },
}


def load_one(conn, meta) -> None:
    df = pd.read_csv(config.RAW_DIR / meta["csv"])
    for c in meta["ts_cols"]:
        df[c] = pd.to_datetime(df[c])
    for c in meta["int_cols"]:
        df[c] = df[c].astype("int32")

    if meta["date_col"]:
        df["etl_date"] = df[meta["date_col"]].dt.date
    else:
        df["etl_date"] = pd.to_datetime(config.ETL_DATE).date()

    conn.register("tmp_load", df)
    conn.execute(f"INSERT INTO {meta['table']} SELECT * FROM tmp_load")
    conn.fetchall()
    conn.unregister("tmp_load")


def main() -> None:
    conn = get_conn()
    truncate_tables(conn, [m["table"] for m in TABLES.values()])
    for meta in TABLES.values():
        load_one(conn, meta)
        n = row_count(conn, meta["table"])
        print(f"   {meta['table']:20s} 加载 {n} 行")
    conn.close()
    print("[03] ODS 层加载完成")


if __name__ == "__main__":
    main()
