from __future__ import annotations
import random
import time
import re
from playwright.sync_api import Page
from .logger import logger
from .selectors import (
    TWEET_ARTICLE,
    TWEET_DATATESTID_ANY,
    TWEET_REPLY,
    TWEET_TEXTAREA,
    TWEET_BUTTON,
    TWEET_BUTTON_MAIN,
    TWEET_LIKE,
    TWEET_RETWEET,
    TWEET_REPOST,
)
from .comments import random_comment
from .monitor import TweetCache
from .config import CONFIG

HOME_URL = "https://x.com/home"


def goto_home(page: Page):
    page.goto(HOME_URL)
    page.wait_for_load_state("domcontentloaded")
    # 等待时间线元素出现（尽量确保可见）
    try:
        page.wait_for_selector(f"{TWEET_DATATESTID_ANY},{TWEET_ARTICLE}", timeout=15000)
    except Exception:
        logger.warning("Timeline not ready after 15s; continuing anyway.")


def _text_snippet(page: Page, locator, limit: int = 80) -> str:
    try:
        txt = locator.inner_text(timeout=1000)
        txt = re.sub(r"\s+", " ", txt).strip()
        return (txt[:limit] + ("…" if len(txt) > limit else "")) if txt else ""
    except Exception:
        return ""


def list_visible_tweets(page: Page, limit: int = 12):
    # 收集前 N 条可见推文元素
    loc = page.locator(f"{TWEET_DATATESTID_ANY},{TWEET_ARTICLE}")
    count = min(loc.count(), limit)
    cards = [loc.nth(i) for i in range(count)]
    logger.info("可见推文卡片数: {}", count)
    # 打印前 5 条的简要内容
    for i, card in enumerate(cards[:5]):
        logger.info("卡片[{}] 内容片段: {}", i, _text_snippet(page, card))
    return cards


def pick_random_tweet(page: Page, cache: TweetCache, attempts: int = 12):
    cards = list_visible_tweets(page, limit=attempts)
    random.shuffle(cards)
    for idx, card in enumerate(cards[:attempts]):
        tid = cache.extract_tweet_id(card)
        snip = _text_snippet(page, card)
        logger.info("Candidate[{}] id={} seen={} snippet={}",
                    idx, tid, (False if not tid else not cache.is_new(tid)), snip)
        if not tid:
            continue
        if cache.is_new(tid):
            return card, tid
    return None, None


def comment_on_tweet(page: Page, card_locator, text: str) -> bool:
    try:
        # 打开评论界面
        reply = card_locator.locator(TWEET_REPLY)
        if not reply or reply.count() == 0:
            logger.warning("No reply button on selected tweet.")
            return False
        reply.first.click()

        # 定位到评论输入框：优先 data-testid，其次 role=textbox
        textbox = None
        try:
            page.wait_for_selector(TWEET_TEXTAREA, timeout=5000)
            textbox = page.locator(TWEET_TEXTAREA).first
        except Exception:
            try:
                textbox = page.get_by_role("textbox").first
            except Exception:
                textbox = None
        if textbox is None:
            logger.warning("No textbox found for reply.")
            return False

        # 确保聚焦再逐字输入，触发前端事件（比 fill 更稳）
        textbox.click()
        textbox.type(text, delay=40)

        # 在对话框范围内优先寻找“发布”按钮
        dialog = page.get_by_role("dialog")
        scope = dialog.nth(0) if dialog.count() > 0 else page
        btns = scope.locator(f"{TWEET_BUTTON}, {TWEET_BUTTON_MAIN}")

        clicked = False
        if btns.count() > 0:
            btn = btns.first
            try:
                btn.wait_for(state="visible", timeout=8000)
                # 等待按钮从 disabled/aria-disabled 变为可用
                handle = btn.element_handle()
                if handle is not None:
                    page.wait_for_function(
                        "b => b && !b.disabled && b.getAttribute('aria-disabled') !== 'true'",
                        arg=handle,
                        timeout=8000,
                    )
                if btn.is_enabled():
                    btn.click()
                    clicked = True
            except Exception as e:
                logger.debug("Primary button click failed, will try fallback: {}", e)

        # 仍未可点，尝试快捷键提交（Windows 常用 Ctrl+Enter）
        if not clicked:
            page.keyboard.press("Control+Enter")
            time.sleep(0.8)

        logger.info("Commented with: {}", text)
        return True
    except Exception as e:
        logger.warning("Random comment failed: {}", e)
        return False


def interact_on_card(page: Page, card_locator, cache: TweetCache, do_comment: bool, do_like: bool, do_retweet: bool) -> bool:
    ok_any = False
    txt_used = None
    try:
        if do_comment:
            ctx = _text_snippet(page, card_locator, limit=120)
            text = random_comment(ctx)
            logger.info("对当前推文评论: {}", text)
            if comment_on_tweet(page, card_locator, text):
                ok_any = True; txt_used = text
        if do_like:
            try:
                like = card_locator.locator(TWEET_LIKE)
                if like and like.count() > 0:
                    like.first.click(); logger.info("对当前推文点赞。"); ok_any = True
            except Exception:
                logger.warning("当前推文点赞失败。")
        if do_retweet:
            try:
                repost = card_locator.locator(TWEET_REPOST)
                if (not repost) or repost.count() == 0:
                    repost = card_locator.locator(TWEET_RETWEET)
                if repost and repost.count() > 0:
                    repost.first.click(); time.sleep(0.3)
                    try:
                        item = page.get_by_role("menuitem").filter(has_text=re.compile("Retweet|Repost|转发|转推", re.I)).first
                        if item and item.count() > 0:
                            item.click(); logger.info("对当前推文转发。"); ok_any = True
                        else:
                            page.get_by_text("Repost").or_(page.get_by_text("Retweet")).first.click(); logger.info("对当前推文转发(文本)"); ok_any = True
                    except Exception:
                        try:
                            page.locator("[data-testid='retweetConfirm']").first.click(); logger.info("对当前推文转发(确认)"); ok_any = True
                        except Exception:
                            logger.warning("当前推文转发失败。")
            except Exception:
                logger.warning("当前推文转发失败。")
    except Exception as e:
        logger.warning("对当前推文操作失败：{}", e)
    return ok_any


def perform_ops_on_random_tweet(page: Page, cache: TweetCache, do_comment: bool, do_like: bool, do_retweet: bool) -> bool:
    goto_home(page)
    # 小幅滚动以扩大候选
    try:
        for _ in range(random.randint(1, 2)):
            page.mouse.wheel(0, random.randint(300, 900)); time.sleep(random.uniform(0.2, 0.5))
    except Exception:
        pass
    card, tid = pick_random_tweet(page, cache)
    if not card:
        logger.info("No visible tweets found for operations.")
        return False
    ok = interact_on_card(page, card, cache, do_comment, do_like, do_retweet)
    if ok and tid:
        cache.mark_seen(tid)
    return ok


def random_comment_once(page: Page, cache: TweetCache) -> bool:
    goto_home(page)

    # 增加滚动以扩大候选集合
    try:
        for _ in range(random.randint(1, 3)):
            page.mouse.wheel(0, random.randint(400, 1200))
            time.sleep(random.uniform(0.2, 0.6))
    except Exception:
        pass

    # 首选：挑选未见过的新推文
    card, tid = pick_random_tweet(page, cache)

    # 若没有合适的新推文，回退：随便挑一条可见推文评论
    if not card:
        cards = list_visible_tweets(page, limit=8)
        if cards:
            card = random.choice(cards)
            tid = None
            logger.info("Fallback to random visible card. Snippet: {}", _text_snippet(page, card))
        else:
            logger.info("No visible tweets found for random comment.")
            return False

    # 取片段作为上下文，AI 模式会用到
    ctx = _text_snippet(page, card, limit=120)
    text = random_comment(ctx)
    logger.info("Attempting to comment: {}", text)
    ok = comment_on_tweet(page, card, text)
    # 简单计数上报（仅在 UI 里展示）
    try:
        if ok and CONFIG.action.do_comment:
            # 使用日志来统计由 UI 读取
            logger.info("统计：评论+1")
    except Exception:
        pass

    if ok and tid:
        cache.mark_seen(tid)
    return ok


def like_random_once(page: Page, cache: TweetCache) -> bool:
    goto_home(page)
    cards = list_visible_tweets(page, limit=8)
    if not cards:
        logger.info("No visible tweets to like.")
        return False
    for card in cards:
        try:
            like = card.locator(TWEET_LIKE)
            if like and like.count() > 0:
                like.first.click()
                logger.info("已点赞该推文。")
                return True
        except Exception:
            continue
    logger.info("未找到可点赞的推文按钮。")
    return False


def retweet_random_once(page: Page, cache: TweetCache) -> bool:
    goto_home(page)
    cards = list_visible_tweets(page, limit=8)
    if not cards:
        logger.info("No visible tweets to retweet.")
        return False
    for card in cards:
        try:
            # 先悬停卡片，部分布局悬停才出现操作栏
            try:
                card.hover(); time.sleep(0.2)
            except Exception:
                pass
            repost = card.locator(TWEET_REPOST)
            if (not repost) or repost.count() == 0:
                repost = card.locator(TWEET_RETWEET)
            if repost and repost.count() > 0:
                repost.first.click(); time.sleep(0.3)
                # 菜单弹出后，优先找 Retweet/Repost/转发
                try:
                    item = page.get_by_role("menuitem").filter(has_text=re.compile("Retweet|Repost|转发|转推", re.I)).first
                    if item and item.count() > 0:
                        item.click(); logger.info("已转发该推文。（menuitem）"); return True
                except Exception:
                    pass
                # 兜底：直接按文本或已知 testid
                try:
                    page.get_by_text("Repost").or_(page.get_by_text("Retweet")).first.click(); logger.info("已转发该推文。（text）"); return True
                except Exception:
                    pass
                try:
                    page.locator("[data-testid='retweetConfirm']").first.click(); logger.info("已转发该推文。（retweetConfirm）"); return True
                except Exception:
                    pass
        except Exception:
            continue
    logger.info("未找到可转发的推文按钮。")
    return False

