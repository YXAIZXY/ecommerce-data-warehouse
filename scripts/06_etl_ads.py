"""06 ADS 应用层 ETL：执行 ads.sql，产出报表核心指标。"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
from db import get_conn, run_sql_file, row_count, truncate_tables

ADS_TABLES = ("ads_trade_day_stats", "ads_user_repurchase", "ads_product_top")


def main() -> None:
    conn = get_conn()
    truncate_tables(conn, ADS_TABLES)
    run_sql_file(conn, config.SQL_DIR / "etl" / "ads.sql")
    for t in ADS_TABLES:
        print(f"   {t:22s} {row_count(conn, t)} 行")
    conn.close()
    print("[06] ADS 层指标计算完成")


if __name__ == "__main__":
    main()
