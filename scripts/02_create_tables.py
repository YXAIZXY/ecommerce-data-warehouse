"""02 建表：执行 DDL，创建 ODS/DWD/DWS/ADS 四层全部表。"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
from db import get_conn, run_sql_file


def main() -> None:
    conn = get_conn()
    run_sql_file(conn, config.SQL_DIR / "ddl.sql")
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "ORDER BY table_name"
    ).fetchall()
    print(f"[02] 建表完成，共 {len(tables)} 张表：")
    for (t,) in tables:
        print(f"   - {t}")
    conn.close()


if __name__ == "__main__":
    main()
