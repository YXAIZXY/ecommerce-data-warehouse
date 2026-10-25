"""02 建表：执行 DDL，创建 ODS/DWD/DWS/ADS 四层全部表。

按 config.USE_MYSQL 自动选择：
  * False -> sql/ddl.sql（DuckDB 本地验证）
  * True  -> sql/ddl_mysql.sql（MySQL 8.0）
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
from db import get_conn, run_sql_file, USE_MYSQL


def main() -> None:
    ddl = "ddl_mysql.sql" if USE_MYSQL else "ddl.sql"
    conn = get_conn()
    run_sql_file(conn, config.SQL_DIR / ddl)
    print(f"[02] 建表完成（引擎：{'MySQL' if USE_MYSQL else 'DuckDB'}，DDL：{ddl}）")
    if hasattr(conn, "close"):
        conn.close()
    else:
        conn.dispose()


if __name__ == "__main__":
    main()
