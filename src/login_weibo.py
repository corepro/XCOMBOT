from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .weibo import WEIBO_HOME, open_home_weibo
from .browser import BrowserManager
import time, os, re

WEIBO_LOGIN_URL = "https://passport.weibo.com/sso/signin?entry=miniblog&source=miniblog&url=https%3A%2F%2Fweibo.com%2F"


# 登录提示/按钮的检测（出现则判定为未登录）
_LOGIN_PROMPT_SELECTORS = [
    "text=登录/注册",
    "text=/登录\s*\/\s*注册/",
    "button:has-text('登录/注册')",
    "button:has-text('登录')",
    "a:has-text('登录')",
    "text=扫码登录",
    "text=手机登录",
    "text=立即登录",
    "text=登录微博",
]


def _has_login_prompt(page: Page) -> bool:
    try:
        # 优先通过可访问名匹配按钮
        import re as _re
        btn = page.get_by_role("button", name=_re.compile("登录|注册")).first
        if btn and btn.count() > 0 and btn.is_visible():
            return True
        # 其次通过文本匹配“登录/注册”
        t = page.get_by_text("登录/注册").first
        if t and t.count() > 0 and t.is_visible():
            return True
        # 兜底：遍历预设选择器
        for sel in _LOGIN_PROMPT_SELECTORS:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return True
    except Exception:
        pass
    # 如果仍在 passport.weibo.com 域名上，视为未登录
    try:
        if "passport.weibo.com" in (page.url or ""):
            return True
    except Exception:
        pass
    return False


def _has_auth_cookie(page: Page) -> bool:
    try:
        cookies = page.context.cookies([WEIBO_HOME])
        names = {c.get("name") for c in cookies}
        return "SUB" in names or "SUBP" in names
    except Exception:
        return False


def _query_username_from_ui(page: Page) -> str | None:
    """从页面元素优先提取用户名：
    - a[href^="/u/"] 或 a[href*="weibo.com/u/"] 的文本
    - 尝试读取全局变量 $CONFIG.nick/onick/screen_name
    - 回退：尝试从顶部导航可见的用户卡片/按钮文本中提取
    """
    try:
        # 1) 走 anchor
        name = page.evaluate(
            """
            () => {
              const anchors = Array.from(document.querySelectorAll('a'));
              for (const a of anchors) {
                const href = (a.getAttribute('href')||'');
                const text = (a.innerText||'').trim();
                if ((href.startsWith('/u/') || href.includes('weibo.com/u/')) && text && text.length <= 24) {
                  return text;
                }
              }
              const cfg = (window.$CONFIG||{});
              const nick = cfg.nick || cfg.onick || cfg.screen_name || cfg.uid || null;
              return nick || null;
            }
            """
        )
        if name and isinstance(name, str) and 1 < len(name) <= 32:
            return name.strip()
    except Exception:
        pass
    # 2) 通过可见元素上的 title/aria-label 猜测
    for sel in ["[aria-label*='我的']", "[title*='我的']", "header a[href^='/u/']"]:
        try:
            el = page.locator(sel).first
            if el and el.count() > 0 and el.is_visible():
                txt = (el.inner_text() or "").strip()
                if 1 < len(txt) <= 32:
                    return txt
        except Exception:
            continue
    return None


def _has_logged_in_ui(page: Page) -> bool:
    if _query_username_from_ui(page):
        return True
    # 常见已登录元素：发布按钮、评论框等
    for sel in ["button:has-text('发布')", "#comment-textarea", "[role='textbox']", "[aria-label*='发布']"]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return True
        except Exception:
            continue
    return False


def get_logged_in_username(page: Page) -> str | None:
    # 若存在“登录/注册”等提示，或仍在 passport 域名，明确未登录
    try:
        if _has_login_prompt(page):
            return None
        if "passport.weibo.com" in (page.url or ""):
            return None
    except Exception:
        pass
    # 优先用 UI 提取用户名
    name = _query_username_from_ui(page)
    if name:
        return name
    # 用户名拿不到则认为未登录（不再仅凭 Cookie 判定登录，避免误判）
    return None


def is_logged_in_weibo(page: Page) -> bool:
    return get_logged_in_username(page) is not None


def ensure_login_weibo(page: Page, timeout_sec: int = 300, on_logged_in=None) -> bool:
    """旧接口：保留兼容。推荐使用 login_flow_weibo(bm)。"""
    open_home_weibo(page)
    if is_logged_in_weibo(page):
        logger.info("Weibo: 检测到已登录。")
        if on_logged_in:
            try:
                on_logged_in()
            except Exception:
                pass
        return True
    logger.info("Weibo: 未检测到登录状态，请在打开的页面完成登录（扫码/密码），最多等待{}秒…", timeout_sec)
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    while time.time() < deadline:
        if _has_login_prompt(page):
            pass
        elif _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("Weibo: 登录成功。")
            try:
                if on_logged_in:
                    on_logged_in()
            except Exception:
                pass
            return True
        if time.time() - last_log > 10:
            logger.info("等待登录中…（检测到未登录界面）")
            last_log = time.time()
        time.sleep(1.2)
    logger.warning("Weibo: 登录等待超时；请确认是否已登录。")
    return False


def login_flow_weibo(bm: BrowserManager, timeout_sec: int = 300) -> None:
    """打开官方登录页并等待登录成功；登录成功将自动跳转到 weibo.com，或出现已登录元素/授权 Cookie。
    成功后保存 storage_state。
    """
    page = bm.page
    assert page is not None
    logger.info("打开 Weibo 登录页: {}", WEIBO_LOGIN_URL)
    page.goto(WEIBO_LOGIN_URL)

    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    while time.time() < deadline:
        cur = page.url or ""
        # 1) 登录页上若看到 登录/注册 提示，则继续等待
        if _has_login_prompt(page):
            pass
        # 2) 已跳转到 weibo.com 或检测到已登录元素/授权 Cookie，即视为成功
        if ("weibo.com" in cur and "passport.weibo.com" not in cur) or _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("Weibo: 登录成功，当前URL={}。保存会话…", cur)
            bm.save_storage(); return
        if time.time() - last_log > 10:
            logger.info("等待登录中… 当前URL={}", cur)
            last_log = time.time()
        time.sleep(1.0)
    raise TimeoutError("Weibo 登录等待超时")


def weibo_probe_login_and_comment(bm: BrowserManager, dry_run: bool = True) -> str:
    """开启 Playwright Trace，检查“登录→评论框打开→（可选）提交”流程。
    返回 trace 文件路径。
    """
    traces_dir = os.path.join("traces")
    os.makedirs(traces_dir, exist_ok=True)
    trace_path = os.path.join(traces_dir, "weibo_login_comment_trace.zip")
    if bm.context:
        try:
            bm.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        except Exception:
            pass
    page = bm.page
    assert page is not None
    # 执行登录流
    login_flow_weibo(bm, timeout_sec=180)
    # 尝试打开评论框再关闭（不真正发送）
    try:
        # 常见评论按钮
        cbtn = page.get_by_role("button", name="评论").first
        if cbtn and cbtn.count() > 0:
            cbtn.click(); time.sleep(0.3)
        # 找到文本框
        box = None
        for sel in ["#comment-textarea", "textarea", "[role='textbox']"]:
            try:
                loc = page.locator(sel).first
                if loc and loc.count() > 0:
                    box = loc; break
            except Exception:
                continue
        if box:
            box.fill("自动化检查，不发送")
            if not dry_run:
                try:
                    box.press("Control+Enter")
                except Exception:
                    pass
            else:
                # 仅演示输入，ESC 关闭
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
    finally:
        try:
            if bm.context:
                bm.context.tracing.stop(path=trace_path)
        except Exception:
            pass
    logger.info("Weibo Trace 已保存：{}", trace_path)
    return trace_path

