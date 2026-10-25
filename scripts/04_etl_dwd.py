"""04 DWD 明细层 ETL：执行 dwd.sql，完成清洗 / 去重 / 维度退化。"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
from db import get_conn, run_sql_file, row_count, truncate_tables, close_conn

DWD_TABLES = ("dwd_user_info", "dwd_product_info", "dwd_order_info",
              "dwd_order_detail", "dwd_payment_info")


def main() -> None:
    conn = get_conn()
    truncate_tables(conn, DWD_TABLES)
    run_sql_file(conn, config.SQL_DIR / "etl" / "dwd.sql")
    for t in DWD_TABLES:
        print(f"   {t:20s} {row_count(conn, t)} 行")
    close_conn(conn)
    print("[04] DWD 层清洗完成")


if __name__ == "__main__":
    main()
