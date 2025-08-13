from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .comments import random_comment
from .config import CONFIG
import time, re, random

_DEF_RE_DETAIL = re.compile(r"https?://weibo\.com/\d+/[A-Za-z0-9]+", re.I)

WEIBO_HOME = "https://weibo.com"
CARD_QUERY = "#scroller article"
# 兜底候选卡片查询（用于不同布局）
FALLBACK_CARD_QUERIES = [
    "#scroller article",
    "article[role='article']",
    "article",
]



# 记录自动化过程中所有关键操作及参数，便于回放/生成代码
class OperationRecorder:
    def __init__(self):
        self.events = []  # list[dict]
        self._t0 = time.perf_counter()

    def _now_ms(self):
        return int((time.perf_counter() - self._t0) * 1000)

    def record(self, kind: str, **data):
        evt = {"t": self._now_ms(), "kind": kind, **data}
        self.events.append(evt)
        try:
            logger.debug("MCP:{}", evt)
        except Exception:
            pass

    def record_navigation(self, url: str, duration_ms: int | None = None):
        self.record("nav", url=url, duration_ms=duration_ms)

        return

    def record_click(self, locator_desc: str, x: float | None, y: float | None, duration_ms: int | None = None):
        self.record("click", locator=locator_desc, x=x, y=y, duration_ms=duration_ms)

    def record_element_snapshot(self, loc, label: str = ""):
        try:
            box = None
            try:
                box = loc.bounding_box()
            except Exception:
                box = None
            attrs = {}
            try:
                attrs["aria-label"] = loc.get_attribute("aria-label")
            except Exception:
                pass
            try:
                attrs["title"] = loc.get_attribute("title")
            except Exception:
                pass
            try:
                tag = loc.evaluate("el => el.tagName")
            except Exception:
                tag = None
            self.record("elem", label=label, box=box, attrs=attrs, tag=tag)
        except Exception:
            pass

    def record_code_step(self, title: str, code: str, meta: dict | None = None):
        self.record("code", title=title, code=code, meta=meta or {})

    def to_mcp_code(self) -> str:
        """将记录转化为带注释的可执行 Python 片段集合，逐步还原实际交互过程。
        仅包含微博点赞/关注/评论/转发相关的操作。
        """
        parts = [
            "from playwright.sync_api import sync_playwright",
            "import re, time",
            "\n",
            "def run():",
            "    with sync_playwright() as p:",
            "        browser = p.chromium.launch(headless=False)",
            "        page = browser.new_page()",
        ]
        for e in self.events:
            k = e.get("kind")
            if k == "nav":
                parts += [
                    f"        # [t+{e.get('t')}ms] 导航",
                    f"        page.goto({e.get('url')!r})",
                    "        page.wait_for_load_state('domcontentloaded')",
                ]
            elif k == "wait":
                dur = e.get("duration_ms") or 300
                parts.append(f"        time.sleep({dur/1000.0:.3f})  # [wait]")
            elif k == "elem":
                parts.append(f"        # 元素快照: label={e.get('label')!r} tag={e.get('tag')!r} attrs={e.get('attrs')} box={e.get('box')}")
            elif k == "click":
                desc = e.get("locator", "")
                x = e.get("x"); y = e.get("y")
                parts += [
                    f"        # [t+{e.get('t')}ms] 点击 {desc}",
                    f"        try:\n            page.locator({desc!r}).first.click()\n        except Exception:\n            pass",
                ]
                if x is not None and y is not None:
                    parts += [
                        f"        # 兜底坐标点击 ({x}, {y})",
                        f"        try:\n            page.mouse.click({x}, {y})\n        except Exception:\n            pass",
                    ]
            elif k == "key":
                parts.append(f"        # 键盘: {e.get('combo')} ({e.get('duration_ms')}ms)")
            elif k == "code":
                title = e.get("title") or "step"
                code = e.get("code") or ""
                parts += [
                    f"        # === {title} (t+{e.get('t')}ms) ===",
                ]
                for ln in code.splitlines():
                    parts.append("        " + ln)
        parts += [
            "        input('MCP run done. Press Enter to close...')",
            "        browser.close()",
            "\n",
            "if __name__ == '__main__':\n    run()",
        ]
        return "\n".join(parts)

        self.record("click", locator=locator_desc, x=x, y=y, duration_ms=duration_ms)

    def record_state(self, name: str, value):
        self.record("state", name=name, value=value)

    def record_wait(self, what: str, duration_ms: int | None = None):
        self.record("wait", what=what, duration_ms=duration_ms)

    def to_python_script(self) -> str:
        """将记录转化为可执行的 Python+Playwright 脚本（简版回放）。
        注意：此回放采用记录到的 locator 文本描述和坐标，可能需要根据页面变化做少量调整。
        """
        lines = [
            "from playwright.sync_api import sync_playwright",
            "import time",
            "\n",
            "def replay():",
            "    with sync_playwright() as p:",
            "        browser = p.chromium.launch(headless=False)",
            "        page = browser.new_page()",
        ]
        for e in self.events:
            k = e.get("kind")
            if k == "nav":
                lines.append(f"        page.goto(\"{e.get('url','')}\")")
                lines.append("        page.wait_for_load_state('domcontentloaded')")
            elif k == "click":
                desc = e.get("locator", "")
                x = e.get("x"); y = e.get("y")
                if desc:
                    lines.append(f"        try:\n            page.locator({desc!r}).first.click()\n        except Exception:\n            pass")
                if x is not None and y is not None:
                    lines.append(f"        try:\n            page.mouse.click({x}, {y})\n        except Exception:\n            pass")
            elif k == "wait":
                dur = e.get("duration_ms") or 300
                lines.append(f"        time.sleep({dur/1000.0:.3f})")
        lines += [
            "        input('Replay done. Press Enter to close...')",
            "        browser.close()",
            "\n",
            "if __name__ == '__main__':\n    replay()",
        ]
        return "\n".join(lines)


def _locator_center_xy(loc) -> tuple[float | None, float | None]:
    """尝试获取 locator 的中心坐标（相对页面视口），以便记录点击坐标。
    Playwright 没有直接 API 返回点击坐标，这里用 bounding_box 估算。
    """
    try:
        box = loc.bounding_box()
        if not box:
            return None, None
        return box["x"] + box["width"] / 2.0, box["y"] + box["height"] / 2.0
    except Exception:
        return None, None


def _text_of(loc) -> str:
    try:
        return (loc.inner_text() or "").strip()
    except Exception:
        return ""

# 状态判断：关注与互动
_FOLLOWED_PAT = re.compile(r"已关注|正在关注|取消关注|Following|已互相关注", re.I)
_FOLLOW_PAT = re.compile(r"^\s*关注\s*$|Follow", re.I)


def detect_follow_status_on_page(page: Page) -> str:
    """返回 'followed' | 'not_followed' | 'unknown'。"""
    try:
        # 优先查找明确文案的按钮
        btn = page.get_by_role("button", name=re.compile("关注|Follow|已关注|取消关注", re.I)).first
        if btn and btn.count() > 0:
            text = _text_of(btn)
            if _FOLLOWED_PAT.search(text):
                return "followed"
            if _FOLLOW_PAT.search(text):
                return "not_followed"
    except Exception:
        pass
    # 兜底：通过 aria-pressed 或 class 态判断
    try:
        any_followed = page.locator("button[aria-pressed='true']").first
        if any_followed and any_followed.count() > 0:
            return "followed"
    except Exception:
        pass
    return "unknown"


def ensure_follow_on_page(page: Page, recorder: OperationRecorder | None = None) -> bool:
    """若未关注则点击关注。返回是否执行了关注操作。"""
    status = detect_follow_status_on_page(page)
    if recorder:
        recorder.record_state("follow_status_before", status)
    if status == "not_followed":
        try:
            btn = page.get_by_role("button", name=_FOLLOW_PAT).first
            if btn and btn.count() > 0:
                x, y = _locator_center_xy(btn)
                t0 = time.perf_counter(); btn.click(); dur = int((time.perf_counter()-t0)*1000)
                if recorder:
                    recorder.record_click("get_by_role('button', name=/关注|Follow/)", x, y, dur)
                time.sleep(0.5)
                return True
        except Exception:
            pass
        # 兜底 XPath
        try:
            loc = page.locator("//button//*[text()='关注']/ancestor::button[1]").first
            if loc and loc.count() > 0:
                x, y = _locator_center_xy(loc)
                t0 = time.perf_counter(); loc.click(); dur = int((time.perf_counter()-t0)*1000)
                if recorder:
                    recorder.record_click("//button//*[text()='关注']/ancestor::button[1]", x, y, dur)
                time.sleep(0.5)
                return True
        except Exception:
            pass
    return False


def detect_interaction_state_on_card(card) -> dict:
    """尽力判断当前卡片的互动状态。"""
    liked = False; commented = False; reposted = False
    # 点赞：常见是 aria-pressed=true 或含激活类
    try:
        lbtn = None
        for sel in [
            "button:has-text('赞')",
            "[role=button][aria-label*='赞']",
            "button[title*='赞']",
            "[aria-pressed='true']",
        ]:
            loc = card.locator(sel).first
            if loc and loc.count() > 0:
                lbtn = loc; break
        if lbtn:
            txt = _text_of(lbtn)
            liked = "已赞" in txt or "取消赞" in txt or "liked" in txt.lower()
            if not liked:
                try:
                    liked = bool(lbtn.get_attribute("aria-pressed") == "true")
                except Exception:
                    pass
    except Exception:
        pass
    # 评论：简单看卡片内是否出现“我”的最新评论输入后标识（难以稳定判断，保守）
    try:
        commented = card.locator(".comment-list, [data-testid*='comment']").count() > 0
    except Exception:
        pass
    # 转发：看是否出现“已转发”或弹出层已提交痕迹（保守）
    try:
        reposted = "已转发" in (card.inner_text() or "")
    except Exception:
        pass
    return {"liked": liked, "commented": commented, "reposted": reposted}


def extract_post_link_from_card(card, page: Page) -> str | None:
    """尝试从卡片中提取详情链接。"""
    try:
        for sel in ["a[href*='weibo.com']", "a[href*='/status']", "time a", "a:has-text('详情')"]:
            loc = card.locator(sel).first
            if loc and loc.count() > 0:
                href = loc.get_attribute("href") or ""
                if _DEF_RE_DETAIL.search(href):
                    return href.split("?")[0]
    except Exception:
        pass
    # 兜底：用当前页 URL（若已在详情页）
    try:
        if _DEF_RE_DETAIL.search((page.url or "")):
            return page.url.split("?")[0]
    except Exception:
        pass
    return None


def automate_on_post(page: Page, do_comment: bool, do_like: bool, do_repost: bool, do_follow: bool = True) -> dict:
    """对当前可见一条博文进行自动化：先判断关注与互动状态，按需执行，最后提取链接。
    返回 {"follow_executed": bool, "like_executed": bool, "comment_executed": bool, "repost_executed": bool, "weibo_link": str|None, "mcp_script": str}
    """
    recorder = OperationRecorder()
    # 进入信息流，确保加载出卡片
    ensure_feed_and_load_cards(page, recorder)
    card = pick_random_post(page, limit=20, require_comment=False)
    if not card:
        return {"error": "no_card_visible", "mcp_script": recorder.to_python_script()}
    try:
        card.scroll_into_view_if_needed()
    except Exception:
        pass

    # 关注逻辑（在卡片范围内优先查找关注按钮，找不到则在页面范围判定）
    follow_executed = False
    try:
        fbtn = card.get_by_role("button", name=_FOLLOW_PAT).first
        if fbtn and fbtn.count() > 0:
            # 判断状态
            text = _text_of(fbtn)
            if _FOLLOWED_PAT.search(text):
                recorder.record_state("follow_status_before", "followed")
            else:
                recorder.record_state("follow_status_before", "not_followed")
                x, y = _locator_center_xy(fbtn)
                t0 = time.perf_counter(); fbtn.click(); dur = int((time.perf_counter()-t0)*1000)
                recorder.record_click("card.get_by_role('button', name=/关注|Follow/)", x, y, dur)
                follow_executed = True
        else:
            follow_executed = ensure_follow_on_page(page, recorder)
    except Exception:
        follow_executed = ensure_follow_on_page(page, recorder)

    # 互动状态判定
    states = detect_interaction_state_on_card(card)
    recorder.record_state("interaction_before", states)

    like_executed = False; comment_executed = False; repost_executed = False
    # 点赞
    if do_like and not states.get("liked"):
        try:
            for sel in ["button:has-text('赞')", "[role=button][aria-label*='赞']", "button[title*='赞']", "[aria-label*='Like']"]:
                loc = card.locator(sel).first
                if loc and loc.count() > 0:
                    x, y = _locator_center_xy(loc)
                    t0 = time.perf_counter(); loc.click(); dur = int((time.perf_counter()-t0)*1000)
                    recorder.record_click(f"card.locator({sel!r}).first", x, y, dur)
                    like_executed = True; break
        except Exception:
            pass

    # 评论与转发：若需要转发，先输入评论再转发
    if (do_comment and not states.get("commented")) or (do_repost and not states.get("reposted")):
        try:
            # 打开评论框
            cbtn = card.get_by_role("button", name=re.compile("评论|Comment", re.I)).first
            if cbtn and cbtn.count() > 0:
                x, y = _locator_center_xy(cbtn)
                t0 = time.perf_counter(); cbtn.click(); dur = int((time.perf_counter()-t0)*1000)
                recorder.record_click("card.get_by_role('button', name=/评论|Comment/)", x, y, dur)
            # 找到文本框
            box = None
            for sel in ["#comment-textarea", "textarea", "[role='textbox']"]:
                loc = card.locator(sel).first
                if loc and loc.count() > 0:
                    box = loc; break
            if box:
                text = random_comment("")
                try:
                    box.click(); box.type(text, delay=35)
                except Exception:
                    box.fill(text)
                comment_executed = do_comment
                # 若需要转发：尝试点击“转发/发布”
                if do_repost and not states.get("reposted"):
                    for sel in ["button:has-text('转发')", "[role=button][aria-label*='转发']", "button:has-text('发布')", "button:has-text('确定')"]:
                        loc = page.locator(sel).first
                        if loc and loc.count() > 0:
                            x, y = _locator_center_xy(loc)
                            t0 = time.perf_counter(); loc.click(); dur = int((time.perf_counter()-t0)*1000)
                            recorder.record_click(f"page.locator({sel!r}).first", x, y, dur)
                            repost_executed = True; break
                else:
                    # 仅评论：提交
                    try:
                        t0 = time.perf_counter(); box.press("Control+Enter"); dur = int((time.perf_counter()-t0)*1000)
                        recorder.record("key", combo="Ctrl+Enter", duration_ms=dur)
                    except Exception:
                        try:
                            t0 = time.perf_counter(); box.press("Enter"); dur = int((time.perf_counter()-t0)*1000)
                            recorder.record("key", combo="Enter", duration_ms=dur)
                        except Exception:
                            pass
        except Exception:
            pass

    link = extract_post_link_from_card(card, page)
    recorder.record_state("post_link", link)

    return {
        "follow_executed": follow_executed,
        "like_executed": like_executed,
        "comment_executed": comment_executed,
        "repost_executed": repost_executed,
        "weibo_link": link,
        "mcp_script": recorder.to_python_script(),
        "mcp_code": recorder.to_mcp_code(),
    }


def _card_has_comment(card) -> bool:
    try:
        loc = card.get_by_role("button", name=re.compile("评论|Comment", re.I)).first
        return bool(loc and loc.count() > 0)
    except Exception:
        return False

# 粗粒度 XPath（来自你提供的片段），可能随页面变动，需要后续迭代

# 进入信息流并等待加载；若当前在个人主页等非信息流视图，尽量切回首页信息流
def ensure_feed_and_load_cards(page: Page, recorder: OperationRecorder | None = None, max_scrolls: int = 6) -> None:
    t0 = time.perf_counter(); page.goto(WEIBO_HOME); page.wait_for_load_state("domcontentloaded"); dur = int((time.perf_counter()-t0)*1000)
    if recorder:
        recorder.record_navigation(WEIBO_HOME, dur)
    # 等待主滚动容器或任何候选卡片出现
    try:
        page.wait_for_selector("#scroller", timeout=15000)
    except Exception:
        pass
    # 若没有任何卡片，尝试点击“首页/发现/推荐”等入口
    def _any_card_present() -> bool:
        for q in FALLBACK_CARD_QUERIES:
            try:
                if page.locator(q).count() > 0:
                    return True
            except Exception:
                continue
        return False
    if not _any_card_present():
        for sel in [
            "a:has-text('首页')", "a:has-text('发现')", "a:has-text('推荐')",
            "[role=link][aria-label*='首页']", "[role=link][aria-label*='发现']",
            "nav a", "[data-testid*='home'] a",
        ]:
            try:
                loc = page.locator(sel).first
                if loc and loc.count() > 0 and loc.is_visible():
                    x, y = _locator_center_xy(loc)
                    t1 = time.perf_counter(); loc.click(); d = int((time.perf_counter()-t1)*1000)
                    if recorder:
                        recorder.record_click(f"page.locator({sel!r}).first", x, y, d)
                    time.sleep(1.0)
                    break
            except Exception:
                continue
    # 滚动加载若干屏
    for i in range(max_scrolls):
        try:
            page.mouse.wheel(0, 800)
            time.sleep(0.8)
        except Exception:
            break

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
    # 优先使用主查询；若数量为0，使用兜底候选
    loc = page.locator(CARD_QUERY)
    cnt = loc.count()
    if cnt == 0:
        for q in FALLBACK_CARD_QUERIES:
            try:
                alt = page.locator(q)
                if alt.count() > 0:
                    loc = alt; cnt = alt.count(); break
            except Exception:
                continue
    cnt = min(cnt, limit)
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


def automate_on_post_alternative(page: Page, do_comment: bool, do_like: bool, do_repost: bool, do_follow: bool = True) -> dict:
    """备选流程模式：按照正确的流程执行微博自动化操作

    正确流程步骤：
    1. 第一步：等待微博首页加载成功
    2. 第二步：获取详情页链接
    3. 第三步：进入详情页
    4. 第四步：提取微博内容
    5. 第五步：执行互动操作（并通过元素变化判断是否互动成功）

    返回 {"follow_executed": bool, "like_executed": bool, "comment_executed": bool, "repost_executed": bool, "weibo_link": str|None, "mcp_script": str}
    """
    recorder = OperationRecorder()

    # 第一步：等待微博首页加载成功
    logger.info("备选流程 - 第一步：等待微博首页加载成功")
    t0 = time.perf_counter()

    # 确保在微博首页并加载卡片（不滚动）
    t0 = time.perf_counter()
    page.goto(WEIBO_HOME)
    page.wait_for_load_state("domcontentloaded")
    dur = int((time.perf_counter()-t0)*1000)
    recorder.record_navigation(WEIBO_HOME, dur)

    # 等待主滚动容器出现
    try:
        page.wait_for_selector("#scroller", timeout=15000)
    except Exception:
        pass

    # 获取一条微博卡片
    card = pick_random_post(page, limit=20, require_comment=False)
    if not card:
        logger.warning("备选流程：未找到可用的微博卡片")
        return {"error": "no_card_visible", "mcp_script": recorder.to_python_script()}

    try:
        card.scroll_into_view_if_needed()
    except Exception:
        pass

    load_duration = time.perf_counter() - t0
    logger.info("备选流程：首页加载完成，耗时 {:.1f} 秒", load_duration)

    # 第二步：获取详情页链接
    logger.info("备选流程 - 第二步：获取详情页链接")
    detail_link = None

    # 尝试多种方式获取详情页链接
    try:
        # 方法1：使用现有函数
        detail_link = extract_post_link_from_card(card, page)
        if detail_link:
            logger.info("备选流程：通过extract_post_link_from_card获取到链接 - {}", detail_link)
        else:
            # 方法2：智能链接分析
            logger.info("备选流程：开始智能链接分析")

            try:
                all_links = card.locator("a").all()
                logger.debug("备选流程：卡片中找到 {} 个链接", len(all_links))

                for i, link in enumerate(all_links):
                    try:
                        href = link.get_attribute("href") or ""
                        text = link.inner_text() or ""
                        logger.debug("备选流程：链接 {}: href={}, text={}", i, href, text[:20])

                        # 检查是否是微博详情页链接
                        if href and _DEF_RE_DETAIL.search(href):
                            detail_link = href.split("?")[0]
                            logger.info("备选流程：找到详情页链接 - {}", detail_link)
                            break
                        elif href and "/status/" in href:
                            # 构造完整URL
                            if href.startswith("/"):
                                detail_link = f"https://weibo.com{href}"
                            else:
                                detail_link = href
                            detail_link = detail_link.split("?")[0]
                            logger.info("备选流程：找到status链接 - {}", detail_link)
                            break
                    except Exception as e:
                        logger.debug("备选流程：分析链接 {} 失败: {}", i, e)
                        continue
            except Exception as e:
                logger.warning("备选流程：智能链接分析失败 - {}", e)
    except Exception as e:
        logger.warning("备选流程：获取链接过程出错 - {}", e)

    if not detail_link:
        logger.warning("备选流程：未找到详情页链接")
        return {"error": "no_detail_link", "mcp_script": recorder.to_python_script()}

    logger.info("备选流程：成功获取详情页链接 - {}", detail_link)
    recorder.record("extract_link", link=detail_link)

    # 第三步：进入详情页
    logger.info("备选流程 - 第三步：进入详情页")
    t0 = time.perf_counter()
    try:
        page.goto(detail_link)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2.0)  # 等待完全加载
        dur = int((time.perf_counter() - t0) * 1000)
        recorder.record_navigation(detail_link, dur)
        recorder.record("sleep", duration=2.0)
        logger.info("备选流程：成功进入详情页，耗时 {:.1f} 秒", dur/1000)
    except Exception as e:
        logger.error("备选流程：进入详情页失败 - {}", e)
        return {"error": "detail_page_failed", "mcp_script": recorder.to_python_script()}

    # 第四步：提取微博内容
    logger.info("备选流程 - 第四步：提取微博内容")
    content_text = ""

    def extract_content_with_multiple_strategies(page) -> str:
        """使用多种策略提取微博内容"""

        # 策略1：详情页专用选择器（更全面的选择器列表）
        detail_page_selectors = [
            # 详情页主要内容区域
            "article .txt",
            "article [node-type='feed_list_content']",
            "[data-testid='post-content']",
            ".detail-content .txt",
            ".post-content",
            ".weibo-detail .txt",
            # 微博新版本选择器
            ".Feed_body .txt",
            ".Feed_content .txt",
            ".WB_text",
            ".WB_detail .txt",
            # 通用内容选择器
            ".txt",
            ".weibo-text",
            ".content-text",
            "[node-type='feed_list_content']",
            # 更多可能的选择器
            ".post-text",
            ".status-text",
            ".weibo-content",
            "[class*='text']",
            "[class*='content']"
        ]

        logger.debug("备选流程：尝试策略1 - 详情页专用选择器")
        for sel in detail_page_selectors:
            try:
                elements = page.locator(sel).all()
                for i, elem in enumerate(elements):
                    if elem.count() > 0:
                        text = elem.inner_text() or ""
                        if text.strip() and len(text.strip()) > 10:  # 确保内容有意义
                            logger.info("备选流程：策略1成功 - 选择器: {}, 元素: {}, 内容: {}...", sel, i, text[:50])
                            return text.strip()
            except Exception as e:
                logger.debug("备选流程：选择器 {} 失败: {}", sel, e)
                continue

        # 策略2：XPath选择器（适配详情页）
        detail_page_xpaths = [
            # 详情页文章内容
            "//article//div[contains(@class, 'txt')]",
            "//article//div[@node-type='feed_list_content']",
            "//div[contains(@class, 'detail')]//div[contains(@class, 'txt')]",
            # 通用文章内容
            "//article//div[text()]",
            "//div[contains(@class, 'post')]//div[text()]",
            "//div[contains(@class, 'content')]//div[text()]"
        ]

        logger.debug("备选流程：尝试策略2 - XPath选择器")
        for xpath in detail_page_xpaths:
            try:
                elements = page.locator(f"xpath={xpath}").all()
                for i, elem in enumerate(elements):
                    if elem.count() > 0:
                        text = elem.inner_text() or ""
                        if text.strip() and len(text.strip()) > 10:
                            logger.info("备选流程：策略2成功 - XPath: {}, 元素: {}, 内容: {}...", xpath, i, text[:50])
                            return text.strip()
            except Exception as e:
                logger.debug("备选流程：XPath {} 失败: {}", xpath, e)
                continue

        # 策略3：智能文本内容查找
        logger.debug("备选流程：尝试策略3 - 智能文本内容查找")
        try:
            # 查找包含较多文本的元素
            text_elements = page.locator("div, p, span").all()
            candidates = []

            for i, elem in enumerate(text_elements):
                try:
                    text = elem.inner_text() or ""
                    text = text.strip()

                    # 过滤条件：文本长度适中，不包含导航元素
                    if (15 <= len(text) <= 2000 and
                        not any(keyword in text for keyword in [
                            "关注", "点赞", "评论", "转发", "首页", "发现", "热搜",
                            "登录", "注册", "设置", "消息", "通知", "搜索",
                            "更多", "展开", "收起", "全文", "网页链接"
                        ])):
                        # 计算文本质量分数
                        score = len(text)
                        # 如果包含中文，加分
                        if any('\u4e00' <= char <= '\u9fff' for char in text):
                            score += 50
                        # 如果包含标点符号，加分
                        if any(char in text for char in "。！？，；："):
                            score += 30

                        candidates.append((score, text, i))
                except Exception:
                    continue

            # 按分数排序，选择最佳候选
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_text = candidates[0][1]
                best_index = candidates[0][2]
                logger.info("备选流程：策略3成功 - 元素{}, 分数{}, 内容: {}...",
                          best_index, candidates[0][0], best_text[:50])
                return best_text

        except Exception as e:
            logger.debug("备选流程：策略3失败: {}", e)

        # 策略4：使用精准模式的XPath（如果在详情页也适用）
        logger.debug("备选流程：尝试策略4 - 精准模式XPath")
        try:
            post_elem = page.query_selector(f"xpath={X_POST}")
            if post_elem:
                text = post_elem.text_content() or ""
                if text.strip():
                    logger.info("备选流程：策略4成功 - 精准模式XPath, 内容: {}...", text[:50])
                    return text.strip()
        except Exception as e:
            logger.debug("备选流程：策略4失败: {}", e)

        # 策略5：微博详情页特殊结构处理
        logger.debug("备选流程：尝试策略5 - 详情页特殊结构")
        try:
            # 尝试获取页面标题作为内容（有时微博内容会在标题中）
            page_title = page.title()
            if page_title and len(page_title.strip()) > 20:
                # 清理标题中的微博相关后缀
                clean_title = page_title.replace(" - 微博", "").replace("的微博", "").strip()
                if len(clean_title) > 15:
                    logger.info("备选流程：策略5成功 - 页面标题, 内容: {}...", clean_title[:50])
                    return clean_title

            # 尝试从meta标签获取描述
            meta_desc = page.locator("meta[name='description']").get_attribute("content")
            if meta_desc and len(meta_desc.strip()) > 20:
                clean_desc = meta_desc.strip()
                logger.info("备选流程：策略5成功 - meta描述, 内容: {}...", clean_desc[:50])
                return clean_desc

            # 尝试从JSON-LD结构化数据获取
            json_ld_scripts = page.locator("script[type='application/ld+json']").all()
            for script in json_ld_scripts:
                try:
                    import json
                    script_content = script.inner_text()
                    data = json.loads(script_content)
                    if isinstance(data, dict) and "text" in data:
                        text = data["text"]
                        if text and len(text.strip()) > 15:
                            logger.info("备选流程：策略5成功 - JSON-LD, 内容: {}...", text[:50])
                            return text.strip()
                except Exception:
                    continue

        except Exception as e:
            logger.debug("备选流程：策略5失败: {}", e)

        return ""

    try:
        logger.info("备选流程：开始多策略内容提取...")
        content_text = extract_content_with_multiple_strategies(page)
        if content_text:
            recorder.record("extract_content", strategy="multi_strategy", content_length=len(content_text))
            logger.info("备选流程：✅ 成功提取内容 ({} 字符) - {}...", len(content_text), content_text[:50])
        else:
            logger.warning("备选流程：❌ 所有策略都未能提取到内容")
            # 记录页面信息用于调试
            try:
                page_title = page.title()
                page_url = page.url
                logger.warning("备选流程：调试信息 - 标题: {}, URL: {}", page_title, page_url)

                # 记录页面上所有可见文本元素的数量
                all_text_elements = page.locator("div, p, span").count()
                logger.warning("备选流程：页面上共有 {} 个文本元素", all_text_elements)

                # 尝试获取页面的基本结构信息
                articles = page.locator("article").count()
                divs_with_txt = page.locator("div.txt").count()
                logger.warning("备选流程：页面结构 - article: {}, div.txt: {}", articles, divs_with_txt)

            except Exception as debug_e:
                logger.warning("备选流程：获取调试信息失败 - {}", debug_e)
    except Exception as e:
        logger.warning("备选流程：提取内容过程失败 - {}", e)

    # 第五步：执行互动操作（使用精准模式的互动代码）
    logger.info("备选流程 - 第五步：执行互动操作（使用精准模式）")

    # 互动操作结果
    follow_executed = False
    like_executed = False
    comment_executed = False
    repost_executed = False

    # 操作间隔函数
    def wait_between_actions(action_name: str):
        wait_time = random.uniform(1.0, 3.0)  # 1-3秒随机间隔
        logger.info("备选流程：{} 完成，等待 {:.1f} 秒后继续下一个操作", action_name, wait_time)
        time.sleep(wait_time)
        recorder.record("sleep", duration=wait_time)

    # 1. 关注操作（如果需要）
    if do_follow:
        logger.info("备选流程：开始执行关注操作")
        try:
            follow_executed = ensure_follow_on_page(page, recorder)
            if follow_executed:
                wait_between_actions("关注")
        except Exception as e:
            logger.warning("备选流程：关注操作失败 - {}", e)

    # 2. 在详情页执行互动操作（使用与精准模式一致的代码）
    logger.info("备选流程：在详情页执行互动操作")

    # 确保在详情页
    if not _on_detail_page(page):
        logger.warning("备选流程：不在详情页，无法执行互动操作")
        return {
            "follow_executed": follow_executed,
            "like_executed": False,
            "comment_executed": False,
            "repost_executed": False,
            "weibo_link": detail_link,
            "mcp_script": recorder.to_python_script(),
            "content_text": content_text[:100] + "..." if len(content_text) > 100 else content_text,
            "error": "not_on_detail_page"
        }

    # 2.1 关注操作（如果需要）
    if do_follow:
        logger.info("备选流程：执行关注操作")
        try:
            follow_executed = ensure_follow_on_page(page, recorder)
            if follow_executed:
                logger.info("备选流程：关注成功")
                wait_between_actions("关注")
        except Exception as e:
            logger.warning("备选流程：关注操作失败 - {}", e)

    # 2.2 使用正常模式的互动流程
    if do_comment or do_repost:
        logger.info("备选流程：开始正常模式互动流程")
        logger.info("备选流程：已获取博文内容: {}...", content_text[:50])

        try:
            # 滚动到视图中（如果需要）
            try:
                page.evaluate("window.scrollTo(0, 0)")  # 滚动到页面顶部
                time.sleep(0.5)
            except Exception:
                pass

            # 1. 查找并激活评论输入框（详情页可能直接有输入框）
            logger.info("备选流程：查找评论输入框或评论按钮")

            # 首先尝试直接查找评论输入框
            comment_box_selectors = [
                f"xpath={X_COMMENT_BOX}",  # 精准模式的评论框XPath
                "textarea[placeholder*='评论']",
                "textarea[placeholder*='说点什么']",
                "#comment-textarea",
                ".comment-textarea",
                "textarea"
            ]

            comment_box = None
            for sel in comment_box_selectors:
                try:
                    if sel.startswith("xpath="):
                        box = page.query_selector(sel)
                    else:
                        box = page.locator(sel).first
                        if box.count() == 0:
                            box = None

                    if box:
                        # 检查输入框是否可见和可用
                        try:
                            is_visible = box.is_visible()
                            is_enabled = box.is_enabled()
                            if is_visible and is_enabled:
                                comment_box = box
                                logger.info("备选流程：找到可用的评论输入框")
                                break
                        except Exception:
                            pass
                except Exception as e:
                    logger.debug("备选流程：评论框选择器 {} 失败: {}", sel, e)
                    continue

            # 如果没有找到可用的输入框，尝试点击评论按钮激活
            if not comment_box:
                logger.info("备选流程：未找到可用评论框，尝试点击评论按钮激活")
                comment_btn_selectors = [
                    f"xpath={X_COMMENT_BTN}",  # 精准模式的评论按钮XPath
                    "button:has-text('评论')",
                    "[role=button]:has-text('评论')",
                    ".comment-btn",
                    "button[title*='评论']",
                    # 添加更多可能的选择器
                    ".comment-area",
                    ".comment-trigger",
                    "[data-testid*='comment']"
                ]

                btn_clicked = False
                for sel in comment_btn_selectors:
                    try:
                        if sel.startswith("xpath="):
                            btn = page.query_selector(sel)
                        else:
                            btn = page.locator(sel).first
                            if btn.count() == 0:
                                btn = None

                        if btn:
                            # 检查按钮是否可用
                            try:
                                is_enabled = btn.is_enabled()
                                is_visible = btn.is_visible()
                                if is_visible and is_enabled:
                                    btn.click()
                                    btn_clicked = True
                                    logger.info("备选流程：已点击评论按钮")
                                    time.sleep(1.0)  # 等待评论框出现
                                    break
                                else:
                                    logger.debug("备选流程：评论按钮不可用 - 可见:{} 启用:{}", is_visible, is_enabled)
                            except Exception:
                                # 尝试强制点击
                                btn.click()
                                btn_clicked = True
                                logger.info("备选流程：已强制点击评论按钮")
                                time.sleep(1.0)
                                break
                    except Exception as e:
                        logger.debug("备选流程：评论按钮选择器 {} 失败: {}", sel, e)
                        continue

                # 如果点击了按钮，重新查找评论框
                if btn_clicked:
                    for sel in comment_box_selectors:
                        try:
                            if sel.startswith("xpath="):
                                box = page.query_selector(sel)
                            else:
                                box = page.locator(sel).first
                                if box.count() == 0:
                                    box = None

                            if box:
                                try:
                                    is_visible = box.is_visible()
                                    is_enabled = box.is_enabled()
                                    if is_visible and is_enabled:
                                        comment_box = box
                                        logger.info("备选流程：点击按钮后找到评论输入框")
                                        break
                                except Exception:
                                    pass
                        except Exception:
                            continue

            # 如果仍然没有找到评论框，尝试其他方法
            if not comment_box:
                logger.warning("备选流程：未找到可用的评论输入框，尝试其他方法")

                # 尝试点击页面上的任何文本区域来激活评论
                try:
                    # 查找任何可能的评论相关区域
                    comment_areas = page.locator(".comment, .reply, [placeholder*='说'], [placeholder*='评']").all()
                    for area in comment_areas:
                        try:
                            if area.is_visible():
                                area.click()
                                time.sleep(0.5)
                                logger.info("备选流程：尝试点击评论区域激活")
                                break
                        except Exception:
                            continue

                    # 重新查找评论框
                    for sel in comment_box_selectors:
                        try:
                            if sel.startswith("xpath="):
                                box = page.query_selector(sel)
                            else:
                                box = page.locator(sel).first
                                if box.count() == 0:
                                    box = None

                            if box and box.is_visible():
                                comment_box = box
                                logger.info("备选流程：激活后找到评论输入框")
                                break
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug("备选流程：尝试激活评论区域失败: {}", e)

            if not comment_box:
                logger.warning("备选流程：所有方法都未能找到评论输入框")
                return {
                    "follow_executed": follow_executed,
                    "like_executed": False,
                    "comment_executed": False,
                    "repost_executed": False,
                    "weibo_link": detail_link,
                    "mcp_script": recorder.to_python_script(),
                    "content_text": content_text[:100] + "..." if len(content_text) > 100 else content_text,
                    "error": "comment_box_not_found"
                }

            # 2. 生成评论内容
            from .comments import random_comment
            comment_text = random_comment(content_text)
            logger.info("备选流程：生成评论内容: {}", comment_text)

            # 3. 填写评论输入框（已经找到了comment_box）
            try:
                comment_box.click()
                time.sleep(0.3)
                comment_box.type(comment_text, delay=35)
                logger.info("备选流程：已输入评论: {}", comment_text)
            except Exception:
                try:
                    comment_box.fill(comment_text)
                    logger.info("备选流程：已填写评论: {}", comment_text)
                except Exception as e:
                    logger.warning("备选流程：评论输入失败 - {}", e)
                    return {
                        "follow_executed": follow_executed,
                        "like_executed": False,
                        "comment_executed": False,
                        "repost_executed": False,
                        "weibo_link": detail_link,
                        "mcp_script": recorder.to_python_script(),
                        "content_text": content_text[:100] + "..." if len(content_text) > 100 else content_text,
                        "error": "comment_input_failed"
                    }

            # 4. 按需执行点赞操作（放在提交前，确保针对同一条内容）
            if do_like:
                logger.info("备选流程：执行点赞操作")
                try:
                    like_btn_selectors = [
                        f"xpath={X_LIKE_BTN}",  # 精准模式的点赞按钮XPath
                        "button:has-text('赞')",
                        "[role=button][aria-label*='赞']",
                        "button[title*='赞']"
                    ]

                    for sel in like_btn_selectors:
                        try:
                            if sel.startswith("xpath="):
                                lbtn = page.query_selector(sel)
                            else:
                                lbtn = page.locator(sel).first
                                if lbtn.count() == 0:
                                    lbtn = None

                            if lbtn:
                                lbtn.click()
                                like_executed = True
                                logger.info("备选流程：已完成点赞（提交前）")
                                break
                        except Exception as e:
                            logger.debug("备选流程：点赞按钮选择器 {} 失败: {}", sel, e)
                            continue
                except Exception as e:
                    logger.warning("备选流程：点赞操作失败 - {}", e)

            # 5. 按需勾选转发选项
            if do_repost:
                logger.info("备选流程：勾选转发选项")
                try:
                    forward_toggle_selectors = [
                        f"xpath={X_FORWARD_TOGGLE}",  # 精准模式的转发开关XPath
                        "input[type='checkbox'][name*='forward']",
                        "input[type='checkbox'][name*='repost']",
                        ".forward-checkbox",
                        ".repost-checkbox"
                    ]

                    for sel in forward_toggle_selectors:
                        try:
                            if sel.startswith("xpath="):
                                fwd = page.query_selector(sel)
                            else:
                                fwd = page.locator(sel).first
                                if fwd.count() == 0:
                                    fwd = None

                            if fwd:
                                fwd.click()
                                repost_executed = True
                                logger.info("备选流程：已勾选转发")
                                break
                        except Exception as e:
                            logger.debug("备选流程：转发开关选择器 {} 失败: {}", sel, e)
                            continue
                except Exception as e:
                    logger.warning("备选流程：转发勾选失败 - {}", e)

            # 6. 通过快捷键提交评论/转发
            logger.info("备选流程：提交评论/转发")
            try:
                # 使用已找到的评论框进行提交
                try:
                    comment_box.press("Control+Enter")
                    logger.info("备选流程：评论/转发已提交")
                    comment_executed = do_comment
                    if not repost_executed and do_repost:
                        repost_executed = True  # 如果转发开关没找到，但评论提交成功，也认为转发成功
                except Exception:
                    try:
                        comment_box.press("Enter")
                        logger.info("备选流程：评论/转发已提交(Enter)")
                        comment_executed = do_comment
                        if not repost_executed and do_repost:
                            repost_executed = True
                    except Exception:
                        # 尝试查找提交按钮
                        submit_btn_selectors = [
                            "button:has-text('发布')",
                            "button:has-text('评论')",
                            "button:has-text('提交')",
                            ".submit-btn",
                            ".publish-btn"
                        ]

                        submit_success = False
                        for btn_sel in submit_btn_selectors:
                            try:
                                submit_btn = page.locator(btn_sel).first
                                if submit_btn.count() > 0 and submit_btn.is_visible():
                                    submit_btn.click()
                                    logger.info("备选流程：通过按钮提交成功")
                                    comment_executed = do_comment
                                    if not repost_executed and do_repost:
                                        repost_executed = True
                                    submit_success = True
                                    break
                            except Exception:
                                continue

                        if not submit_success:
                            logger.warning("备选流程：所有提交方法都失败")
            except Exception as e:
                logger.warning("备选流程：提交过程失败 - {}", e)

            # 等待提交完成
            time.sleep(1.0)
            wait_between_actions("互动操作")

        except Exception as e:
            logger.warning("备选流程：正常模式互动流程失败 - {}", e)

    # 如果只需要点赞（没有评论和转发）
    elif do_like:
        logger.info("备选流程：执行单独点赞操作")
        try:
            like_btn_selectors = [
                f"xpath={X_LIKE_BTN}",
                "button:has-text('赞')",
                "[role=button][aria-label*='赞']",
                "button[title*='赞']"
            ]

            for sel in like_btn_selectors:
                try:
                    if sel.startswith("xpath="):
                        lbtn = page.query_selector(sel)
                    else:
                        lbtn = page.locator(sel).first
                        if lbtn.count() == 0:
                            lbtn = None

                    if lbtn:
                        lbtn.click()
                        like_executed = True
                        logger.info("备选流程：点赞成功")
                        wait_between_actions("点赞")
                        break
                except Exception as e:
                    logger.debug("备选流程：点赞按钮选择器 {} 失败: {}", sel, e)
                    continue
        except Exception as e:
            logger.warning("备选流程：点赞操作失败 - {}", e)



    # 返回结果
    result = {
        "follow_executed": follow_executed,
        "like_executed": like_executed,
        "comment_executed": comment_executed,
        "repost_executed": repost_executed,
        "weibo_link": detail_link,
        "mcp_script": recorder.to_python_script(),
        "content_text": content_text[:100] + "..." if len(content_text) > 100 else content_text
    }

    logger.info("备选流程完成：关注={} 点赞={} 评论={} 转发={}",
                follow_executed, like_executed, comment_executed, repost_executed)

    return result

