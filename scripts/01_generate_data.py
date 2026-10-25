"""01 数据生成：模拟电商业务库，产出 5 张业务表 CSV。

业务表：
  user_info      用户表
  product_info   商品表
  order_info     订单表
  order_detail   订单明细表
  payment_info   支付表

产出 CSV 到 data/raw/，供后续 ODS 层加载。
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

import config

random.seed(42)
fake = Faker("zh_CN")
Faker.seed(42)

CATEGORIES = ["手机数码", "家用电器", "服饰鞋包", "食品生鲜", "美妆个护", "运动户外"]

# 各类目价格区间，让客单价更贴近真实电商
CATEGORY_PRICE_RANGE = {
    "手机数码": (499, 8999),
    "家用电器": (199, 5999),
    "服饰鞋包": (39, 999),
    "食品生鲜": (9.9, 299),
    "美妆个护": (29, 899),
    "运动户外": (49, 1999),
}
BRANDS = {
    "手机数码": ["华为", "小米", "苹果", "OPPO", "vivo"],
    "家用电器": ["美的", "格力", "海尔", "苏泊尔", "九阳"],
    "服饰鞋包": ["优衣库", "海澜之家", "李宁", "安踏", "森马"],
    "食品生鲜": ["三只松鼠", "良品铺子", "百草味", "蒙牛", "伊利"],
    "美妆个护": ["兰蔻", "欧莱雅", "珀莱雅", "自然堂", "百雀羚"],
    "运动户外": ["迪卡侬", "李宁", "安踏", "骆驼", "探路者"],
}

# 各类目常见商品名（品牌 + 品类词，贴近真实商品）
PRODUCT_NAMES = {
    "手机数码": ["智能手机", "平板电脑", "蓝牙耳机", "智能手表", "笔记本电脑"],
    "家用电器": ["变频空调", "滚筒洗衣机", "电饭煲", "破壁机", "空气净化器"],
    "服饰鞋包": ["休闲外套", "运动鞋", "双肩包", "针织衫", "牛仔裤"],
    "食品生鲜": ["坚果礼盒", "纯牛奶整箱", "新鲜水果", "零食大礼包", "冷冻海鲜"],
    "美妆个护": ["保湿面霜", "洗面奶", "口红", "洗发水", "防晒霜"],
    "运动户外": ["跑步鞋", "登山包", "瑜伽垫", "帐篷", "运动水壶"],
}
PAY_TYPES = ["微信", "支付宝", "银行卡"]
PAY_CHANNELS = ["微信", "支付宝", "银联", "花呗"]

date_start = datetime.strptime(config.DATE_START, "%Y-%m-%d")
date_end = datetime.strptime(config.DATE_END, "%Y-%m-%d")


def rand_dt() -> datetime:
    span = (date_end - date_start).total_seconds()
    return date_start + timedelta(seconds=random.randint(0, int(span)))


def gen_users(n: int) -> pd.DataFrame:
    rows = []
    for uid in range(1, n + 1):
        reg = rand_dt()
        rows.append({
            "user_id": uid,
            "user_name": fake.name(),
            "gender": random.choice(["男", "女"]),
            "age": random.randint(18, 55),
            "city": fake.city(),
            "register_time": reg.strftime("%Y-%m-%d %H:%M:%S"),
            "user_level": random.choices(
                ["普通", "白银", "黄金", "钻石"], weights=[60, 25, 10, 5]
            )[0],
        })
    return pd.DataFrame(rows)


def gen_products(n: int) -> pd.DataFrame:
    rows = []
    for pid in range(1, n + 1):
        cat = random.choice(CATEGORIES)
        lo, hi = CATEGORY_PRICE_RANGE[cat]
        price = round(random.uniform(lo, hi), 2)
        brand = random.choice(BRANDS[cat])
        rows.append({
            "product_id": pid,
            "product_name": f"{brand} {random.choice(PRODUCT_NAMES[cat])}",
            "category": cat,
            "brand": brand,
            "price": price,
            "cost": round(price * random.uniform(0.4, 0.7), 2),
        })
    return pd.DataFrame(rows)


def gen_orders(users: pd.DataFrame, products: pd.DataFrame, n: int):
    """生成订单、订单明细、支付表，保证金额一致。"""
    order_rows, detail_rows, pay_rows = [], [], []
    detail_id = 1
    payment_id = 1
    pids = products["product_id"].tolist()
    prices = dict(zip(products["product_id"], products["price"]))
    uids = users["user_id"].tolist()

    # 用户活跃度服从幂律分布（少数高频、多数低频），
    # 让"复购率"更贴近真实电商（而非人人均匀下单导致 100% 复购）
    activity = [random.paretovariate(1.2) for _ in uids]

    for oid in range(1, n + 1):
        uid = random.choices(uids, weights=activity)[0]
        t = rand_dt()
        status = random.choices(
            ["已支付", "已完成", "待支付", "已取消"],
            weights=[45, 30, 15, 10],
        )[0]

        n_items = random.randint(1, 4)
        total = 0.0
        cur_details = []
        for _ in range(n_items):
            pid = random.choice(pids)
            qty = random.randint(1, 3)
            unit_price = round(prices[pid] * random.uniform(0.8, 1.0), 2)
            discount = round(unit_price * qty * random.uniform(0, 0.2), 2)
            line_total = round(unit_price * qty - discount, 2)
            total = round(total + line_total, 2)
            cur_details.append({
                "id": detail_id,
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "price": unit_price,
                "discount": discount,
            })
            detail_id += 1

        detail_rows.extend(cur_details)
        order_rows.append({
            "order_id": oid,
            "user_id": uid,
            "order_status": status,
            "order_time": t.strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": total,
            "pay_type": random.choice(PAY_TYPES),
        })

        if status in ("已支付", "已完成"):
            pay_rows.append({
                "payment_id": payment_id,
                "order_id": oid,
                "user_id": uid,
                "pay_amount": total,
                "pay_time": (t + timedelta(minutes=random.randint(1, 60))
                             ).strftime("%Y-%m-%d %H:%M:%S"),
                "pay_channel": random.choice(PAY_CHANNELS),
            })
            payment_id += 1

    return (pd.DataFrame(order_rows), pd.DataFrame(detail_rows),
            pd.DataFrame(pay_rows))


def main() -> None:
    config.ensure_dirs()
    users = gen_users(config.N_USERS)
    products = gen_products(config.N_PRODUCTS)
    orders, details, payments = gen_orders(users, products, config.N_ORDERS)

    users.to_csv(config.RAW_DIR / "user_info.csv", index=False)
    products.to_csv(config.RAW_DIR / "product_info.csv", index=False)
    orders.to_csv(config.RAW_DIR / "order_info.csv", index=False)
    details.to_csv(config.RAW_DIR / "order_detail.csv", index=False)
    payments.to_csv(config.RAW_DIR / "payment_info.csv", index=False)

    print("[01] 造数完成：")
    print(f"   user_info     : {len(users)} 行")
    print(f"   product_info  : {len(products)} 行")
    print(f"   order_info    : {len(orders)} 行")
    print(f"   order_detail  : {len(details)} 行")
    print(f"   payment_info  : {len(payments)} 行")
    print(f"   数据目录       : {config.RAW_DIR}")


if __name__ == "__main__":
    main()
