"""数据库连接与 SQL 执行工具。

本地离线验证使用 DuckDB；切 MySQL 时无需改动 ETL 脚本，
只需将 config.USE_MYSQL 置 True 并填写连接信息（见 README「技术选型」）。
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import duckdb

import config


def get_conn() -> duckdb.DuckDBPyConnection:
    config.ensure_dirs()
    return duckdb.connect(str(config.WAREHOUSE_DB))


def run_sql_file(conn: duckdb.DuckDBPyConnection, path) -> None:
    """按分号拆分执行 SQL 文件，跳过注释与空语句。"""
    sql = Path(path).read_text(encoding="utf-8")
    for stmt in sql.split(";"):
        lines = [
            ln for ln in stmt.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if lines:
            conn.execute("\n".join(lines))
            conn.fetchall()


def scalar(conn, sql: str, params=None):
    """执行查询并返回第一行第一列（用 fetchall 完整消费结果）。"""
    if params:
        return conn.execute(sql, params).fetchall()[0][0]
    return conn.execute(sql).fetchall()[0][0]


def row_count(conn, table: str) -> int:
    return scalar(conn, f"SELECT COUNT(*) FROM {table}")


def truncate_tables(conn, tables) -> None:
    """清空目标表，保证 ETL 可幂等重跑（全量覆盖，不重复累加）。"""
    for t in tables:
        conn.execute(f"DELETE FROM {t}")
        conn.fetchall()
