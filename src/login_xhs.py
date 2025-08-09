from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .xhs import XHS_HOME, open_home_xhs
from .browser import BrowserManager
import time, os, re

XHS_LOGIN_URL = "https://www.xiaohongshu.com/explore"

# 登录提示/按钮的检测（出现则判定为未登录）
_LOGIN_PROMPT_SELECTORS = [
    "text=登录",
    "button:has-text('登录')",
    "text=注册",
    "text=扫码登录",
    "text=手机登录",
    "text=立即登录",
    "text=登录小红书",
    "a:has-text('登录')",
]


def _has_login_prompt(page: Page) -> bool:
    try:
        # 优先通过可访问名匹配按钮
        import re as _re
        btn = page.get_by_role("button", name=_re.compile("登录|注册")).first
        if btn and btn.count() > 0 and btn.is_visible():
            return True
        # 其次通过文本匹配"登录"
        t = page.get_by_text("登录").first
        if t and t.count() > 0 and t.is_visible():
            return True
        # 兜底：遍历预设选择器
        for sel in _LOGIN_PROMPT_SELECTORS:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return True
    except Exception:
        pass
    # 如果在 passport 域名上，视为未登录
    try:
        if "passport" in (page.url or ""):
            return True
    except Exception:
        pass
    return False


def _has_auth_cookie(page: Page) -> bool:
    try:
        cookies = page.context.cookies([XHS_HOME])
        names = {c.get("name") for c in cookies}
        # 小红书常见的认证cookie
        return "web_session" in names or "xsecappid" in names or "a1" in names
    except Exception:
        return False


def _query_username_from_ui(page: Page) -> str | None:
    """从页面元素提取用户名"""
    try:
        # 尝试从用户头像或用户名元素提取
        name = page.evaluate(
            """
            () => {
              // 查找用户相关的链接或元素
              const userLinks = Array.from(document.querySelectorAll('a[href*="/user/"]'));
              for (const a of userLinks) {
                const text = (a.innerText||'').trim();
                if (text && text.length <= 24 && !text.includes('http')) {
                  return text;
                }
              }
              // 查找可能的用户名显示元素
              const userElements = Array.from(document.querySelectorAll('[class*="user"], [class*="name"], [class*="nick"]'));
              for (const el of userElements) {
                const text = (el.innerText||'').trim();
                if (text && text.length > 1 && text.length <= 32 && !text.includes('http')) {
                  return text;
                }
              }
              return null;
            }
            """
        )
        if name and isinstance(name, str) and 1 < len(name) <= 32:
            return name.strip()
    except Exception:
        pass
    return None


def _has_logged_in_ui(page: Page) -> bool:
    if _query_username_from_ui(page):
        return True
    # 常见已登录元素：发布按钮、评论框等
    for sel in [
        "button:has-text('发布')", 
        "button:has-text('发笔记')",
        "[role='textbox']", 
        "[aria-label*='发布']",
        "[class*='publish']",
        "[class*='create']"
    ]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return True
        except Exception:
            continue
    return False


def get_logged_in_username(page: Page) -> str | None:
    # 若存在"登录"等提示，明确未登录
    try:
        if _has_login_prompt(page):
            return None
    except Exception:
        pass
    # 优先用 UI 提取用户名
    name = _query_username_from_ui(page)
    if name:
        return name
    # 用户名拿不到则认为未登录
    return None


def is_logged_in_xhs(page: Page) -> bool:
    return get_logged_in_username(page) is not None


def ensure_login_xhs(page: Page, timeout_sec: int = 300, on_logged_in=None) -> bool:
    """旧接口：保留兼容。推荐使用 login_flow_xhs(bm) 或 ensure_login_xhs_with_save(bm)。"""
    open_home_xhs(page)
    if is_logged_in_xhs(page):
        logger.info("XHS: 检测到已登录。")
        if on_logged_in:
            try:
                on_logged_in()
            except Exception:
                pass
        return True
    logger.info("XHS: 未检测到登录状态，请在打开的页面完成登录（扫码/密码），最多等待{}秒…", timeout_sec)
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    while time.time() < deadline:
        if _has_login_prompt(page):
            pass
        elif _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("XHS: 登录成功。")
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
    logger.warning("XHS: 登录等待超时；请确认是否已登录。")
    return False


def ensure_login_xhs_with_save(bm: BrowserManager, timeout_sec: int = 300) -> bool:
    """确保小红书登录并自动保存Cookie状态"""
    page = bm.page
    assert page is not None

    open_home_xhs(page)
    if is_logged_in_xhs(page):
        logger.info("XHS: 检测到已登录。")
        bm.save_storage()  # 保存当前登录状态
        return True

    logger.info("XHS: 未检测到登录状态，请在打开的页面完成登录（扫码/密码），最多等待{}秒…", timeout_sec)
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0

    while time.time() < deadline:
        if _has_login_prompt(page):
            pass
        elif _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("XHS: 登录成功。保存会话…")
            bm.save_storage()  # 登录成功后保存状态
            return True
        if time.time() - last_log > 10:
            logger.info("等待登录中…（检测到未登录界面）")
            last_log = time.time()
        time.sleep(1.2)

    logger.warning("XHS: 登录等待超时；请确认是否已登录。")
    return False


def login_flow_xhs(bm: BrowserManager, timeout_sec: int = 300) -> None:
    """打开小红书首页并等待登录成功；登录成功后保存 storage_state。"""
    page = bm.page
    assert page is not None
    logger.info("打开 XHS 首页: {}", XHS_LOGIN_URL)
    page.goto(XHS_LOGIN_URL)

    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    while time.time() < deadline:
        cur = page.url or ""
        # 1) 登录页上若看到 登录 提示，则继续等待
        if _has_login_prompt(page):
            pass
        # 2) 检测到已登录元素/授权 Cookie，即视为成功
        elif _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("XHS: 登录成功，当前URL={}。保存会话…", cur)
            bm.save_storage()
            return
        if time.time() - last_log > 10:
            logger.info("等待登录中… 当前URL={}", cur)
            last_log = time.time()
        time.sleep(1.0)
    raise TimeoutError("XHS 登录等待超时")


def xhs_probe_login_and_comment(bm: BrowserManager, dry_run: bool = True) -> str:
    """开启 Playwright Trace，检查"登录→评论框打开→（可选）提交"流程。
    返回 trace 文件路径。
    """
    traces_dir = os.path.join("traces")
    os.makedirs(traces_dir, exist_ok=True)
    trace_path = os.path.join(traces_dir, "xhs_login_comment_trace.zip")
    if bm.context:
        try:
            bm.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        except Exception:
            pass
    page = bm.page
    assert page is not None
    # 执行登录流
    login_flow_xhs(bm, timeout_sec=180)
    # 尝试打开评论框再关闭（不真正发送）
    try:
        # 常见评论按钮
        cbtn = page.get_by_role("button", name="评论").first
        if cbtn and cbtn.count() > 0:
            cbtn.click()
            time.sleep(0.3)
        # 找到文本框
        box = None
        for sel in ["textarea", "input[type='text']", "[role='textbox']", "div[contenteditable='true']"]:
            try:
                loc = page.locator(sel).first
                if loc and loc.count() > 0 and loc.is_visible():
                    box = loc
                    break
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
    logger.info("XHS Trace 已保存：{}", trace_path)
    return trace_path
