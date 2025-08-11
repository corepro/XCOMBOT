from __future__ import annotations
from .random_mode import random_comment_once, like_random_once, retweet_random_once

import time
import threading
import re
from .browser import BrowserManager
from .login import open_home, login_flow
from .login_weibo import ensure_login_weibo
from .config import CONFIG
from .logger import logger
from .follow import goto_user, ensure_following
from .monitor import TweetCache, check_and_interact_latest
from .humanize import random_wait, random_scroll, random_mouse_move
from .weibo import like_once as weibo_like_once, comment_once as weibo_comment_once, retweet_once as weibo_retweet_once, follow_once as weibo_follow_once
from .weibo import open_home_weibo
from .selectors import TWEET_TEXTAREA, TWEET_BUTTON, TWEET_BUTTON_MAIN, TWEET_REPLY, TWEET_LIKE, TWEET_REPOST, TWEET_RETWEET
from .comments import random_comment
from .oplog import write_oplog
from .anti_detection.integration import with_anti_detection, with_navigation_protection

# 全局停止事件（UI 可控制）
STOP_EVENT = threading.Event()


def run_follow_once():
    if getattr(CONFIG, "platform", "twitter") == "weibo":
        bm = BrowserManager()
        try:
            bm.launch(); bm.new_context(use_storage=True)
            return weibo_follow_once(bm.page)
        finally:
            bm.close()
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        open_home(bm)
        for user in CONFIG.users_to_follow:
            goto_user(bm.page, user)
            ensure_following(bm.page)
            random_scroll(bm.page)
    finally:
        bm.close()


def like_once(keep_open: bool = False):
    if getattr(CONFIG, "platform", "twitter") == "weibo":
        bm = BrowserManager()
        try:
            bm.launch(); bm.new_context(use_storage=True)
            ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
            return weibo_like_once(bm.page)
        finally:
            if not keep_open:
                bm.close()
    bm = BrowserManager()
    try:
        bm.launch(); bm.new_context(use_storage=True); open_home(bm)
        cache = TweetCache()
        like_random_once(bm.page, cache)
    finally:
        bm.close()


def retweet_once(keep_open: bool = False):
    if getattr(CONFIG, "platform", "twitter") == "weibo":
        bm = BrowserManager()
        try:
            bm.launch(); bm.new_context(use_storage=True)
            ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
            return weibo_retweet_once(bm.page)
        finally:
            if not keep_open:
                bm.close()
    bm = BrowserManager()
    try:
        bm.launch(); bm.new_context(use_storage=True); open_home(bm)
        cache = TweetCache()
        retweet_random_once(bm.page, cache)
    finally:
        bm.close()


def comment_once(keep_open: bool = False):
    if getattr(CONFIG, "platform", "twitter") == "weibo":
        bm = BrowserManager()
        try:
            bm.launch(); bm.new_context(use_storage=True)
            ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
            ok = weibo_comment_once(bm.page)
            return ok
        finally:
            if not keep_open:
                bm.close()
    bm = BrowserManager()
    cache = TweetCache()
    try:
        bm.launch(); bm.new_context(use_storage=True); open_home(bm)
        random_comment_once(bm.page, cache)
    finally:
        bm.close()


def run_monitor_loop():
    # 先支持 twitter 的随机评论循环；weibo 走单次接口占位
    if getattr(CONFIG, "platform", "twitter") == "weibo":
        logger.info("Weibo: 暂未实现监控循环，先使用单次操作接口；将检查登录")
        while not STOP_EVENT.is_set():
            try:
                comment_once()
                for _ in range(CONFIG.poll_interval_sec):
                    if STOP_EVENT.is_set():
                        break
                    time.sleep(1)
            except Exception as e:
                logger.exception("Weibo monitor loop error: {}", e)
        return

    bm = BrowserManager()
    cache = TweetCache()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        open_home(bm)
        while not STOP_EVENT.is_set():
            try:
                random_mouse_move(bm.page)
                random_comment_once(bm.page, cache)
                random_wait(0.8, 1.8)
                random_scroll(bm.page)
            except Exception as e:
                logger.exception("Random monitor error: {}", e)

            interval = CONFIG.poll_interval_sec
            logger.info("Sleep {} sec before next poll...", interval)
            for _ in range(interval):
                if STOP_EVENT.is_set():
                    break
                time.sleep(1)
    finally:
        bm.close()


# 随机模式：在单一浏览器会话中，按给定顺序执行一轮或多轮（不自动关闭，除非 keep_open=False）
# seq 元素取值："comment" | "like" | "retweet" | "follow"

def run_random_batch(seq: list[str], rounds: int = 1, keep_open: bool = True):
    platform = getattr(CONFIG, "platform", "twitter")
    bm = BrowserManager()
    cache = TweetCache()
    try:
        bm.launch(); bm.new_context(use_storage=True)
        if platform == "weibo":
            ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
        else:
            open_home(bm)
        for r in range(max(1, int(rounds))):
            logger.info("随机模式：会话内第 {} 轮，顺序={}", r+1, " → ".join(seq))
            for op in seq:
                if platform == "weibo":
                    if op == "comment":
                        ok = weibo_comment_once(bm.page); logger.info("Weibo 随机评论：{}", "成功" if ok else "失败")
                    elif op == "like":
                        ok = weibo_like_once(bm.page); logger.info("Weibo 随机点赞：{}", "成功" if ok else "失败")
                    elif op == "retweet":
                        ok = weibo_retweet_once(bm.page); logger.info("Weibo 随机转发：{}", "成功" if ok else "失败")
                    elif op == "follow":
                        ok = weibo_follow_once(bm.page); logger.info("Weibo 随机关注：{}", "成功" if ok else "失败")
                else:
                    if op == "comment":
                        ok = random_comment_once(bm.page, cache); logger.info("Twitter 随机评论：{}", "成功" if ok else "失败")
                    elif op == "like":
                        ok = like_random_once(bm.page, cache); logger.info("Twitter 随机点赞：{}", "成功" if ok else "失败")
                    elif op == "retweet":
                        ok = retweet_random_once(bm.page, cache); logger.info("Twitter 随机转发：{}", "成功" if ok else "失败")
                    elif op == "follow":
                        run_follow_once(); ok = True
        logger.info("随机模式：会话内所有轮次完成。")
    finally:
        if not keep_open:
            bm.close()

# 会话内：从推荐/时间线随机挑选 N 条不同博文，针对每条执行一次(评论/赞/转)集合
# 仅用于 Twitter，目前 Weibo 使用 weibo_*_once 近似实现；你若需要我也能补随机挑微博。
from .random_mode import perform_ops_on_random_tweet

def run_random_n_posts(n: int, do_comment: bool, do_like: bool, do_retweet: bool, keep_open: bool = True, on_progress=None):
    platform = getattr(CONFIG, "platform", "twitter")
    bm = BrowserManager(); cache = TweetCache()
    try:
        bm.launch(); bm.new_context(use_storage=True)
        if platform == "weibo":
            ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
            # 简化：weibo 暂以 weibo_*_once 代替（每次都操作首条，后续可扩展随机）
            for i in range(max(1, int(n))):
                if do_comment:
                    weibo_comment_once(bm.page)
                if do_like:
                    weibo_like_once(bm.page)
                if do_retweet:
                    weibo_retweet_once(bm.page)
        else:
            open_home(bm)
            picked = 0
            target = max(1, int(n))
            while picked < target:
                ok = perform_ops_on_random_tweet(bm.page, cache, do_comment, do_like, do_retweet)
                if ok:
                    picked += 1
                    try:
                        if on_progress:
                            on_progress(picked, target)
                    except Exception:
                        pass
                time.sleep(0.8)
        logger.info("随机模式(博文数)完成：N={}", n)
    finally:
        if not keep_open:
            bm.close()

# Weibo：随机 N 条不同卡片（基于 #scroller article），对每条执行一次集合操作
from .weibo import open_home_weibo, list_visible_posts, pick_random_post, interact_on_card

def run_weibo_random_n_posts(n: int, do_comment: bool, do_like: bool, do_retweet: bool, keep_open: bool = True, on_progress=None):
    bm = BrowserManager()
    try:
        bm.launch(); bm.new_context(use_storage=True)
        ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
        # 确保会话期间 UI 其他线程不会关闭浏览器
        logger.info("Weibo 随机模式：开始会话。目标 N={}", n)
        picked = 0
        seen = set()
        tries = 0
        target = max(1, int(n))
        while picked < target and tries < target * 10:
            tries += 1
            try:
                if (bm.page is None) or (hasattr(bm.page, 'is_closed') and bm.page.is_closed()):
                    logger.info("Weibo: 页面已关闭，重建上下文…")
                    bm.new_context(use_storage=True)
                open_home_weibo(bm.page)
            except Exception as e:
                logger.warning("Weibo: 打开首页失败，重建上下文重试… {}", e)
                try:
                    bm.new_context(use_storage=True)
                    open_home_weibo(bm.page)
                except Exception as e2:
                    logger.warning("Weibo: 重试打开首页仍失败 {}，继续下一轮", e2)
                    time.sleep(1.0)
                    continue
            # 滚动几屏，尽量拿到更多卡片
            # 尽量避免滚动导致定位丢失：先尝试不滚动直接选卡片
            card = pick_random_post(bm.page)
            if not card:
                try:
                    for _ in range(2):
                        bm.page.mouse.wheel(0, 700); time.sleep(0.4)
                except Exception:
                    pass
                card = pick_random_post(bm.page)
            # 可选：滚动后再校验卡片确实带有评论按钮，否则继续重试
            try:
                from .weibo import _card_has_comment as _check
            except Exception:
                _check = None
            if card and _check:
                try:
                    if not _check(card):
                        card = None
                except Exception:
                    card = None
            if not card:
                logger.info("Weibo: 滚动后仍未找到可评论卡片，重试…"); time.sleep(0.8); continue
            # 用卡片文本 hash 去重
            try:
                text = (card.inner_text(timeout=2000) or "").strip()
                hid = hash(text)
                if hid in seen:
                    logger.info("Weibo: 随机到重复卡片，重试…"); continue
                seen.add(hid)
            except Exception:
                pass
            ok = interact_on_card(bm.page, card, do_comment, do_like, do_retweet)
            if ok:
                picked += 1
                logger.info("Weibo: 本次成功，进度 {}/{}", picked, target)
                try:
                    if on_progress:
                        on_progress(picked, target)
                except Exception:
                    pass
            else:
                logger.info("Weibo: 本次未成功，重试…")
            time.sleep(0.8)
        logger.info("Weibo 随机模式(博文数)完成：N={} 实际执行={} 次 尝试次数={}", n, picked, tries)
    finally:
        if not keep_open:
            bm.close()

# Weibo 简单重复：始终操作首页第一条卡片，不滚动
from .weibo import like_once as wb_like_once, comment_once as wb_comment_once, retweet_once as wb_retweet_once, comment_and_optionally_repost

def run_weibo_firstcard_repeat(n: int, do_comment: bool, do_like: bool, do_retweet: bool, keep_open: bool = True, on_progress=None):
    bm = BrowserManager()
    try:
        bm.launch(); bm.new_context(use_storage=True)
        ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
        total = max(1, int(n))
        for i in range(total):
            try:
                open_home_weibo(bm.page)
                ok_any = False
                # 操作顺序：评论(可选) → 点赞(可选, 提交前) → 勾选转发(可选) → 一次性提交
                if do_comment or do_retweet or do_like:
                    ok_any = bool(comment_and_optionally_repost(bm.page, do_repost=do_retweet, do_like=do_like, back_to_home=False)) or ok_any
                if on_progress:
                    try:
                        on_progress(i+1, total)
                    except Exception:
                        pass
                # 间隔等待（除最后一次）
                if i < total - 1:
                    for _ in range(int(CONFIG.poll_interval_sec)):
                        time.sleep(1)
            except Exception as e:
                logger.warning("Weibo: 第{}次操作失败 {}，继续下一次", i+1, e)
                if on_progress:
                    try:
                        on_progress(i+1, total)
                    except Exception:
                        pass
                if i < total - 1:
                    for _ in range(int(CONFIG.poll_interval_sec)):
                        time.sleep(1)
        logger.info("Weibo 简单重复完成：N={}", total)
    finally:
        if not keep_open:
            bm.close()

from .weibo import automate_on_post as wb_automate_on_post

def run_weibo_joint_once(keep_open: bool = False):
    """微博联动一次：根据 CONFIG.action 中的勾选执行 评论/点赞/转发/关注 的组合。
    返回结果字典，包含本次是否执行各动作和提取到的链接等。
    """
    bm = BrowserManager()
    try:
        bm.launch(); bm.new_context(use_storage=True)
        ensure_login_weibo(bm.page, on_logged_in=lambda: bm.save_storage())
        do_comment = bool(getattr(CONFIG.action, "do_comment", True))
        do_like = bool(getattr(CONFIG.action, "do_like", True))
        do_retweet = bool(getattr(CONFIG.action, "do_retweet", False))
        do_follow = bool(getattr(CONFIG.action, "do_follow", True))
        res = wb_automate_on_post(bm.page, do_comment=do_comment, do_like=do_like, do_repost=do_retweet, do_follow=do_follow)
        logger.info("Weibo 联动结果: {}", res)
        return res
    finally:
        if not keep_open:
            bm.close()




# XHS：完整功能版本（登录→获取内容→评论→点赞→收藏→分享）
from .login_xhs import ensure_login_xhs, ensure_login_xhs_with_save
from .xhs import (
    open_home_xhs, pick_random_card, extract_card_content,
    xhs_interact_with_post, follow_user, act_once_on_first_card as xhs_once_legacy
)
from .zhihu import (
    open_home_zhihu, list_visible_posts, pick_random_post,
    zhihu_interact_with_post
)
from .login_zhihu import ensure_login_zhihu, ensure_login_zhihu_with_save
from .toutiao import (
    open_home_toutiao, list_visible_posts as toutiao_list_visible_posts,
    pick_random_post as toutiao_pick_random_post, toutiao_interact_with_post
)
from .login_toutiao import ensure_login_toutiao, ensure_login_toutiao_with_save

def xhs_full_interaction(page, do_comment: bool = True, do_like: bool = True,
                        do_collect: bool = True, do_share: bool = False) -> bool:
    """执行完整的小红书交互流程"""
    start_time = time.time()
    logger.info("XHS: [{}] 开始执行交互流程 - 评论:{} 点赞:{} 收藏:{} 分享:{}",
               time.strftime("%H:%M:%S"), do_comment, do_like, do_collect, do_share)

    try:
        # 打开首页
        logger.info("XHS: [{}] 正在打开首页...", time.strftime("%H:%M:%S"))
        open_home_xhs(page)
        logger.info("XHS: [{}] 首页加载完成，等待2秒...", time.strftime("%H:%M:%S"))
        time.sleep(2.0)

        # 选择随机卡片
        logger.info("XHS: [{}] 正在搜索可用卡片...", time.strftime("%H:%M:%S"))
        card = pick_random_card(page, limit=20)
        if not card:
            logger.error("XHS: [{}] 未找到可用卡片，交互失败", time.strftime("%H:%M:%S"))
            return False

        # 提取卡片内容
        logger.info("XHS: [{}] 正在提取卡片内容...", time.strftime("%H:%M:%S"))
        content = extract_card_content(card)
        logger.info("XHS: [{}] 选中卡片 - {}", time.strftime("%H:%M:%S"), content.get("title", "无标题")[:50])

        # 进入详情页
        logger.info("XHS: [{}] 正在尝试进入详情页...", time.strftime("%H:%M:%S"))
        opened = False
        for click_sel in ["a", "img", "picture"]:
            try:
                logger.debug("XHS: [{}] 尝试点击元素: {}", time.strftime("%H:%M:%S"), click_sel)
                elem = card.locator(click_sel).first
                if elem and elem.count() > 0:
                    elem.click(timeout=30000)
                    opened = True
                    logger.info("XHS: [{}] 成功点击 {} 进入详情页", time.strftime("%H:%M:%S"), click_sel)
                    break
            except Exception as e:
                logger.debug("XHS: [{}] 点击 {} 失败: {}", time.strftime("%H:%M:%S"), click_sel, str(e))
                continue

        if not opened:
            logger.info("XHS: [{}] 尝试直接点击卡片...", time.strftime("%H:%M:%S"))
            try:
                card.click(timeout=30000)
                opened = True
                logger.info("XHS: [{}] 成功直接点击卡片进入详情页", time.strftime("%H:%M:%S"))
            except Exception as e:
                logger.debug("XHS: [{}] 直接点击卡片失败: {}", time.strftime("%H:%M:%S"), str(e))
                pass

        if not opened:
            logger.error("XHS: [{}] 无法进入详情页，所有点击尝试都失败", time.strftime("%H:%M:%S"))
            return False

        # 等待详情页加载
        logger.info("XHS: [{}] 详情页加载中，等待2秒...", time.strftime("%H:%M:%S"))
        time.sleep(2.0)
        logger.info("XHS: [{}] 已进入详情页: {}", time.strftime("%H:%M:%S"), page.url)

        # 执行交互
        logger.info("XHS: [{}] 开始执行具体交互操作...", time.strftime("%H:%M:%S"))
        result = xhs_interact_with_post(
            page,
            do_comment=do_comment,
            do_like=do_like,
            do_collect=do_collect,
            do_share=do_share
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info("XHS: [{}] 交互完成 - 评论:{} 点赞:{} 收藏:{} 分享:{} 总耗时:{:.1f}秒",
                   time.strftime("%H:%M:%S"), result["comment"], result["like"],
                   result["collect"], result["share"], duration)

        success = result.get("success", False)
        if success:
            logger.info("XHS: [{}] ✅ 交互流程成功完成", time.strftime("%H:%M:%S"))
        else:
            logger.warning("XHS: [{}] ❌ 交互流程失败", time.strftime("%H:%M:%S"))

        return success

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error("XHS: [{}] ❌ 完整交互失败: {} (耗时:{:.1f}秒)",
                    time.strftime("%H:%M:%S"), str(e), duration)
        return False


def run_xhs_firstcard_repeat(n: int, do_comment: bool, do_like: bool, do_collect: bool = True, do_share: bool = False, keep_open: bool = True, on_progress=None):
    """小红书批量执行（使用完整功能版本）"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)

        # 登录
        if not ensure_login_xhs(bm.page, timeout_sec=180):
            logger.error("XHS: 登录失败")
            return

        total = max(1, int(n))
        success_count = 0

        for i in range(total):
            try:
                logger.info("XHS: 开始第 {}/{} 次执行", i + 1, total)

                # 使用完整功能版本
                ok = xhs_full_interaction(
                    bm.page,
                    do_comment=do_comment,
                    do_like=do_like,
                    do_collect=do_collect,
                    do_share=do_share
                )

                if ok:
                    success_count += 1
                    logger.info("XHS: 第 {} 次执行成功", i + 1)
                else:
                    logger.warning("XHS: 第 {} 次执行失败", i + 1)

                if on_progress:
                    try:
                        on_progress(i + 1, total)
                    except Exception:
                        pass

                # 间隔等待
                if i < total - 1:
                    interval = max(5, int(CONFIG.poll_interval_sec))
                    logger.info("XHS: 等待 {} 秒后继续...", interval)
                    for _ in range(interval):
                        time.sleep(1)

            except Exception as e:
                logger.warning("XHS: 第{}次操作失败 {}，继续下一次", i+1, e)
                if i < total - 1:
                    for _ in range(max(5, int(CONFIG.poll_interval_sec))):
                        time.sleep(1)

        logger.info("XHS 批量执行完成：总数={} 成功={} 成功率={:.1f}%",
                   total, success_count, (success_count/total*100) if total > 0 else 0)

    finally:
        if not keep_open:
            bm.close()


def xhs_comment_once():
    """小红书评论一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_xhs(bm.page, timeout_sec=180):
            logger.error("XHS: 登录失败")
            return False
        return xhs_full_interaction(bm.page, do_comment=True, do_like=False, do_collect=False, do_share=False)
    finally:
        bm.close()


def xhs_like_once():
    """小红书点赞一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_xhs(bm.page, timeout_sec=180):
            logger.error("XHS: 登录失败")
            return False
        return xhs_full_interaction(bm.page, do_comment=False, do_like=True, do_collect=False, do_share=False)
    finally:
        bm.close()


def xhs_collect_once():
    """小红书收藏一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_xhs(bm.page, timeout_sec=180):
            logger.error("XHS: 登录失败")
            return False
        return xhs_full_interaction(bm.page, do_comment=False, do_like=False, do_collect=True, do_share=False)
    finally:
        bm.close()


def xhs_share_once():
    """小红书分享一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_xhs(bm.page, timeout_sec=180):
            logger.error("XHS: 登录失败")
            return False
        return xhs_full_interaction(bm.page, do_comment=False, do_like=False, do_collect=False, do_share=True)
    finally:
        bm.close()


def xhs_follow_once():
    """小红书关注一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_xhs_with_save(bm, timeout_sec=180):
            logger.error("XHS: 登录失败")
            return False

        # 打开首页并选择文章，然后关注作者
        open_home_xhs(bm.page)
        time.sleep(2.0)

        card = pick_random_card(bm.page, limit=20)
        if not card:
            logger.warning("XHS: 未找到可用卡片")
            return False

        # 进入详情页
        opened = False
        for click_sel in ["a", "img", "picture"]:
            try:
                elem = card.locator(click_sel).first
                if elem and elem.count() > 0:
                    elem.click(timeout=30000)
                    opened = True
                    break
            except Exception:
                continue

        if not opened:
            try:
                card.click(timeout=30000)
                opened = True
            except Exception:
                pass

        if not opened:
            logger.warning("XHS: 无法进入详情页")
            return False

        time.sleep(2.0)
        return follow_user(bm.page)

    finally:
        bm.close()


# ==================== 知乎任务函数 ====================

def zhihu_full_interaction(page: Page, do_comment: bool = True, do_like: bool = True,
                          do_collect: bool = True, do_follow: bool = False) -> bool:
    """知乎完整交互流程"""
    start_time = time.time()
    logger.info("Zhihu: [{}] 开始执行交互流程 - 评论:{} 点赞:{} 收藏:{} 关注:{}",
               time.strftime("%H:%M:%S"), do_comment, do_like, do_collect, do_follow)

    try:
        # 打开首页并选择内容
        logger.info("Zhihu: [{}] 正在打开首页...", time.strftime("%H:%M:%S"))
        open_home_zhihu(page)
        logger.info("Zhihu: [{}] 首页加载完成，等待2秒...", time.strftime("%H:%M:%S"))
        time.sleep(2.0)

        logger.info("Zhihu: [{}] 正在搜索可用内容...", time.strftime("%H:%M:%S"))
        post = pick_random_post(page, limit=20)
        if not post:
            logger.error("Zhihu: [{}] 未找到可用内容，交互失败", time.strftime("%H:%M:%S"))
            return False

        # 进入详情页
        opened = False
        for click_sel in ["a", ".ContentItem-title", ".QuestionHeader-title"]:
            try:
                elem = post.locator(click_sel).first
                if elem and elem.count() > 0:
                    elem.click(timeout=30000)
                    opened = True
                    break
            except Exception:
                continue

        if not opened:
            try:
                post.click(timeout=30000)
                opened = True
            except Exception:
                pass

        if not opened:
            logger.warning("Zhihu: 无法进入详情页")
            return False

        time.sleep(3.0)
        logger.info("Zhihu: 已进入详情页: {}", page.url)

        # 执行交互
        results = zhihu_interact_with_post(page, do_comment, do_like, do_collect, do_follow)
        success = any(results.values())

        if success:
            logger.info("Zhihu: 交互完成 - 评论:{} 点赞:{} 收藏:{} 关注:{}",
                       results["comment"], results["like"], results["collect"], results["follow"])
        else:
            logger.warning("Zhihu: 所有交互都失败")

        return success

    except Exception as e:
        logger.warning("Zhihu: 交互过程异常: {}", str(e))
        return False


def zhihu_comment_once():
    """知乎评论一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_zhihu_with_save(bm, timeout_sec=180):
            logger.error("Zhihu: 登录失败")
            return False
        return zhihu_full_interaction(bm.page, do_comment=True, do_like=False, do_collect=False, do_follow=False)
    finally:
        bm.close()


def zhihu_like_once():
    """知乎点赞一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_zhihu_with_save(bm, timeout_sec=180):
            logger.error("Zhihu: 登录失败")
            return False
        return zhihu_full_interaction(bm.page, do_comment=False, do_like=True, do_collect=False, do_follow=False)
    finally:
        bm.close()


def zhihu_collect_once():
    """知乎收藏一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_zhihu_with_save(bm, timeout_sec=180):
            logger.error("Zhihu: 登录失败")
            return False
        return zhihu_full_interaction(bm.page, do_comment=False, do_like=False, do_collect=True, do_follow=False)
    finally:
        bm.close()


def zhihu_follow_once():
    """知乎关注一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_zhihu_with_save(bm, timeout_sec=180):
            logger.error("Zhihu: 登录失败")
            return False
        return zhihu_full_interaction(bm.page, do_comment=False, do_like=False, do_collect=False, do_follow=True)
    finally:
        bm.close()


def run_zhihu_firstcard_repeat(count: int = 3, interval_sec: int = 30,
                              do_comment: bool = True, do_like: bool = True,
                              do_collect: bool = True, do_follow: bool = False,
                              keep_open: bool = False, on_progress=None):
    """知乎重复执行任务"""
    bm = BrowserManager() if not keep_open else None
    page = None

    try:
        if not keep_open:
            bm.launch()
            bm.new_context(use_storage=True)
            page = bm.page
            if not ensure_login_zhihu_with_save(bm, timeout_sec=180):
                logger.error("Zhihu: 登录失败")
                return
        else:
            # 使用已有的浏览器实例
            from .browser import get_current_page
            page = get_current_page()
            if not page:
                logger.error("Zhihu: 未找到活动的浏览器页面")
                return

        success_count = 0
        for i in range(count):
            if STOP_EVENT.is_set():
                logger.info("Zhihu: 收到停止信号，退出循环")
                break

            logger.info("Zhihu: 开始第 {}/{} 次执行", i + 1, count)

            try:
                success = zhihu_full_interaction(page, do_comment, do_like, do_collect, do_follow)
                if success:
                    success_count += 1
                    logger.info("Zhihu: 第 {} 次执行成功", i + 1)
                else:
                    logger.warning("Zhihu: 第 {} 次执行失败", i + 1)

                # 更新进度
                if on_progress:
                    on_progress(i + 1, count)

                if i < count - 1:
                    logger.info("Zhihu: 等待 {} 秒后继续...", interval_sec)
                    for _ in range(interval_sec):
                        if STOP_EVENT.is_set():
                            logger.info("Zhihu: 收到停止信号，退出等待")
                            return
                        time.sleep(1)

            except Exception as e:
                logger.warning("Zhihu: 第 {} 次执行异常: {}", i + 1, str(e))

        logger.info("Zhihu: 执行完成，成功 {}/{} 次", success_count, count)

    finally:
        if not keep_open and bm:
            bm.close()


# ==================== 今日头条任务函数 ====================

def toutiao_full_interaction(page: Page, do_comment: bool = True, do_like: bool = True,
                            do_collect: bool = True, do_follow: bool = False) -> bool:
    """今日头条完整交互流程"""
    try:
        # 打开首页并选择内容
        open_home_toutiao(page)
        time.sleep(2.0)

        post = toutiao_pick_random_post(page, limit=20)
        if not post:
            logger.warning("Toutiao: 未找到可用内容")
            return False

        # 进入详情页
        opened = False
        for click_sel in ["a", ".article-title", ".video-title", ".content-title"]:
            try:
                elem = post.locator(click_sel).first
                if elem and elem.count() > 0:
                    elem.click(timeout=30000)
                    opened = True
                    break
            except Exception:
                continue

        if not opened:
            try:
                post.click(timeout=30000)
                opened = True
            except Exception:
                pass

        if not opened:
            logger.warning("Toutiao: 无法进入详情页")
            return False

        time.sleep(3.0)
        logger.info("Toutiao: 已进入详情页: {}", page.url)

        # 执行交互
        results = toutiao_interact_with_post(page, do_comment, do_like, do_collect, do_follow)
        success = any(results.values())

        if success:
            logger.info("Toutiao: 交互完成 - 评论:{} 点赞:{} 收藏:{} 关注:{}",
                       results["comment"], results["like"], results["collect"], results["follow"])
        else:
            logger.warning("Toutiao: 所有交互都失败")

        return success

    except Exception as e:
        logger.warning("Toutiao: 交互过程异常: {}", str(e))
        return False


def toutiao_comment_once():
    """今日头条评论一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_toutiao(bm.page, timeout_sec=180):
            logger.error("Toutiao: 登录失败")
            return False
        return toutiao_full_interaction(bm.page, do_comment=True, do_like=False, do_collect=False, do_follow=False)
    finally:
        bm.close()


def toutiao_like_once():
    """今日头条点赞一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_toutiao(bm.page, timeout_sec=180):
            logger.error("Toutiao: 登录失败")
            return False
        return toutiao_full_interaction(bm.page, do_comment=False, do_like=True, do_collect=False, do_follow=False)
    finally:
        bm.close()


def toutiao_collect_once():
    """今日头条收藏一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_toutiao(bm.page, timeout_sec=180):
            logger.error("Toutiao: 登录失败")
            return False
        return toutiao_full_interaction(bm.page, do_comment=False, do_like=False, do_collect=True, do_follow=False)
    finally:
        bm.close()


def toutiao_follow_once():
    """今日头条关注一次"""
    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)
        if not ensure_login_toutiao(bm.page, timeout_sec=180):
            logger.error("Toutiao: 登录失败")
            return False
        return toutiao_full_interaction(bm.page, do_comment=False, do_like=False, do_collect=False, do_follow=True)
    finally:
        bm.close()


def run_toutiao_firstcard_repeat(count: int = 3, interval_sec: int = 30,
                                do_comment: bool = True, do_like: bool = True,
                                do_collect: bool = True, do_follow: bool = False,
                                keep_open: bool = False, on_progress=None):
    """今日头条重复执行任务"""
    bm = BrowserManager() if not keep_open else None
    page = None

    try:
        if not keep_open:
            bm.launch()
            bm.new_context(use_storage=True)
            page = bm.page
            if not ensure_login_toutiao(page, timeout_sec=180):
                logger.error("Toutiao: 登录失败")
                return
        else:
            # 使用已有的浏览器实例
            from .browser import get_current_page
            page = get_current_page()
            if not page:
                logger.error("Toutiao: 未找到活动的浏览器页面")
                return

        success_count = 0
        for i in range(count):
            if STOP_EVENT.is_set():
                logger.info("Toutiao: 收到停止信号，退出循环")
                break

            logger.info("Toutiao: 开始第 {}/{} 次执行", i + 1, count)

            try:
                success = toutiao_full_interaction(page, do_comment, do_like, do_collect, do_follow)
                if success:
                    success_count += 1
                    logger.info("Toutiao: 第 {} 次执行成功", i + 1)
                else:
                    logger.warning("Toutiao: 第 {} 次执行失败", i + 1)

                # 更新进度
                if on_progress:
                    on_progress(i + 1, count)

                if i < count - 1:
                    logger.info("Toutiao: 等待 {} 秒后继续...", interval_sec)
                    for _ in range(interval_sec):
                        if STOP_EVENT.is_set():
                            logger.info("Toutiao: 收到停止信号，退出等待")
                            return
                        time.sleep(1)

            except Exception as e:
                logger.warning("Toutiao: 第 {} 次执行异常: {}", i + 1, str(e))

        logger.info("Toutiao: 执行完成，成功 {}/{} 次", success_count, count)

    finally:
        if not keep_open and bm:
            bm.close()


# 精准模式：对指定链接逐条执行（最小实现：Twitter/Weibo）
def twitter_act_on_url(bm: BrowserManager, url: str, do_like: bool, do_retweet: bool, do_comment: bool):
    try:
        if (bm.page is None) or (hasattr(bm.page, 'is_closed') and bm.page.is_closed()):
            bm.new_context(use_storage=True)
        page = bm.page
        page.goto(url, timeout=45000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(0.6)
        # 清理可能的 Cookie/隐私遮罩
        try:
            page.evaluate("() => { const m = document.querySelector('[data-testid=twc-cc-mask], .twc-cc-mask'); if (m) m.remove(); }")
        except Exception:
            pass
        try:
            page.get_by_role("button", name=re.compile("Accept|同意|允许|OK", re.I)).first.click()
        except Exception:
            pass
        # 先评论，再点赞，再转发（避免转发后上下文变化影响后续）
        if do_comment:
            t0 = time.perf_counter()
            try:
                page.locator(TWEET_REPLY).first.click(); time.sleep(0.2)
                txt = random_comment("")
                try:
                    page.fill(TWEET_TEXTAREA, txt)
                except Exception:
                    page.get_by_role("textbox").first.fill(txt)
                clicked = False
                try:
                    if page.locator(TWEET_BUTTON).count() > 0:
                        page.locator(TWEET_BUTTON).click(); clicked = True
                    else:
                        page.locator(TWEET_BUTTON_MAIN).click(); clicked = True
                except Exception:
                    pass
                if not clicked:
                    # 遭遮罩阻挡时退回键盘提交或再次点击
                    try:
                        page.keyboard.press("Control+Enter")
                    except Exception:
                        pass
                dt = int((time.perf_counter()-t0)*1000)
                write_oplog("twitter", "comment", url, txt, True, None, dt)
                logger.info("Twitter: 评论完成 [{}] {}", url, txt)
            except Exception as e:
                write_oplog("twitter", "comment", url, None, False, str(e))
                logger.warning("Twitter: 评论失败 {}", e)
        if do_like:
            t0 = time.perf_counter()
            try:
                page.locator(TWEET_LIKE).first.click();
                dt = int((time.perf_counter()-t0)*1000)
                write_oplog("twitter", "like", url, None, True, None, dt)
                logger.info("Twitter: 点赞完成 [{}]", url)
            except Exception as e:
                write_oplog("twitter", "like", url, None, False, str(e))
                logger.warning("Twitter: 点赞失败 {}", e)
        if do_retweet:
            t0 = time.perf_counter()
            try:
                rp = page.locator(TWEET_REPOST).first
                if not rp or rp.count() == 0:
                    rp = page.locator(TWEET_RETWEET).first
                rp.click(); time.sleep(0.3)
                try:
                    item = page.get_by_role("menuitem").filter(has_text=re.compile("Retweet|Repost|转发|转推", re.I)).first
                    if item and item.count() > 0:
                        item.click()
                    else:
                        page.get_by_text("Repost").or_(page.get_by_text("Retweet")).first.click()
                except Exception:
                    pass
                try:
                    page.locator("[data-testid='retweetConfirm']").first.click()
                except Exception:
                    pass
                dt = int((time.perf_counter()-t0)*1000)
                write_oplog("twitter", "retweet", url, None, True, None, dt)
                logger.info("Twitter: 转发完成 [{}]", url)
            except Exception as e:
                write_oplog("twitter", "retweet", url, None, False, str(e))
                logger.warning("Twitter: 转发失败 {}", e)
    except Exception as e:
        write_oplog("twitter", "visit", url, None, False, str(e))
        logger.warning("Twitter: 访问失败 {} - {}", url, e)


@with_navigation_protection
@with_anti_detection("weibo_url_processing")
def weibo_act_on_url(bm: BrowserManager, url: str, do_like: bool, do_retweet: bool, do_comment: bool, do_collect: bool = False):
    start_time = time.time()
    logger.info("Weibo精准模式: [{}] 开始处理URL: {}", time.strftime("%H:%M:%S"), url)
    logger.info("Weibo精准模式: [{}] 操作配置 - 评论:{} 点赞:{} 转发:{} 收藏:{}",
               time.strftime("%H:%M:%S"), do_comment, do_like, do_retweet, do_collect)

    try:
        # 确保页面可用；崩溃或关闭则重建
        logger.debug("Weibo精准模式: [{}] 检查页面状态...", time.strftime("%H:%M:%S"))
        if (bm.page is None) or (hasattr(bm.page, 'is_closed') and bm.page.is_closed()):
            logger.info("Weibo精准模式: [{}] 页面不可用，重建上下文...", time.strftime("%H:%M:%S"))
            bm.new_context(use_storage=True)
        page = bm.page

        # 导航，失败一次后重试（重建上下文）
        logger.info("Weibo精准模式: [{}] 正在导航到: {}", time.strftime("%H:%M:%S"), url)
        try:
            page.goto(url, timeout=45000)
            logger.info("Weibo精准模式: [{}] ✅ 页面导航成功", time.strftime("%H:%M:%S"))
        except Exception as e:
            logger.warning("Weibo精准模式: [{}] 首次导航失败: {}，重建上下文重试...", time.strftime("%H:%M:%S"), str(e))
            bm.new_context(use_storage=True)
            page = bm.page
            page.goto(url, timeout=45000)
            logger.info("Weibo精准模式: [{}] ✅ 重试导航成功", time.strftime("%H:%M:%S"))

        logger.info("Weibo精准模式: [{}] 等待页面加载完成...", time.strftime("%H:%M:%S"))
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1.0)
        logger.info("Weibo精准模式: [{}] ✅ 页面加载完成", time.strftime("%H:%M:%S"))

        # 评论 → 赞 → 转发 → 收藏 的顺序
        if do_comment:
            logger.info("Weibo精准模式: [{}] 开始执行评论操作...", time.strftime("%H:%M:%S"))
            t0 = time.perf_counter()
            ok = False
            txt = random_comment("")
            logger.info("Weibo精准模式: [{}] 生成评论内容: {}", time.strftime("%H:%M:%S"), txt)
            try:
                # 打开评论
                logger.debug("Weibo精准模式: [{}] 寻找评论按钮...", time.strftime("%H:%M:%S"))
                try:
                    cbtn = page.get_by_role("button", name=re.compile("评论|Comment", re.I)).first
                    if cbtn and cbtn.count() > 0:
                        logger.info("Weibo精准模式: [{}] 找到评论按钮，正在点击...", time.strftime("%H:%M:%S"))
                        cbtn.click(); time.sleep(0.2)
                        logger.info("Weibo精准模式: [{}] ✅ 评论按钮点击成功", time.strftime("%H:%M:%S"))
                    else:
                        logger.warning("Weibo精准模式: [{}] 未找到评论按钮", time.strftime("%H:%M:%S"))
                except Exception as e:
                    logger.warning("Weibo精准模式: [{}] 点击评论按钮失败: {}", time.strftime("%H:%M:%S"), str(e))
                # 定位输入框
                logger.debug("Weibo精准模式: [{}] 寻找评论输入框...", time.strftime("%H:%M:%S"))
                sel_textboxes = ["#comment-textarea", "textarea", "[role='textbox']"]
                box = None
                for i, sel in enumerate(sel_textboxes):
                    try:
                        logger.debug("Weibo精准模式: [{}] 尝试选择器 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(sel_textboxes), sel)
                        loc = page.locator(sel).first
                        if loc and loc.count() > 0:
                            logger.info("Weibo精准模式: [{}] ✅ 找到评论输入框: {}", time.strftime("%H:%M:%S"), sel)
                            box = loc; break
                    except Exception as e:
                        logger.debug("Weibo精准模式: [{}] 选择器失败: {} - {}", time.strftime("%H:%M:%S"), sel, str(e))
                        continue
                if not box:
                    logger.error("Weibo精准模式: [{}] ❌ 评论输入框未找到", time.strftime("%H:%M:%S"))
                    raise RuntimeError("评论输入框未找到")

                logger.info("Weibo精准模式: [{}] 正在填入评论内容...", time.strftime("%H:%M:%S"))
                box.fill(txt)
                logger.info("Weibo精准模式: [{}] ✅ 评论内容填入成功", time.strftime("%H:%M:%S"))
                # 提交
                logger.info("Weibo精准模式: [{}] 正在提交评论...", time.strftime("%H:%M:%S"))
                submitted = False
                try:
                    logger.debug("Weibo精准模式: [{}] 尝试快捷键 Control+Enter...", time.strftime("%H:%M:%S"))
                    box.press("Control+Enter"); submitted = True
                    logger.info("Weibo精准模式: [{}] ✅ 快捷键提交成功", time.strftime("%H:%M:%S"))
                except Exception as e:
                    logger.debug("Weibo精准模式: [{}] 快捷键提交失败: {}", time.strftime("%H:%M:%S"), str(e))

                if not submitted:
                    logger.info("Weibo精准模式: [{}] 尝试点击提交按钮...", time.strftime("%H:%M:%S"))
                    submit_selectors = [
                        "button:has-text('发布')",
                        "button:has-text('确定')",
                        "button:has-text('评论')",
                        "[role=button][aria-label*='发布']",
                    ]
                    for i, bsel in enumerate(submit_selectors):
                        try:
                            logger.debug("Weibo精准模式: [{}] 尝试提交按钮 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(submit_selectors), bsel)
                            loc = page.locator(bsel).first
                            if loc and loc.count() > 0:
                                loc.click(); submitted = True
                                logger.info("Weibo精准模式: [{}] ✅ 提交按钮点击成功: {}", time.strftime("%H:%M:%S"), bsel)
                                break
                        except Exception as e:
                            logger.debug("Weibo精准模式: [{}] 提交按钮失败: {} - {}", time.strftime("%H:%M:%S"), bsel, str(e))
                            continue

                ok = submitted
                if ok:
                    logger.info("Weibo精准模式: [{}] ✅ 评论操作成功完成", time.strftime("%H:%M:%S"))
                else:
                    logger.error("Weibo精准模式: [{}] ❌ 评论提交失败", time.strftime("%H:%M:%S"))
            except Exception as e:
                write_oplog("weibo", "comment", url, None, False, str(e))
            else:
                write_oplog("weibo", "comment", url, txt, ok, None if ok else "submit_failed", int((time.perf_counter()-t0)*1000))

        if do_like:
            logger.info("Weibo精准模式: [{}] 开始执行点赞操作...", time.strftime("%H:%M:%S"))
            t0 = time.perf_counter()
            ok = False
            try:
                like_selectors = [
                    "button:has-text('赞')",
                    "[role=button][aria-label*='赞']",
                    "button[title*='赞']",
                    "[aria-label*='Like']",
                ]
                for i, sel in enumerate(like_selectors):
                    try:
                        logger.debug("Weibo精准模式: [{}] 尝试点赞按钮 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(like_selectors), sel)
                        loc = page.locator(sel).first
                        if loc and loc.count() > 0:
                            loc.click(); ok = True
                            logger.info("Weibo精准模式: [{}] ✅ 点赞成功: {}", time.strftime("%H:%M:%S"), sel)
                            break
                    except Exception as e:
                        logger.debug("Weibo精准模式: [{}] 点赞按钮失败: {} - {}", time.strftime("%H:%M:%S"), sel, str(e))
                        continue

                if not ok:
                    logger.warning("Weibo精准模式: [{}] ❌ 未找到可用的点赞按钮", time.strftime("%H:%M:%S"))
            except Exception as e:
                write_oplog("weibo", "like", url, None, False, str(e))
            else:
                write_oplog("weibo", "like", url, None, ok, None if ok else "not_found", int((time.perf_counter()-t0)*1000))

        if do_retweet:
            logger.info("Weibo精准模式: [{}] 开始执行转发操作...", time.strftime("%H:%M:%S"))
            t0 = time.perf_counter()
            ok = False
            try:
                # 打开转发菜单/弹层
                logger.debug("Weibo精准模式: [{}] 寻找转发按钮...", time.strftime("%H:%M:%S"))
                retweet_selectors = [
                    "button:has-text('转发')",
                    "[role=button][aria-label*='转发']",
                    "button:has-text('Repost')",
                    "button:has-text('分享')",
                ]
                retweet_clicked = False
                for i, sel in enumerate(retweet_selectors):
                    try:
                        logger.debug("Weibo精准模式: [{}] 尝试转发按钮 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(retweet_selectors), sel)
                        loc = page.locator(sel).first
                        if loc and loc.count() > 0:
                            loc.click(); time.sleep(0.4)
                            logger.info("Weibo精准模式: [{}] ✅ 转发按钮点击成功: {}", time.strftime("%H:%M:%S"), sel)
                            retweet_clicked = True
                            break
                    except Exception as e:
                        logger.debug("Weibo精准模式: [{}] 转发按钮失败: {} - {}", time.strftime("%H:%M:%S"), sel, str(e))
                        continue

                if retweet_clicked:
                    # 点击发布/确定
                    logger.debug("Weibo精准模式: [{}] 寻找发布按钮...", time.strftime("%H:%M:%S"))
                    publish_selectors = [
                        "button:has-text('发布')",
                        "button:has-text('确定')",
                        "[role=button][aria-label*='发布']",
                        "[role=button][aria-label*='确定']",
                    ]
                    for i, sel in enumerate(publish_selectors):
                        try:
                            logger.debug("Weibo精准模式: [{}] 尝试发布按钮 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(publish_selectors), sel)
                            loc = page.locator(sel).first
                            if loc and loc.count() > 0:
                                loc.click(); ok = True
                                logger.info("Weibo精准模式: [{}] ✅ 转发发布成功: {}", time.strftime("%H:%M:%S"), sel)
                                break
                        except Exception as e:
                            logger.debug("Weibo精准模式: [{}] 发布按钮失败: {} - {}", time.strftime("%H:%M:%S"), sel, str(e))
                            continue
                else:
                    logger.warning("Weibo精准模式: [{}] ❌ 未找到转发按钮", time.strftime("%H:%M:%S"))
                if not ok:
                    logger.warning("Weibo精准模式: [{}] ❌ 转发操作失败", time.strftime("%H:%M:%S"))
                    # 兜底：评论面板切换转发开关
                    try:
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
            except Exception as e:
                write_oplog("weibo", "retweet", url, None, False, str(e))
                logger.error("Weibo精准模式: [{}] 转发操作异常: {}", time.strftime("%H:%M:%S"), str(e))
            else:
                write_oplog("weibo", "retweet", url, None, ok, None if ok else "not_found", int((time.perf_counter()-t0)*1000))

        # 收藏功能
        if do_collect:
            logger.info("Weibo精准模式: [{}] 开始执行收藏操作...", time.strftime("%H:%M:%S"))
            t0 = time.perf_counter()
            ok = False
            try:
                collect_selectors = [
                    "button:has-text('收藏')",
                    "[role=button][aria-label*='收藏']",
                    "button[title*='收藏']",
                    "[aria-label*='Bookmark']",
                    "button:has-text('⭐')",
                ]
                for i, sel in enumerate(collect_selectors):
                    try:
                        logger.debug("Weibo精准模式: [{}] 尝试收藏按钮 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(collect_selectors), sel)
                        loc = page.locator(sel).first
                        if loc and loc.count() > 0:
                            loc.click(); ok = True
                            logger.info("Weibo精准模式: [{}] ✅ 收藏成功: {}", time.strftime("%H:%M:%S"), sel)
                            break
                    except Exception as e:
                        logger.debug("Weibo精准模式: [{}] 收藏按钮失败: {} - {}", time.strftime("%H:%M:%S"), sel, str(e))
                        continue

                if not ok:
                    logger.warning("Weibo精准模式: [{}] ❌ 未找到可用的收藏按钮", time.strftime("%H:%M:%S"))
            except Exception as e:
                write_oplog("weibo", "collect", url, None, False, str(e))
                logger.error("Weibo精准模式: [{}] 收藏操作异常: {}", time.strftime("%H:%M:%S"), str(e))
            else:
                write_oplog("weibo", "collect", url, None, ok, None if ok else "not_found", int((time.perf_counter()-t0)*1000))

        # 操作完成总结
        end_time = time.time()
        duration = end_time - start_time
        logger.info("Weibo精准模式: [{}] ✅ URL处理完成: {} (总耗时:{:.1f}秒)",
                   time.strftime("%H:%M:%S"), url, duration)

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        write_oplog("weibo", "visit", url, None, False, str(e))
        logger.error("Weibo精准模式: [{}] ❌ URL访问失败: {} - {} (耗时:{:.1f}秒)",
                    time.strftime("%H:%M:%S"), url, str(e), duration)


@with_navigation_protection
@with_anti_detection("zhihu_url_processing")
def zhihu_act_on_url(bm: BrowserManager, url: str, do_like: bool, do_retweet: bool, do_comment: bool, do_collect: bool = False, do_follow: bool = False):
    """知乎精准模式：处理单个知乎URL"""
    start_time = time.time()
    logger.info("Zhihu精准模式: [{}] 开始处理URL: {}", time.strftime("%H:%M:%S"), url)
    logger.info("Zhihu精准模式: [{}] 操作配置 - 评论:{} 点赞:{} 收藏:{} 关注:{}",
               time.strftime("%H:%M:%S"), do_comment, do_like, do_collect, do_follow)

    try:
        # 确保页面可用
        logger.debug("Zhihu精准模式: [{}] 检查页面状态...", time.strftime("%H:%M:%S"))
        if (bm.page is None) or (hasattr(bm.page, 'is_closed') and bm.page.is_closed()):
            logger.info("Zhihu精准模式: [{}] 页面不可用，重建上下文...", time.strftime("%H:%M:%S"))
            bm.new_context(use_storage=True)
        page = bm.page

        # 导航到URL
        logger.info("Zhihu精准模式: [{}] 正在导航到: {}", time.strftime("%H:%M:%S"), url)
        try:
            page.goto(url, timeout=45000)
            logger.info("Zhihu精准模式: [{}] ✅ 页面导航成功", time.strftime("%H:%M:%S"))
        except Exception as e:
            logger.warning("Zhihu精准模式: [{}] 首次导航失败: {}，重建上下文重试...", time.strftime("%H:%M:%S"), str(e))
            bm.new_context(use_storage=True)
            page = bm.page
            page.goto(url, timeout=45000)
            logger.info("Zhihu精准模式: [{}] ✅ 重试导航成功", time.strftime("%H:%M:%S"))

        logger.info("Zhihu精准模式: [{}] 等待页面加载完成...", time.strftime("%H:%M:%S"))
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2.0)  # 知乎页面需要更多时间加载
        logger.info("Zhihu精准模式: [{}] ✅ 页面加载完成", time.strftime("%H:%M:%S"))

        # 使用知乎的交互函数
        from .zhihu import zhihu_interact_with_post

        logger.info("Zhihu精准模式: [{}] 开始执行交互操作...", time.strftime("%H:%M:%S"))
        result = zhihu_interact_with_post(
            page=page,
            do_comment=do_comment,
            do_like=do_like,
            do_collect=do_collect,
            do_follow=do_follow
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info("Zhihu精准模式: [{}] 交互完成 - 评论:{} 点赞:{} 收藏:{} 关注:{} 总耗时:{:.1f}秒",
                   time.strftime("%H:%M:%S"), result["comment"], result["like"],
                   result["collect"], result["follow"], duration)

        # 判断是否成功（至少一个操作成功）
        success = any(result.values())
        if success:
            logger.info("Zhihu精准模式: [{}] ✅ URL处理成功: {}", time.strftime("%H:%M:%S"), url)
        else:
            logger.warning("Zhihu精准模式: [{}] ⚠️ URL处理未完成任何操作: {}", time.strftime("%H:%M:%S"), url)

        return success

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error("Zhihu精准模式: [{}] ❌ URL处理失败: {} - {} (耗时:{:.1f}秒)",
                    time.strftime("%H:%M:%S"), url, str(e), duration)
        return False


@with_navigation_protection
@with_anti_detection("xhs_url_processing")
def xhs_act_on_url(bm: BrowserManager, url: str, do_like: bool, do_retweet: bool, do_comment: bool, do_collect: bool = False, do_follow: bool = False):
    """小红书精准模式：处理单个小红书URL"""
    start_time = time.time()
    logger.info("XHS精准模式: [{}] 开始处理URL: {}", time.strftime("%H:%M:%S"), url)
    logger.info("XHS精准模式: [{}] 操作配置 - 评论:{} 点赞:{} 分享:{} 收藏:{} 关注:{}",
               time.strftime("%H:%M:%S"), do_comment, do_like, do_retweet, do_collect, do_follow)

    try:
        # 确保页面可用
        logger.debug("XHS精准模式: [{}] 检查页面状态...", time.strftime("%H:%M:%S"))
        if (bm.page is None) or (hasattr(bm.page, 'is_closed') and bm.page.is_closed()):
            logger.info("XHS精准模式: [{}] 页面不可用，重建上下文...", time.strftime("%H:%M:%S"))
            bm.new_context(use_storage=True)
        page = bm.page

        # 导航到URL
        logger.info("XHS精准模式: [{}] 正在导航到: {}", time.strftime("%H:%M:%S"), url)
        try:
            page.goto(url, timeout=45000)
            logger.info("XHS精准模式: [{}] ✅ 页面导航成功", time.strftime("%H:%M:%S"))
        except Exception as e:
            logger.warning("XHS精准模式: [{}] 首次导航失败: {}，重建上下文重试...", time.strftime("%H:%M:%S"), str(e))
            bm.new_context(use_storage=True)
            page = bm.page
            page.goto(url, timeout=45000)
            logger.info("XHS精准模式: [{}] ✅ 重试导航成功", time.strftime("%H:%M:%S"))

        logger.info("XHS精准模式: [{}] 等待页面加载完成...", time.strftime("%H:%M:%S"))
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2.0)  # 小红书页面需要时间加载
        logger.info("XHS精准模式: [{}] ✅ 页面加载完成", time.strftime("%H:%M:%S"))

        # 使用小红书的交互函数
        from .xhs import xhs_interact_with_post

        logger.info("XHS精准模式: [{}] 开始执行交互操作...", time.strftime("%H:%M:%S"))
        result = xhs_interact_with_post(
            page=page,
            do_comment=do_comment,
            do_like=do_like,
            do_collect=do_collect,
            do_share=do_retweet,  # 小红书用分享代替转发
            do_follow=do_follow
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info("XHS精准模式: [{}] 交互完成 - 评论:{} 点赞:{} 收藏:{} 分享:{} 关注:{} 总耗时:{:.1f}秒",
                   time.strftime("%H:%M:%S"), result["comment"], result["like"],
                   result["collect"], result["share"], result["follow"], duration)

        # 判断是否成功（至少一个操作成功）
        success = any(result.values())
        if success:
            logger.info("XHS精准模式: [{}] ✅ URL处理成功: {}", time.strftime("%H:%M:%S"), url)
        else:
            logger.warning("XHS精准模式: [{}] ⚠️ URL处理未完成任何操作: {}", time.strftime("%H:%M:%S"), url)

        return success

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error("XHS精准模式: [{}] ❌ URL处理失败: {} - {} (耗时:{:.1f}秒)",
                    time.strftime("%H:%M:%S"), url, str(e), duration)
        return False


@with_navigation_protection
@with_anti_detection("toutiao_url_processing")
def toutiao_act_on_url(bm: BrowserManager, url: str, do_like: bool, do_retweet: bool, do_comment: bool, do_collect: bool = False, do_follow: bool = False):
    """今日头条精准模式：处理单个今日头条URL"""
    start_time = time.time()
    logger.info("Toutiao精准模式: [{}] 开始处理URL: {}", time.strftime("%H:%M:%S"), url)
    logger.info("Toutiao精准模式: [{}] 操作配置 - 评论:{} 点赞:{} 收藏:{} 关注:{}",
               time.strftime("%H:%M:%S"), do_comment, do_like, do_collect, do_follow)

    try:
        # 确保页面可用
        logger.debug("Toutiao精准模式: [{}] 检查页面状态...", time.strftime("%H:%M:%S"))
        if (bm.page is None) or (hasattr(bm.page, 'is_closed') and bm.page.is_closed()):
            logger.info("Toutiao精准模式: [{}] 页面不可用，重建上下文...", time.strftime("%H:%M:%S"))
            bm.new_context(use_storage=True)
        page = bm.page

        # 导航到URL
        logger.info("Toutiao精准模式: [{}] 正在导航到: {}", time.strftime("%H:%M:%S"), url)
        try:
            page.goto(url, timeout=45000)
            logger.info("Toutiao精准模式: [{}] ✅ 页面导航成功", time.strftime("%H:%M:%S"))
        except Exception as e:
            logger.warning("Toutiao精准模式: [{}] 首次导航失败: {}，重建上下文重试...", time.strftime("%H:%M:%S"), str(e))
            bm.new_context(use_storage=True)
            page = bm.page
            page.goto(url, timeout=45000)
            logger.info("Toutiao精准模式: [{}] ✅ 重试导航成功", time.strftime("%H:%M:%S"))

        logger.info("Toutiao精准模式: [{}] 等待页面加载完成...", time.strftime("%H:%M:%S"))
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2.0)  # 今日头条页面需要时间加载
        logger.info("Toutiao精准模式: [{}] ✅ 页面加载完成", time.strftime("%H:%M:%S"))

        # 使用今日头条的交互函数
        from .toutiao import toutiao_interact_with_post

        logger.info("Toutiao精准模式: [{}] 开始执行交互操作...", time.strftime("%H:%M:%S"))
        result = toutiao_interact_with_post(
            page=page,
            do_comment=do_comment,
            do_like=do_like,
            do_collect=do_collect,
            do_follow=do_follow
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info("Toutiao精准模式: [{}] 交互完成 - 评论:{} 点赞:{} 收藏:{} 关注:{} 总耗时:{:.1f}秒",
                   time.strftime("%H:%M:%S"), result["comment"], result["like"],
                   result["collect"], result["follow"], duration)

        # 判断是否成功（至少一个操作成功）
        success = any(result.values())
        if success:
            logger.info("Toutiao精准模式: [{}] ✅ URL处理成功: {}", time.strftime("%H:%M:%S"), url)
        else:
            logger.warning("Toutiao精准模式: [{}] ⚠️ URL处理未完成任何操作: {}", time.strftime("%H:%M:%S"), url)

        return success

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error("Toutiao精准模式: [{}] ❌ URL处理失败: {} - {} (耗时:{:.1f}秒)",
                    time.strftime("%H:%M:%S"), url, str(e), duration)
        return False


def process_links(links: list[str], do_like: bool, do_retweet: bool, do_comment: bool, do_follow: bool = False, keep_open: bool = False, do_collect: bool = False):
    """精准模式：处理链接列表，支持所有平台"""
    platform = getattr(CONFIG, "platform", "twitter")
    logger.info("精准模式: 开始处理 {} 个链接，平台: {}", len(links), platform.upper())

    bm = BrowserManager()
    try:
        bm.launch()
        bm.new_context(use_storage=True)

        # 根据平台进行登录
        if platform == "weibo":
            from .login_weibo import ensure_login_weibo
            ensure_login_weibo(bm.page)
        elif platform == "xhs":
            from .login_xhs import ensure_login_xhs_with_save
            ensure_login_xhs_with_save(bm)
        elif platform == "zhihu":
            from .login_zhihu import ensure_login_zhihu_with_save
            ensure_login_zhihu_with_save(bm)
        elif platform == "toutiao":
            from .login_toutiao import ensure_login_toutiao_with_save
            ensure_login_toutiao_with_save(bm)
        elif platform == "twitter":
            from .login import login_flow
            login_flow(bm)

        # 处理每个链接
        success_count = 0
        for i, url in enumerate(links, 1):
            logger.info("精准模式: [{}/{}] 处理链接: {}", i, len(links), url)

            try:
                if platform == "weibo":
                    success = weibo_act_on_url(bm, url, do_like, do_retweet, do_comment, do_collect)
                elif platform == "xhs":
                    success = xhs_act_on_url(bm, url, do_like, do_retweet, do_comment, do_collect, do_follow)
                elif platform == "zhihu":
                    success = zhihu_act_on_url(bm, url, do_like, do_retweet, do_comment, do_collect, do_follow)
                elif platform == "toutiao":
                    success = toutiao_act_on_url(bm, url, do_like, do_retweet, do_comment, do_collect, do_follow)
                elif platform == "twitter":
                    success = twitter_act_on_url(bm, url, do_like, do_retweet, do_comment)
                else:
                    logger.error("精准模式: 不支持的平台: {}", platform)
                    success = False

                if success:
                    success_count += 1
                    logger.info("精准模式: [{}/{}] ✅ 链接处理成功", i, len(links))
                else:
                    logger.warning("精准模式: [{}/{}] ❌ 链接处理失败", i, len(links))

                # 间隔等待（除最后一次）
                if i < len(links):
                    wait_time = CONFIG.poll_interval_sec
                    logger.info("精准模式: 等待 {} 秒后处理下一个链接...", wait_time)
                    time.sleep(wait_time)

            except Exception as e:
                logger.error("精准模式: [{}/{}] 链接处理异常: {} - {}", i, len(links), url, str(e))

        logger.info("精准模式: 处理完成，成功: {}/{}", success_count, len(links))

    finally:
        if not keep_open:
            bm.close()

