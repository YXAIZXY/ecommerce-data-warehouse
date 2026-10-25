"""05 DWS 汇总层 ETL：执行 dws.sql，按日/主题聚合。"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
from db import get_conn, run_sql_file, row_count, truncate_tables, close_conn

DWS_TABLES = ("dws_trade_topic_1d", "dws_user_topic_1d", "dws_product_topic_1d")


def main() -> None:
    conn = get_conn()
    truncate_tables(conn, DWS_TABLES)
    run_sql_file(conn, config.SQL_DIR / "etl" / "dws.sql")
    for t in DWS_TABLES:
        print(f"   {t:22s} {row_count(conn, t)} 行")
    close_conn(conn)
    print("[05] DWS 层汇总完成")


if __name__ == "__main__":
    main()
