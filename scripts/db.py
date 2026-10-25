"""数据库连接与 SQL 执行工具（DuckDB / MySQL 双引擎）。

通过 config.USE_MYSQL 开关切换：
  * False（默认）：本地离线验证，DuckDB，免安装
  * True：生产/面试对标，MySQL 8.0（经 pymysql + SQLAlchemy）

对上层 ETL 脚本暴露统一接口：get_conn / run_sql_file / scalar / row_count /
truncate_tables / load_dataframe / read_df，脚本无需感知底层引擎。
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config

USE_MYSQL = config.USE_MYSQL

if USE_MYSQL:
    from sqlalchemy import create_engine, text
else:
    import duckdb


def get_conn():
    """返回连接对象：DuckDB 连接 或 MySQL SQLAlchemy Engine。"""
    if USE_MYSQL:
        c = config.MYSQL_CONF
        url = (f"mysql+pymysql://{c['user']}:{c['password']}@"
               f"{c['host']}:{c['port']}/{c['database']}?charset=utf8mb4")
        return create_engine(url)
    config.ensure_dirs()
    return duckdb.connect(str(config.WAREHOUSE_DB))


def _split_statements(sql: str):
    for stmt in sql.split(";"):
        lines = [
            ln for ln in stmt.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if lines:
            yield "\n".join(lines)


def run_sql_file(conn, path) -> None:
    """按分号拆分执行 SQL 文件，跳过注释与空语句。"""
    sql = Path(path).read_text(encoding="utf-8")
    if USE_MYSQL:
        with conn.begin() as c:
            for s in _split_statements(sql):
                c.execute(text(s))
    else:
        for s in _split_statements(sql):
            conn.execute(s)
            conn.fetchall()


def scalar(conn, sql: str, params=None):
    """执行查询并返回第一行第一列。"""
    if USE_MYSQL:
        with conn.connect() as c:
            r = c.execute(text(sql), params or {}).fetchone()
            return r[0] if r else None
    if params:
        return conn.execute(sql, params).fetchall()[0][0]
    return conn.execute(sql).fetchall()[0][0]


def row_count(conn, table: str) -> int:
    return scalar(conn, f"SELECT COUNT(*) FROM {table}")


def truncate_tables(conn, tables) -> None:
    """清空目标表，保证 ETL 可幂等重跑（全量覆盖）。"""
    if USE_MYSQL:
        with conn.begin() as c:
            for t in tables:
                c.execute(text(f"DELETE FROM {t}"))
    else:
        for t in tables:
            conn.execute(f"DELETE FROM {t}")
            conn.fetchall()


def load_dataframe(conn, table: str, df: pd.DataFrame) -> None:
    """把 DataFrame 全量写入表（ODS 接入层用）。"""
    if USE_MYSQL:
        df.to_sql(table, conn, if_exists="append", index=False)
    else:
        conn.register("tmp_load", df)
        conn.execute(f"INSERT INTO {table} SELECT * FROM tmp_load")
        conn.fetchall()
        conn.unregister("tmp_load")


def read_df(conn, sql: str) -> pd.DataFrame:
    """执行查询返回 DataFrame（报表用）。"""
    if USE_MYSQL:
        return pd.read_sql(sql, conn)
    return conn.execute(sql).df()


def close_conn(conn) -> None:
    """关闭连接（DuckDB close / MySQL engine dispose）。"""
    if USE_MYSQL:
        conn.dispose()
    else:
        conn.close()
