from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .selectors import TWEET_ARTICLE, TWEET_DATATESTID_ANY, TWEET_REPLY, TWEET_REPOST, TWEET_RETWEET, TWEET_TEXTAREA, TWEET_BUTTON, TWEET_BUTTON_MAIN
from .comments import random_comment
import time


class TweetCache:
    def __init__(self):
        self.seen_ids: set[str] = set()

    def extract_tweet_id(self, locator) -> str | None:
        try:
            # X 的 DOM 不稳定，这里采用位置序号或 data-testid-fallback
            # 尝试从 attribute data-tweet-id（如果存在）
            el = locator.first
            id_attr = el.get_attribute("data-tweet-id")
            if id_attr:
                return id_attr
            # 退而求其次：用 innerText 的前几十字符 hash
            text = el.inner_text(timeout=2000)
            return str(hash(text)) if text else None
        except Exception:
            return None

    def mark_seen(self, tweet_id: str):
        self.seen_ids.add(tweet_id)

    def is_new(self, tweet_id: str) -> bool:
        return tweet_id not in self.seen_ids


def check_and_interact_latest(page: Page, username: str, cache: TweetCache):
    url = f"https://x.com/{username}"
    logger.info("Checking timeline: {}", url)
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")

    # 取最近一条 tweet/article
    locator = page.locator(f"{TWEET_DATATESTID_ANY},{TWEET_ARTICLE}").first
    if not locator or locator.count() == 0:
        logger.warning("No tweet/article found on page.")
        return False

    tweet_id = cache.extract_tweet_id(locator)
    if not tweet_id:
        logger.warning("Cannot extract tweet id; skip.")
        return False

    if not cache.is_new(tweet_id):
        logger.info("No new tweet (id seen).")
        return False

    logger.info("New tweet detected: {}", tweet_id)
    cache.mark_seen(tweet_id)

    # 执行转发（不带评论）
    if CONFIG.action.do_retweet:
        try:
            repost = locator.locator(TWEET_REPOST)
            if not repost or repost.count() == 0:
                repost = locator.locator(TWEET_RETWEET)
            repost.first.click()
            time.sleep(0.8)
            # 直接 Retweet（不引用）
            page.get_by_role("menuitem", name="Retweet").or_(page.get_by_text("Repost")).first.click()
            logger.info("已转发该推文。")
        except Exception as e:
            logger.warning("转发展开失败: {}", e)

    # 评论
    if CONFIG.action.do_comment:
        try:
            reply = locator.locator(TWEET_REPLY)
            reply.first.click()
            page.wait_for_selector(TWEET_TEXTAREA, timeout=5000)
            page.fill(TWEET_TEXTAREA, random_comment())
            # 某些布局按钮是 tweetButtonInline 或 tweetButton
            if page.locator(TWEET_BUTTON).count() > 0:
                page.locator(TWEET_BUTTON).click()
            else:
                page.locator(TWEET_BUTTON_MAIN).click()
            logger.info("已评论该推文。")
        except Exception as e:
            logger.warning("评论失败: {}", e)

    return True

