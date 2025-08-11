from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .browser import BrowserManager
import time, os, re

ZHIHU_HOME = "https://www.zhihu.com"
ZHIHU_LOGIN_URL = "https://www.zhihu.com/signin"


# 登录提示/按钮的检测（出现则判定为未登录）
_LOGIN_PROMPT_SELECTORS = [
    "text=登录",
    "text=注册",
    "button:has-text('登录')",
    "button:has-text('注册')",
    "a:has-text('登录')",
    "text=扫码登录",
    "text=手机登录",
    "text=立即登录",
    "text=登录知乎",
    ".SignFlow-tab",
    ".Login-content",
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
    # 如果仍在登录页面，视为未登录
    try:
        if "signin" in (page.url or "") or "login" in (page.url or ""):
            return True
    except Exception:
        pass
    return False


def _has_auth_cookie(page: Page) -> bool:
    try:
        cookies = page.context.cookies([ZHIHU_HOME])
        names = {c.get("name") for c in cookies}
        return "z_c0" in names or "q_c1" in names or "d_c0" in names
    except Exception:
        return False


def _query_username_from_ui(page: Page) -> str | None:
    """从页面元素优先提取用户名"""
    try:
        # 1) 尝试从用户头像或用户名元素提取
        name = page.evaluate(
            """
            () => {
              // 查找用户头像或用户名相关元素
              const selectors = [
                '.AppHeader-userInfo .Popover-target img',
                '.AppHeader-userInfo .Button-label',
                '.TopstoryItem-avatar img',
                '[data-tooltip*="个人主页"]',
                '.Avatar img'
              ];
              
              for (const sel of selectors) {
                const elem = document.querySelector(sel);
                if (elem) {
                  const alt = elem.getAttribute('alt');
                  const title = elem.getAttribute('title');
                  const text = elem.innerText || elem.textContent;
                  const name = alt || title || text;
                  if (name && name.length > 0 && name.length <= 32) {
                    return name.trim();
                  }
                }
              }
              
              // 尝试从全局变量获取
              const zhihu = window.zhihu || {};
              const user = zhihu.user || {};
              return user.name || user.nickname || null;
            }
            """
        )
        if name and isinstance(name, str) and 1 < len(name) <= 32:
            return name.strip()
    except Exception:
        pass
    
    # 2) 通过可见元素上的 title/aria-label 猜测
    for sel in [
        "[aria-label*='个人主页']", 
        "[title*='个人主页']", 
        ".AppHeader-userInfo",
        ".Avatar"
    ]:
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
    for sel in [
        ".AppHeader-userInfo", 
        ".QuestionHeader-side button:has-text('写回答')",
        ".AnswerForm",
        "[aria-label*='个人主页']",
        ".Avatar"
    ]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return True
        except Exception:
            continue
    return False


def get_logged_in_username(page: Page) -> str | None:
    # 若存在"登录"等提示，或仍在登录页面，明确未登录
    try:
        if _has_login_prompt(page):
            return None
        if "signin" in (page.url or "") or "login" in (page.url or ""):
            return None
    except Exception:
        pass
    # 优先用 UI 提取用户名
    name = _query_username_from_ui(page)
    if name:
        return name
    # 用户名拿不到则认为未登录
    return None


def is_logged_in_zhihu(page: Page) -> bool:
    return get_logged_in_username(page) is not None


def ensure_login_zhihu(page: Page, timeout_sec: int = 300, on_logged_in=None) -> bool:
    """确保知乎登录（旧接口，推荐使用 login_flow_zhihu(bm)）"""
    page.goto(ZHIHU_HOME)
    page.wait_for_load_state("domcontentloaded")

    if is_logged_in_zhihu(page):
        logger.info("Zhihu: 检测到已登录。")
        if on_logged_in:
            try:
                on_logged_in()
            except Exception:
                pass
        return True

    logger.info("Zhihu: 未检测到登录状态，请在打开的页面完成登录（扫码/密码），最多等待{}秒…", timeout_sec)
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0

    while time.time() < deadline:
        if _has_login_prompt(page):
            pass
        elif _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("Zhihu: 登录成功。")
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

    logger.warning("Zhihu: 登录等待超时；请确认是否已登录。")
    return False


def ensure_login_zhihu_with_save(bm: BrowserManager, timeout_sec: int = 300) -> bool:
    """确保知乎登录并自动保存Cookie状态"""
    page = bm.page
    assert page is not None

    page.goto(ZHIHU_HOME)
    page.wait_for_load_state("domcontentloaded")

    if is_logged_in_zhihu(page):
        logger.info("Zhihu: 检测到已登录。")
        bm.save_storage()  # 保存当前登录状态
        return True

    logger.info("Zhihu: 未检测到登录状态，请在打开的页面完成登录（扫码/密码），最多等待{}秒…", timeout_sec)
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0

    while time.time() < deadline:
        if _has_login_prompt(page):
            pass
        elif _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("Zhihu: 登录成功。保存会话…")
            bm.save_storage()  # 登录成功后保存状态
            return True
        if time.time() - last_log > 10:
            logger.info("等待登录中…（检测到未登录界面）")
            last_log = time.time()
        time.sleep(1.2)

    logger.warning("Zhihu: 登录等待超时；请确认是否已登录。")
    return False


def login_flow_zhihu(bm: BrowserManager, timeout_sec: int = 300) -> None:
    """打开知乎登录页并等待登录成功"""
    page = bm.page
    assert page is not None
    logger.info("打开 Zhihu 登录页: {}", ZHIHU_LOGIN_URL)
    page.goto(ZHIHU_LOGIN_URL)

    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    while time.time() < deadline:
        cur = page.url or ""
        # 1) 登录页上若看到登录提示，则继续等待
        if _has_login_prompt(page):
            pass
        # 2) 已跳转到主页或检测到已登录元素/授权 Cookie，即视为成功
        if ("zhihu.com" in cur and "signin" not in cur and "login" not in cur) or _has_logged_in_ui(page) or _has_auth_cookie(page):
            logger.info("Zhihu: 登录成功，当前URL={}。保存会话…", cur)
            bm.save_storage()
            return
        if time.time() - last_log > 10:
            logger.info("等待登录中… 当前URL={}", cur)
            last_log = time.time()
        time.sleep(1.0)
    raise TimeoutError("Zhihu 登录等待超时")


# 兼容性函数，用于测试
def login(bm: BrowserManager, timeout_sec: int = 300) -> bool:
    """兼容性登录函数"""
    try:
        login_flow_zhihu(bm, timeout_sec)
        return True
    except Exception:
        return False


def check_login_status(page) -> bool:
    """兼容性登录状态检查函数"""
    return is_logged_in_zhihu(page)
