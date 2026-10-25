"""07 调度：按依赖顺序编排 ODS -> DWD -> DWS -> ADS 全流程。

生产环境建议用 Airflow / DolphinScheduler 以 DAG 方式调度，
本项目用 subprocess 按顺序串行执行，模拟任务依赖编排。
可传入 --loop N 秒，演示定时重跑（增量/幂等场景）。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# 任务依赖顺序（下游依赖上游，串行执行）
TASKS = ["03_etl_ods.py", "04_etl_dwd.py", "05_etl_dws.py", "06_etl_ads.py"]


def run_pipeline() -> None:
    base = Path(__file__).resolve().parent
    env = {**os.environ, "PYTHONUTF8": "1"}
    for script in TASKS:
        print(f"\n===== 执行 {script} =====")
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(base / script)],
            cwd=str(base.parent), env=env,
        )
        if r.returncode != 0:
            raise SystemExit(f"任务 {script} 失败，流程中断")


def main() -> None:
    interval = None
    if "--loop" in sys.argv:
        try:
            interval = int(sys.argv[sys.argv.index("--loop") + 1])
        except (ValueError, IndexError):
            raise SystemExit("用法：python 07_scheduler.py [--loop 秒数]")

    while True:
        run_pipeline()
        print("\n[07] 数仓全流程调度完成")
        if interval is None:
            break
        print(f"   {interval} 秒后重新执行...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
