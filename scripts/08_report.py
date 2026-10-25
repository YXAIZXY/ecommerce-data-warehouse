"""08 报表：查询 ADS 层指标，输出控制台报表 + 图表 + Markdown 报告。"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
import pandas as pd

import config
from db import get_conn, scalar


def latest_dt(conn, table: str, col: str = "dt") -> str:
    return scalar(conn, f"SELECT MAX({col}) FROM {table}")


def print_summary(conn) -> None:
    print("=" * 56)
    print("【ADS 核心指标汇总】")
    print("=" * 56)

    total = conn.execute("""
        SELECT SUM(gmv), SUM(order_count)
        FROM ads_trade_day_stats
    """).fetchall()[0]
    distinct_payers = scalar(
        conn, "SELECT COUNT(DISTINCT user_id) FROM dwd_payment_info"
    )
    print(f"  累计 GMV        : {total[0]:,.2f} 元")
    print(f"  累计订单量      : {int(total[1]):,} 单")
    print(f"  累计支付用户数  : {distinct_payers:,} 人（去重）")

    rate = conn.execute("""
        SELECT AVG(pay_conversion_rate), AVG(avg_order_amount)
        FROM ads_trade_day_stats
    """).fetchall()[0]
    print(f"  平均支付转化率  : {rate[0] * 100:.2f}%")
    print(f"  平均客单价      : {rate[1]:,.2f} 元")

    rep = conn.execute(
        "SELECT total_buyer, repurchase_buyer, repurchase_rate "
        "FROM ads_user_repurchase ORDER BY dt DESC LIMIT 1"
    ).fetchall()[0]
    if rep:
        print(f"  复购人数        : {int(rep[1]):,} / {int(rep[0]):,}")
        print(f"  复购率          : {rep[2] * 100:.2f}%")


def top_products(conn, dt, limit: int = 10) -> pd.DataFrame:
    return conn.execute(
        f"""
        SELECT rank, product_id, product_name, category, sale_quantity, sale_amount
        FROM ads_product_top
        WHERE dt = ? AND rank <= ?
        ORDER BY rank
        """, [dt, limit]
    ).df()


def make_charts(conn, dt) -> None:
    # 1) 每日 GMV 趋势
    daily = conn.execute(
        "SELECT dt, gmv, order_count FROM ads_trade_day_stats ORDER BY dt"
    ).df()
    daily["dt"] = pd.to_datetime(daily["dt"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    ax = axes[0]
    ax.plot(daily["dt"], daily["gmv"], marker="o", linewidth=1.5, color="#2E75B6")
    ax.set_title("每日 GMV 趋势")
    ax.set_xlabel("日期")
    ax.set_ylabel("GMV（元）")
    ax.grid(alpha=0.3)
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(45)

    # 2) 热销 TOP10
    top = top_products(conn, dt)
    ax = axes[1]
    ax.barh(top["product_name"].astype(str)[::-1], top["sale_quantity"][::-1],
            color="#548235")
    ax.set_title(f"热销商品 TOP10（{dt}）")
    ax.set_xlabel("销量")
    fig.tight_layout()
    fig.savefig(config.OUTPUT_DIR / "charts.png", dpi=120)
    plt.close(fig)
    print(f"   图表已保存：{config.OUTPUT_DIR / 'charts.png'}")


def write_markdown(conn, dt) -> None:
    daily = conn.execute(
        "SELECT dt, gmv, order_count, pay_conversion_rate "
        "FROM ads_trade_day_stats ORDER BY dt"
    ).df()
    daily["dt"] = pd.to_datetime(daily["dt"])
    top = top_products(conn, dt, limit=10)

    lines = [
        "# 电商交易数仓 · 数据日报",
        "",
        f"- 数据区间：{daily['dt'].min():%Y-%m-%d} ~ {daily['dt'].max():%Y-%m-%d}",
        f"- 累计 GMV：{daily['gmv'].sum():,.2f} 元",
        f"- 累计订单：{int(daily['order_count'].sum()):,} 单",
        "",
        "## 热销商品 TOP10",
        "",
        "| 排名 | 商品 | 类目 | 销量 | 销售额 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, r in top.iterrows():
        lines.append(
            f"| {int(r['rank'])} | {r['product_name']} | {r['category']} "
            f"| {int(r['sale_quantity'])} | {r['sale_amount']:,.2f} |"
        )
    lines.append("")
    lines.append("![图表](charts.png)")

    (config.OUTPUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"   Markdown 报告已保存：{config.OUTPUT_DIR / 'report.md'}")


def main() -> None:
    conn = get_conn()
    dt = latest_dt(conn, "ads_trade_day_stats")
    print_summary(conn)
    print("\n【热销商品 TOP10】")
    print(top_products(conn, dt).to_string(index=False))
    print()
    make_charts(conn, dt)
    write_markdown(conn, dt)
    conn.close()
    print("\n[08] 报表生成完成")


if __name__ == "__main__":
    main()
