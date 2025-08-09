from __future__ import annotations
import time
import argparse
from contextlib import contextmanager
import sys
sys.path.append('.')
from src.ui_bootstrap import AppUIBoot
from src.config import CONFIG
from src.logger import logger


@contextmanager
def ui_instance(hidden: bool = True):
    ui = AppUIBoot()
    try:
        if hidden:
            try:
                ui.app.withdraw()
            except Exception:
                pass
        yield ui
    finally:
        try:
            ui.app.destroy()
        except Exception:
            pass


def test_start_stop_cycle(ui: AppUIBoot, cycles: int = 2, sleep_sec: int = 2):
    logger.info("[SMOKE] test_start_stop_cycle cycles={} sleep_sec={}", cycles, sleep_sec)
    for i in range(cycles):
        logger.info("[SMOKE] start cycle {}", i + 1)
        ui.start_loop()
        time.sleep(sleep_sec)
        ui.stop_loop()
        # 等待线程回收并重置按钮
        time.sleep(1.0)
        assert ui._worker is None, "worker should be None after stop"
        logger.info("[SMOKE] cycle {} done", i + 1)


def test_quick_actions(ui: AppUIBoot, platform: str = "twitter"):
    logger.info("[SMOKE] test_quick_actions platform={}", platform)
    ui.var_platform.set(platform)
    ui._run_like_once(); time.sleep(0.5)
    ui._run_comment_once(); time.sleep(0.5)
    ui._run_retweet_once(); time.sleep(0.5)


def _wait_worker_done(ui: AppUIBoot, timeout: int = 60):
    t0 = time.time()
    while ui._worker and ui._worker.is_alive():
        time.sleep(0.5)
        if time.time() - t0 > timeout:
            raise TimeoutError("worker not finished in time")


def test_random_batch(ui: AppUIBoot):
    logger.info("[SMOKE] test_random_batch")
    ui.var_scope.set("random")
    if hasattr(ui, "var_cnt_rounds"):
        ui.var_cnt_rounds.set(1)
    # 勾选全部
    ui.var_comment.set(True)
    ui.var_like.set(True)
    ui.var_rt.set(True)
    ui.var_follow.set(False)
    ui.run_batch()
    _wait_worker_done(ui, timeout=120)


def test_precise_batch(ui: AppUIBoot):
    logger.info("[SMOKE] test_precise_batch")
    ui.var_scope.set("list")
    # 取较少的链接进行验证；优先 weibo
    links = [
        "https://weibo.com/5828016458/PETBBmS5G",
        "https://x.com/ShouldHaveCat/status/1953622486907523115",
    ]
    ui.links_text.delete("1.0", "end")
    ui.links_text.insert("1.0", "\n".join(links))
    ui.var_comment.set(True)
    ui.var_like.set(True)
    ui.var_rt.set(True)
    ui.var_follow.set(False)
    ui.run_batch()
    _wait_worker_done(ui, timeout=180)


def test_login_button(ui: AppUIBoot, platform: str = "weibo", timeout: int = 30):
    logger.info("[SMOKE] test_login_button platform={}", platform)
    ui.var_platform.set(platform)
    start = time.time()
    # 触发登录流程；如已登录将立即返回
    ui.login_account()
    dt = time.time() - start
    logger.info("[SMOKE] login flow returned in {:.1f}s", dt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run a quick subset of UI smoke tests")
    args = parser.parse_args()

    # 使用更轻量的配置
    CONFIG.headless = True
    CONFIG.slow_mo_ms = 0

    with ui_instance(hidden=True) as ui:
        # 顶部工具条变量应存在
        assert hasattr(ui, "var_platform") and hasattr(ui, "var_mode"), "toolbar vars missing"
        # 1) 登录按钮（weibo）
        try:
            test_login_button(ui, platform="weibo")
        except Exception as e:
            logger.warning("[SMOKE] login_button error: {}", e)
        # 2) 开始-停止-开始 能否循环
        try:
            test_start_stop_cycle(ui, cycles=1 if args.quick else 2, sleep_sec=1)
        except Exception as e:
            logger.warning("[SMOKE] start_stop_cycle error: {}", e)
        # 3) 快捷动作（Twitter 与 Weibo 各一轮）
        try:
            test_quick_actions(ui, platform="twitter")
        except Exception as e:
            logger.warning("[SMOKE] quick_actions twitter error: {}", e)
        try:
            test_quick_actions(ui, platform="weibo")
        except Exception as e:
            logger.warning("[SMOKE] quick_actions weibo error: {}", e)
        # 4) 批量（随机 + 精准）
        try:
            test_random_batch(ui)
        except Exception as e:
            logger.warning("[SMOKE] random_batch error: {}", e)
        try:
            test_precise_batch(ui)
        except Exception as e:
            logger.warning("[SMOKE] precise_batch error: {}", e)

    logger.info("[SMOKE] UI smoke completed")


if __name__ == "__main__":
    main()

