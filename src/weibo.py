from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .comments import random_comment
from .config import CONFIG
import time, re, random

_DEF_RE_DETAIL = re.compile(r"https?://weibo\.com/\d+/[A-Za-z0-9]+", re.I)

WEIBO_HOME = "https://weibo.com"
CARD_QUERY = "#scroller article"


def _card_has_comment(card) -> bool:
    try:
        loc = card.get_by_role("button", name=re.compile("评论|Comment", re.I)).first
        return bool(loc and loc.count() > 0)
    except Exception:
        return False

# 粗粒度 XPath（来自你提供的片段），可能随页面变动，需要后续迭代
X_POST = "//*[@id='scroller']/div[1]/div[1]/div/article/div/div[1]/div[1]/div"
X_LIKE_BTN = "//*[@id='scroller']/div[1]/div[1]/div/article/footer/div/div/div/div[3]/div/button"
X_COMMENT_BTN = "//*[@id='scroller']/div[1]/div[1]/div/article/footer/div/div/div/div[2]/div/div"
X_COMMENT_BOX = "//*[@id='comment-textarea']"
X_FORWARD_TOGGLE = "//*[@id='scroller']/div[1]/div[1]/div/article/div[3]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/label/span[1]"


def open_home_weibo(page: Page):
    page.goto(WEIBO_HOME)
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_selector("#scroller", timeout=20000)
    except Exception:
        logger.warning("Weibo: #scroller not visible in 20s, continue anyway.")


def list_visible_posts(page: Page, limit: int = 20):
    loc = page.locator(CARD_QUERY)
    cnt = min(loc.count(), limit)
    cards = [loc.nth(i) for i in range(cnt)]
    logger.info("Weibo: 可见博文数 {}", cnt)
    return cards


def pick_random_post(page: Page, limit: int = 20, require_comment: bool = True):
    cards = list_visible_posts(page, limit=limit)
    if not cards:
        return None
    # 优先选择含有“评论”按钮的卡片
    if require_comment:
        cards = [c for c in cards if _card_has_comment(c)] or cards
    random.shuffle(cards)
    return cards[0]


def _on_detail_page(page: Page) -> bool:
    try:
        return bool(_DEF_RE_DETAIL.match((page.url or "").split("?")[0]))
    except Exception:
        return False


def login_flow_weibo(page: Page):
    logger.info("Opening Weibo home for login: {}", WEIBO_HOME)
    open_home_weibo(page)
    # 等待主页滚动容器出现（用户可手动扫码/登录）
    try:
        page.wait_for_selector("#scroller", timeout=300000)  # 最多 5 分钟
    except Exception:
        logger.warning("Weibo login wait timed out; continuing if already logged in.")


def like_once(page: Page) -> bool:
    # 若当前已在具体博文详情页，则直接在当前页操作
    if not _on_detail_page(page):
        open_home_weibo(page)
    post = page.query_selector(f"xpath={X_POST}")
    if not post:
        logger.warning("Weibo: 未找到博文内容")
        return False
    try:
        post.evaluate("el => el.scrollIntoView()")
    except Exception:
        pass
    btn = page.query_selector(f"xpath={X_LIKE_BTN}")
    if btn:
        btn.click()
        logger.info("Weibo: 已完成点赞")
        return True
    logger.warning("Weibo: 未找到点赞按钮")
    return False


def comment_once(page: Page) -> bool:
    if not _on_detail_page(page):
        open_home_weibo(page)
    post = page.query_selector(f"xpath={X_POST}")
    if not post:
        logger.warning("Weibo: 未找到博文内容")
        return False
    content = (post.text_content() or "").strip()
    logger.info("Weibo: 已获取博文内容: {}...", content[:50])
    try:
        post.evaluate("el => el.scrollIntoView()")
    except Exception:
        pass

    btn = page.query_selector(f"xpath={X_COMMENT_BTN}")
    if not btn:
        logger.warning("Weibo: 未找到评论按钮")
        return False
    btn.click()
    logger.info("Weibo: 已激活评论框")

    text = random_comment(content)
    box = page.query_selector(f"xpath={X_COMMENT_BOX}")
    if not box:
        logger.warning("Weibo: 未找到评论输入框")
        return False
    box.fill(text)
    logger.info("Weibo: 已输入评论: {}", text)


    try:
        box.press("Control+Enter")
        logger.info("Weibo: 评论已提交")
    except Exception:
        logger.warning("Weibo: 提交热键失败，尝试 Enter"); box.press("Enter")

    # 回主页并滚动以模拟人类
    time.sleep(1.0)
    page.goto(WEIBO_HOME, timeout=30000)
    for i in range(3):
        try:
            page.mouse.wheel(0, 500)
            time.sleep(0.6)
        except Exception:
            break
    return True


def comment_and_optionally_repost(page: Page, do_repost: bool = False, do_like: bool = False, back_to_home: bool = True) -> bool:
    """在评论框内输入后，若 do_repost=True 再点转发开关，最后统一提交。
    保证“转发必须有评论内容”这一业务约束。
    """
    if not _on_detail_page(page):
        open_home_weibo(page)
    post = page.query_selector(f"xpath={X_POST}")
    if not post:
        logger.warning("Weibo: 未找到博文内容")
        return False
    content = (post.text_content() or "").strip()
    logger.info("Weibo: 已获取博文内容: {}...", content[:50])
    try:
        post.evaluate("el => el.scrollIntoView()")
    except Exception:
        pass

    btn = page.query_selector(f"xpath={X_COMMENT_BTN}")
    if not btn:
        logger.warning("Weibo: 未找到评论按钮")
        return False
    btn.click(); logger.info("Weibo: 已激活评论框")

    # 填写评论内容
    text = random_comment(content)
    box = page.query_selector(f"xpath={X_COMMENT_BOX}")
    if not box:
        logger.warning("Weibo: 未找到评论输入框")
        return False
    try:
        box.click();
        box.type(text, delay=35)
    except Exception:
        box.fill(text)
    logger.info("Weibo: 已输入评论: {}", text)

    # 点赞（放在提交前，确保针对同一条卡片）
    if do_like:
        try:
            lbtn = page.query_selector(f"xpath={X_LIKE_BTN}")
            if lbtn:
                lbtn.click(); logger.info("Weibo: 已完成点赞（提交前）")
        except Exception:
            pass

    # 若需要转发，则先勾选转发开关（此时评论已非空）
    if do_repost:
        try:
            fwd = page.query_selector(f"xpath={X_FORWARD_TOGGLE}")
            if fwd:
                fwd.click(); logger.info("Weibo: 已勾选转发")
        except Exception:
            pass

    # 最后统一提交
    try:
        box.press("Control+Enter"); logger.info("Weibo: 评论/转发已提交")
    except Exception:
        try:
            box.press("Enter"); logger.info("Weibo: 评论/转发已提交(Enter)")
        except Exception:
            logger.warning("Weibo: 提交失败")
            return False
    if back_to_home:
        time.sleep(1.0)
        page.goto(WEIBO_HOME, timeout=30000)
    return True



def retweet_once(page: Page) -> bool:
    """按规则：必须先有评论文本再转发。统一复用 comment_and_optionally_repost(do_repost=True)。"""
    return comment_and_optionally_repost(page, do_repost=True)


def interact_on_card(page: Page, card, do_comment: bool, do_like: bool, do_retweet: bool) -> bool:
    ok_any = False
    try:
        if do_comment:
            try:
                cbtn = card.get_by_role("button", name=re.compile("评论|Comment", re.I)).first
                if cbtn and cbtn.count() > 0:
                    cbtn.click(); time.sleep(0.2)
            except Exception:
                pass
            box = None
            # 仅在当前卡片范围内寻找评论输入框，避免命中顶部“发微博”输入框
            for sel in ["#comment-textarea", "textarea", "[role='textbox']"]:
                try:
                    loc = card.locator(sel).first
                    if loc and loc.count() > 0:
                        box = loc; break
                except Exception:
                    continue
            if box:
                text = random_comment("")
                try:
                    box.click(); box.type(text, delay=35)
                except Exception:
                    try:
                        box.fill(text)
                    except Exception:
                        pass
                submitted = False
                try:
                    box.press("Control+Enter"); submitted = True
                except Exception:
                    pass
                if not submitted:
                    # 仅在卡片范围内找按钮，避免点击到全局“发布”按钮
                    for bsel in [
                        "button:has-text('评论')",
                        "button:has-text('发布')",
                        "button:has-text('确定')",
                        "[role=button][aria-label*='评论']",
                        "[role=button][aria-label*='发布']",
                    ]:
                        try:
                            loc = card.locator(bsel).first
                            if loc and loc.count() > 0:
                                loc.click(); submitted = True; break
                        except Exception:
                            continue
                ok_any = ok_any or submitted
        if do_like:
            try:
                for sel in [
                    "button:has-text('赞')",
                    "[role=button][aria-label*='赞']",
                    "button[title*='赞']",
                    "[aria-label*='Like']",
                ]:
                    loc = card.locator(sel).first
                    if loc and loc.count() > 0:
                        loc.click(); ok_any = True; break
            except Exception:
                pass
        if do_retweet:
            try:
                for sel in [
                    "button:has-text('转发')",
                    "[role=button][aria-label*='转发']",
                    "button:has-text('Repost')",
                    "button:has-text('分享')",
                ]:
                    loc = card.locator(sel).first
                    if loc and loc.count() > 0:
                        loc.click(); time.sleep(0.3); break
                for sel in [
                    "button:has-text('发布')",
                    "button:has-text('确定')",
                    "[role=button][aria-label*='发布']",
                    "[role=button][aria-label*='确定']",
                ]:
                    loc = page.locator(sel).first
                    if loc and loc.count() > 0:
                        loc.click(); ok_any = True; break
            except Exception:
                pass
    except Exception as e:
        logger.warning("Weibo: 对当前卡片操作失败 {}", e)
    return ok_any


def follow_once(page: Page) -> bool:
    """针对 CONFIG.users_to_follow 打一次“关注”。支持用户名或完整链接。"""
    success = False
    for u in CONFIG.users_to_follow:
        url = u
        if not re.match(r"^https?://", u, re.I):
            # 尝试两种常见形式：/n/用户名 和 /u/UID
            url = f"https://weibo.com/n/{u}"
        try:
            logger.info("Weibo: 打开用户主页 {}", url)
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)
            # 查找“关注”按钮
            try:
                btn = page.get_by_role("button", name=re.compile(r"^\s*关注\s*$", re.I)).first
                if btn:
                    btn.click(); success = True; logger.info("Weibo: 已点击关注")
                    time.sleep(0.8)
                    continue
            except Exception:
                pass
            # 兜底：文本匹配
            try:
                page.locator("//button//*[text()='关注']/ancestor::button[1]").first.click()
                success = True; logger.info("Weibo: 已点击关注(兜底)")
            except Exception:
                logger.warning("Weibo: 未找到关注按钮 {}", url)
        except Exception as e:
            logger.warning("Weibo: 访问主页失败 {} - {}", url, e)
    return success

