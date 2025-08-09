from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .comments import random_comment
import time, re, random

XHS_HOME = "https://www.xiaohongshu.com/explore"

# 卡片选择器候选
CARD_CANDIDATES = [
    "article",
    "[data-testid='note-card']",
    "[class*='note-item']",
    "[class*='feed-item']",
    "[class*='card']",
    "div:has(img)",
    "div:has(a[href*='/explore/'])",
    "section",
    "div:has(button)",
]


def open_home_xhs(page: Page):
    page.goto(XHS_HOME)
    page.wait_for_load_state("domcontentloaded")
    try:
        # Feed 容器存在多样性，这里仅等待主区域加载完成
        page.wait_for_selector("body", timeout=20000)
    except Exception:
        logger.warning("XHS: body not ready in 20s; continue anyway.")


def _has_login_prompt(page: Page) -> bool:
    try:
        # 常见登录提示/按钮
        for sel in [
            "text=登录", "button:has-text('登录')", "text=注册", "text=扫码登录", "text=手机登录",
        ]:
            loc = page.locator(sel).first
            if loc and loc.count() > 0 and loc.is_visible():
                return True
    except Exception:
        pass
    try:
        return "passport" in (page.url or "")
    except Exception:
        return False


def ensure_login_xhs(page: Page, timeout_sec: int = 180) -> bool:
    open_home_xhs(page)
    if not _has_login_prompt(page):
        logger.info("XHS: 检测到可能已登录。")
        return True
    logger.info("XHS: 未登录，请在打开的页面完成登录，最多等待{}秒…", timeout_sec)
    deadline = time.time() + max(5, int(timeout_sec))
    last_log = 0
    while time.time() < deadline:
        if not _has_login_prompt(page):
            logger.info("XHS: 登录成功。")
            return True
        if time.time() - last_log > 10:
            logger.info("等待登录中… 当前URL={}", page.url)
            last_log = time.time()
        time.sleep(1.2)
    logger.warning("XHS: 登录等待超时；请确认是否已登录。")
    return False


def list_visible_cards(page: Page, limit: int = 20):
    """获取可见的卡片列表"""
    cards = []
    for sel in CARD_CANDIDATES:
        try:
            loc = page.locator(sel)
            cnt = min(loc.count(), limit)
            for i in range(cnt):
                card = loc.nth(i)
                if card.is_visible():
                    cards.append(card)
                    if len(cards) >= limit:
                        break
            if cards:
                break
        except Exception:
            continue
    logger.info("XHS: 找到可见卡片数 {}", len(cards))
    return cards


def pick_random_card(page: Page, limit: int = 20):
    """随机选择一个卡片"""
    cards = list_visible_cards(page, limit=limit)
    if not cards:
        return None
    random.shuffle(cards)
    return cards[0]


def _first_card(page: Page):
    """获取第一个可见卡片（保持向后兼容）"""
    cards = list_visible_cards(page, limit=1)
    return cards[0] if cards else None


def extract_card_content(card) -> dict:
    """提取卡片内容信息"""
    content = {
        "title": "",
        "text": "",
        "author": "",
        "tags": [],
        "images": [],
        "url": ""
    }

    try:
        # 提取标题
        for title_sel in ["h1", "h2", "h3", "[class*='title']", "[class*='content']"]:
            try:
                title_elem = card.locator(title_sel).first
                if title_elem and title_elem.count() > 0:
                    title = title_elem.inner_text().strip()
                    if title and len(title) > 3:
                        content["title"] = title[:100]  # 限制长度
                        break
            except Exception:
                continue

        # 提取文本内容
        try:
            text = card.inner_text().strip()
            if text:
                content["text"] = text[:500]  # 限制长度
        except Exception:
            pass

        # 提取作者信息
        for author_sel in ["[class*='author']", "[class*='user']", "[class*='name']"]:
            try:
                author_elem = card.locator(author_sel).first
                if author_elem and author_elem.count() > 0:
                    author = author_elem.inner_text().strip()
                    if author and len(author) <= 50:
                        content["author"] = author
                        break
            except Exception:
                continue

        # 提取链接
        for link_sel in ["a[href*='/explore/']", "a[href*='/discovery/']", "a[href^='/']"]:
            try:
                link_elem = card.locator(link_sel).first
                if link_elem and link_elem.count() > 0:
                    href = link_elem.get_attribute("href")
                    if href:
                        content["url"] = href
                        break
            except Exception:
                continue

    except Exception as e:
        logger.warning("XHS: 提取卡片内容失败: {}", str(e))

    return content


def act_once_on_first_card(page: Page, do_comment: bool, do_like: bool, do_share: bool) -> bool:
    # 打开首页并获取第一条卡片
    open_home_xhs(page)
    card = _first_card(page)
    if not card:
        logger.warning("XHS: 未找到首条卡片")
        return False
    try:
        card.scroll_into_view_if_needed()
    except Exception:
        pass

    # 进入详情页（评论输入通常在详情页才可用）
    logger.info("XHS: 尝试进入详情页...")
    opened = False
    # 尝试多种方式点击进入详情页
    for link_sel in [
        "a[href*='/explore/']",
        "a[href*='/discovery/']",
        "a[href^='/']",
        "a",  # 任何链接
    ]:
        try:
            link = card.locator(link_sel).first
            if link and link.count() > 0:
                logger.info("XHS: 通过链接进入详情页: {}", link_sel)
                link.click(timeout=30000); opened = True; break
        except Exception as e:
            logger.warning("XHS: 点击链接失败 {}: {}", link_sel, str(e))
            continue

    # 如果没有找到链接，尝试点击图片或其他可点击元素
    if not opened:
        for click_sel in ["img", "picture", "[class*='cover']", "[class*='image']"]:
            try:
                elem = card.locator(click_sel).first
                if elem and elem.count() > 0:
                    logger.info("XHS: 点击元素进入详情页: {}", click_sel)
                    elem.click(timeout=30000); opened = True; break
            except Exception as e:
                logger.warning("XHS: 点击元素失败 {}: {}", click_sel, str(e))
                continue

    # 最后尝试直接点击卡片
    if not opened:
        try:
            logger.info("XHS: 直接点击卡片进入详情页")
            card.click(timeout=30000); opened = True
        except Exception as e:
            logger.warning("XHS: 无法点击卡片: {}", str(e))

    if not opened:
        logger.warning("XHS: 未能进入详情页")
        return False

    # 等待详情页加载
    logger.info("XHS: 等待详情页加载...")
    time.sleep(1.5)  # 给页面一些时间跳转

    # 检查是否成功进入详情页（URL应该包含具体的笔记ID）
    current_url = page.url
    logger.info("XHS: 当前URL: {}", current_url)

    # 如果还在首页，尝试更直接的方式进入详情页
    if "/explore" == current_url.split('?')[0].rstrip('/').split('/')[-1]:
        logger.warning("XHS: 似乎仍在首页，尝试其他方式进入详情页")
        # 尝试寻找并点击笔记标题或图片
        for detail_sel in [
            "img", "picture", "[class*='cover']", "[class*='image']",
            "h1", "h2", "h3", "[class*='title']", "[class*='content']",
        ]:
            try:
                detail_elem = card.locator(detail_sel).first
                if detail_elem and detail_elem.count() > 0:
                    logger.info("XHS: 尝试点击元素进入详情页: {}", detail_sel)
                    detail_elem.click()
                    time.sleep(2.0)
                    if page.url != current_url:
                        logger.info("XHS: 成功进入详情页: {}", page.url)
                        break
            except Exception:
                continue

    try:
        page.wait_for_load_state("domcontentloaded")
        logger.info("XHS: 详情页DOM已加载")
    except Exception:
        logger.warning("XHS: 详情页DOM加载超时")

    # 在详情页寻找评论区
    if do_comment or do_share:
        logger.info("XHS: 在详情页寻找评论区...")
        # 等待页面稳定
        time.sleep(1.5)

        # 先尝试滚动查看页面结构
        try:
            page.evaluate("window.scrollTo(0, 0)"); time.sleep(0.3)  # 先到顶部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)"); time.sleep(0.3)  # 中间
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(0.3)  # 底部
        except Exception:
            pass

        # 寻找评论按钮或评论区入口
        comment_btn = None
        for bsel in [
            "button:has-text('评论')",
            "[role=button][aria-label*='评论']",
            "[data-testid*='comment']",
            "svg[aria-label*='评论']",
            "text=评论",
            # 小红书特有的评论统计按钮
            "span:has-text('评论')",
            "div:has-text('评论')",
            "[class*='comment']",
        ]:
            try:
                loc = page.locator(bsel).first
                if loc and loc.count() > 0 and loc.is_visible():
                    logger.info("XHS: 找到评论按钮: {}", bsel)
                    comment_btn = loc; break
            except Exception:
                continue

        # 点击评论按钮
        if comment_btn:
            try:
                comment_btn.click();
                logger.info("XHS: 已点击评论按钮")
                time.sleep(0.5)
            except Exception:
                logger.warning("XHS: 点击评论按钮失败")
        else:
            logger.info("XHS: 未找到明显的评论按钮，尝试直接寻找评论输入框")
        # 进一步确保切到“评论”面板/标签
        for tab_sel in [
            "[role='tab']:has-text('评论')",
            "li:has-text('评论')",
            "a:has-text('评论')",
            "button:has-text('评论')",
            r"text=/评论\s*\d+/",
        ]:
            try:
                t = page.locator(tab_sel).first
                if t and t.count() > 0 and t.is_visible():
                    t.click(); time.sleep(0.2)
                    break
            except Exception:
                continue

    # 寻找评论输入框
    box = None
    if do_comment or do_share:
        logger.info("XHS: 寻找评论输入框...")

        # 第一轮：寻找常见的评论输入框
        for sel in [
            # 最常见的输入框类型
            "textarea",
            "input[type='text']",
            "[role='textbox']",
            "div[contenteditable='true']",
            # 带评论相关属性的
            "textarea[placeholder*='评论']",
            "input[placeholder*='评论']",
            "div[contenteditable='true'][data-placeholder*='评论']",
            "div[contenteditable='plaintext-only']",
            # 语义化属性
            "[aria-label*='评论']",
            "[data-testid*='comment-input']",
            "[data-testid*='comment']",
            # 占位符文本
            "[placeholder*='写评论']",
            "[placeholder*='友善']",
            "[placeholder*='发表']",
            "[placeholder*='说点什么']",
            # 容器内的输入框
            "section:has-text('评论') textarea",
            "aside:has-text('评论') textarea",
            "div:has-text('评论') textarea",
            "section:has([contenteditable]) [contenteditable='true']",
            # 小红书可能的特殊选择器
            "[class*='comment'] textarea",
            "[class*='comment'] input",
            "[class*='comment'] [contenteditable]",
        ]:
            try:
                loc = page.locator(sel).first
                if loc and loc.count() > 0 and loc.is_visible():
                    logger.info("XHS: 找到评论输入框: {}", sel)
                    box = loc; break
            except Exception:
                continue
        # 尝试点击“写评论/发表后评论”等提示文本再找一次
        if not box:
            logger.info("XHS: 第一轮未找到输入框，尝试点击提示文本...")
            for tsel in [
                "text=写评论", "text=友善评论", "text=发表后评论", "text=说点什么",
                "text=发表评论", "text=留下点什么", "text=说两句",
                "text=写下你的评论", "text=参与讨论",
                # 可能的占位符div
                "div:has-text('写评论')",
                "div:has-text('说点什么')",
                "span:has-text('写评论')",
            ]:
                try:
                    t = page.locator(tsel).first
                    if t and t.count() > 0 and t.is_visible():
                        logger.info("XHS: 点击提示文本: {}", tsel)
                        t.click(); time.sleep(0.5)
                        break
                except Exception:
                    continue

            # 点击后再次寻找输入框
            for sel in [
                "textarea", "input[type='text']", "[role='textbox']",
                "div[contenteditable='true']", "[contenteditable='true']",
                "input[placeholder*='评论']",
            ]:
                try:
                    loc = page.locator(sel).first
                    if loc and loc.count() > 0 and loc.is_visible():
                        logger.info("XHS: 点击提示文本后找到输入框: {}", sel)
                        box = loc; break
                except Exception:
                    continue

            # 如果还没找到，滚动页面再找一次
            if not box:
                logger.info("XHS: 滚动页面寻找评论输入框...")
                try:
                    page.mouse.wheel(0, 400); time.sleep(0.3)
                    page.mouse.wheel(0, 400); time.sleep(0.3)
                except Exception:
                    pass

                for sel in [
                    "textarea", "[role='textbox']", "div[contenteditable='true']",
                    "input[placeholder*='评论']", "[contenteditable='true']",
                ]:
                    try:
                        loc = page.locator(sel).first
                        if loc and loc.count() > 0 and loc.is_visible():
                            logger.info("XHS: 滚动后找到输入框: {}", sel)
                            box = loc; break
                    except Exception:
                        continue
        if not box:
            logger.warning("XHS: 未找到评论输入框；跳过评论，仅执行点赞/分享（如配置）")
        else:
            text = random_comment("")
            try:
                box.click(); box.type(text, delay=25)
            except Exception:
                try:
                    box.fill(text)
                except Exception:
                    pass
            logger.info("XHS: 已输入评论: {}", text)

    # 点赞（在提交前）
    if do_like:
        for lsel in [
            "button:has-text('赞')",
            "button:has-text('喜欢')",
            "[aria-label*='赞']",
            "[data-testid*='like']",
        ]:
            try:
                loc = page.locator(lsel).first
                if loc and loc.count() > 0:
                    loc.click(); logger.info("XHS: 已点赞（提交前）"); break
            except Exception:
                continue

    # 分享/转发（如果有对应入口）
    if do_share:
        for ssel in [
            "button:has-text('转发')",
            "button:has-text('分享')",
            "[aria-label*='分享']",
            "[data-testid*='share']",
        ]:
            try:
                loc = page.locator(ssel).first
                if loc and loc.count() > 0:
                    loc.click(); logger.info("XHS: 已点击分享/转发"); break
            except Exception:
                continue

    # 提交评论
    if do_comment or do_share:
        try:
            if 'box' in locals() and box:
                try:
                    box.press("Control+Enter")
                except Exception:
                    box.press("Enter")
                logger.info("XHS: 评论/分享已提交")
            else:
                logger.info("XHS: 无评论输入框，已跳过提交")
        except Exception:
            logger.warning("XHS: 提交评论失败，已忽略")
    return True


def like_post(page: Page) -> bool:
    """点赞当前页面的笔记 - 优化版本"""
    logger.info("XHS: 尝试点赞...")

    # 小红书详情页点赞按钮通常在右侧固定位置或底部操作栏
    # 优先级：右侧固定按钮 > 底部操作栏 > 通用选择器
    like_selectors = [
        # 小红书特定的点赞按钮选择器（右侧固定位置）
        "[class*='interaction'] [class*='like']:not([class*='active'])",
        "[class*='sidebar'] [class*='like']:not([class*='active'])",
        "[class*='right-side'] [class*='like']:not([class*='active'])",

        # 底部操作栏的点赞按钮
        "[class*='bottom-bar'] [class*='like']:not([class*='active'])",
        "[class*='action-bar'] [class*='like']:not([class*='active'])",
        "[class*='toolbar'] [class*='like']:not([class*='active'])",

        # 通用点赞按钮选择器
        "button:has-text('赞')",
        "button:has-text('点赞')",
        "[aria-label*='赞']",
        "[aria-label*='点赞']",
        "[data-testid*='like']",
        "svg[aria-label*='赞']",

        # 更具体的小红书点赞按钮
        ".like-wrapper:not(.liked)",
        ".like-btn:not(.active)",
        "[class*='like']:not([class*='liked']):not([class*='active'])",
    ]

    for like_sel in like_selectors:
        try:
            loc = page.locator(like_sel).first
            if loc and loc.count() > 0:
                # 检查元素是否可见
                if loc.is_visible():
                    # 检查是否已经点赞（避免重复点赞）
                    class_name = loc.get_attribute("class") or ""
                    if any(keyword in class_name.lower() for keyword in ["liked", "active", "selected"]):
                        logger.info("XHS: 已经点过赞了")
                        return True

                    # 尝试点击点赞按钮
                    try:
                        # 先滚动到元素位置
                        loc.scroll_into_view_if_needed()
                        time.sleep(0.3)

                        # 点击点赞按钮
                        loc.click(timeout=5000)
                        logger.info("XHS: 点赞成功 - 使用选择器: {}", like_sel)
                        time.sleep(0.8)  # 等待动画完成
                        return True

                    except Exception as click_error:
                        # 如果普通点击失败，尝试强制点击
                        try:
                            loc.click(force=True)
                            logger.info("XHS: 强制点赞成功 - 使用选择器: {}", like_sel)
                            time.sleep(0.8)
                            return True
                        except Exception:
                            logger.debug("XHS: 点赞失败 {}: {}", like_sel, str(click_error))
                            continue

        except Exception as e:
            logger.debug("XHS: 点赞选择器失败 {}: {}", like_sel, str(e))
            continue

    logger.warning("XHS: 未找到可用的点赞按钮")
    return False


def collect_post(page: Page) -> bool:
    """收藏当前页面的笔记 - 优化版本"""
    logger.info("XHS: 尝试收藏...")

    # 小红书收藏按钮通常在右侧固定位置或底部操作栏
    collect_selectors = [
        # 小红书特定的收藏按钮选择器（右侧固定位置）
        "[class*='interaction'] [class*='collect']:not([class*='active'])",
        "[class*='sidebar'] [class*='collect']:not([class*='active'])",
        "[class*='right-side'] [class*='collect']:not([class*='active'])",
        "[class*='interaction'] [class*='favorite']:not([class*='active'])",

        # 底部操作栏的收藏按钮
        "[class*='bottom-bar'] [class*='collect']:not([class*='active'])",
        "[class*='action-bar'] [class*='collect']:not([class*='active'])",
        "[class*='toolbar'] [class*='collect']:not([class*='active'])",

        # 通用收藏按钮选择器
        "button:has-text('收藏')",
        "button:has-text('收藏夹')",
        "button:has-text('保存')",
        "[aria-label*='收藏']",
        "[aria-label*='保存']",
        "[data-testid*='collect']",
        "[data-testid*='favorite']",
        "[data-testid*='save']",
        "svg[aria-label*='收藏']",

        # 更具体的收藏按钮
        ".collect-wrapper:not(.collected)",
        ".collect-btn:not(.active)",
        ".favorite-btn:not(.active)",
        "[class*='collect']:not([class*='collected']):not([class*='active'])",
        "[class*='favorite']:not([class*='favorited']):not([class*='active'])",
    ]

    for collect_sel in collect_selectors:
        try:
            loc = page.locator(collect_sel).first
            if loc and loc.count() > 0:
                # 检查元素是否可见
                if loc.is_visible():
                    # 检查是否已经收藏（避免重复收藏）
                    class_name = loc.get_attribute("class") or ""
                    if any(keyword in class_name.lower() for keyword in ["collected", "favorited", "active", "selected"]):
                        logger.info("XHS: 已经收藏过了")
                        return True

                    # 尝试点击收藏按钮
                    try:
                        # 先滚动到元素位置
                        loc.scroll_into_view_if_needed()
                        time.sleep(0.3)

                        # 点击收藏按钮
                        loc.click(timeout=5000)
                        logger.info("XHS: 收藏成功 - 使用选择器: {}", collect_sel)
                        time.sleep(0.8)  # 等待动画完成
                        return True

                    except Exception as click_error:
                        # 如果普通点击失败，尝试强制点击
                        try:
                            loc.click(force=True)
                            logger.info("XHS: 强制收藏成功 - 使用选择器: {}", collect_sel)
                            time.sleep(0.8)
                            return True
                        except Exception:
                            logger.debug("XHS: 收藏失败 {}: {}", collect_sel, str(click_error))
                            continue

        except Exception as e:
            logger.debug("XHS: 收藏选择器失败 {}: {}", collect_sel, str(e))
            continue

    logger.warning("XHS: 未找到可用的收藏按钮")
    return False


def extract_post_content(page: Page) -> str:
    """提取当前页面的笔记内容，用于AI评论生成"""
    logger.info("XHS: 提取笔记内容...")

    content_parts = []

    # 提取标题
    title_selectors = [
        "[class*='title']",
        "[class*='note-title']",
        "[class*='post-title']",
        "h1", "h2", "h3",
        "[data-testid*='title']",
        ".title",
    ]

    for title_sel in title_selectors:
        try:
            loc = page.locator(title_sel).first
            if loc and loc.count() > 0 and loc.is_visible():
                title_text = loc.inner_text().strip()
                if title_text and len(title_text) > 3:
                    content_parts.append(f"标题: {title_text}")
                    break
        except Exception:
            continue

    # 提取正文内容
    content_selectors = [
        "[class*='content']",
        "[class*='note-content']",
        "[class*='post-content']",
        "[class*='desc']",
        "[class*='description']",
        "[data-testid*='content']",
        ".content",
        ".desc",
        "p",
    ]

    for content_sel in content_selectors:
        try:
            elements = page.locator(content_sel).all()
            for elem in elements[:3]:  # 最多取前3个元素
                if elem.is_visible():
                    text = elem.inner_text().strip()
                    if text and len(text) > 10 and len(text) < 500:  # 过滤太短或太长的文本
                        content_parts.append(text)
        except Exception:
            continue

    # 如果没有找到具体内容，尝试提取页面主要文本
    if not content_parts:
        try:
            # 尝试获取页面主要内容区域的文本
            main_selectors = [
                "main",
                "[role='main']",
                ".main-content",
                ".note-detail",
                ".post-detail",
            ]

            for main_sel in main_selectors:
                try:
                    loc = page.locator(main_sel).first
                    if loc and loc.count() > 0:
                        text = loc.inner_text().strip()
                        if text and len(text) > 20:
                            content_parts.append(text[:300])  # 截取前300字符
                            break
                except Exception:
                    continue
        except Exception:
            pass

    # 合并内容
    if content_parts:
        full_content = " ".join(content_parts)
        # 清理和截断内容
        full_content = full_content.replace("\n", " ").replace("\t", " ")
        full_content = " ".join(full_content.split())  # 去除多余空格
        result = full_content[:200]  # 截取前200字符，适合AI处理
        logger.info("XHS: 提取到内容: {}...", result[:50])
        return result
    else:
        logger.warning("XHS: 未能提取到笔记内容")
        return "小红书笔记"  # 默认内容


def share_post(page: Page) -> bool:
    """分享当前页面的笔记"""
    logger.info("XHS: 尝试分享...")
    for share_sel in [
        "button:has-text('分享')",
        "button:has-text('转发')",
        "[aria-label*='分享']",
        "[data-testid*='share']",
        "svg[aria-label*='分享']",
        "[class*='share']",
    ]:
        try:
            loc = page.locator(share_sel).first
            if loc and loc.count() > 0 and loc.is_visible():
                loc.click()
                logger.info("XHS: 分享按钮点击成功")
                time.sleep(0.5)
                # 可能会弹出分享选项，这里简单关闭
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
                return True
        except Exception as e:
            logger.debug("XHS: 分享尝试失败 {}: {}", share_sel, str(e))
            continue
    logger.warning("XHS: 未找到分享按钮")
    return False


def follow_user(page: Page, user_id: str = None) -> bool:
    """关注用户 - 可以在详情页关注作者，或者访问指定用户主页关注"""
    logger.info("XHS: 尝试关注用户...")

    # 如果提供了用户ID，先访问用户主页
    if user_id:
        try:
            user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
            logger.info("XHS: 访问用户主页: {}", user_url)
            page.goto(user_url, timeout=30000)
            time.sleep(2.0)
        except Exception as e:
            logger.warning("XHS: 访问用户主页失败: {}", str(e))
            return False

    # 查找关注按钮
    follow_selectors = [
        # 小红书特定的关注按钮
        "button:has-text('关注')",
        "button:has-text('+ 关注')",
        "[class*='follow']:not([class*='followed']):not([class*='following'])",
        "[class*='follow-btn']:not([class*='followed'])",

        # 通用关注按钮
        "[aria-label*='关注']",
        "[data-testid*='follow']",
        "button[title*='关注']",

        # 更具体的选择器
        ".follow-button:not(.followed)",
        ".btn-follow:not(.following)",
    ]

    for follow_sel in follow_selectors:
        try:
            loc = page.locator(follow_sel).first
            if loc and loc.count() > 0 and loc.is_visible():
                # 检查是否已经关注
                button_text = loc.inner_text().strip()
                class_name = loc.get_attribute("class") or ""

                if any(keyword in button_text for keyword in ["已关注", "取消关注", "following"]):
                    logger.info("XHS: 已经关注过该用户")
                    return True

                if any(keyword in class_name.lower() for keyword in ["followed", "following"]):
                    logger.info("XHS: 已经关注过该用户")
                    return True

                # 点击关注按钮
                try:
                    loc.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    loc.click(timeout=5000)
                    logger.info("XHS: 关注成功 - 使用选择器: {}", follow_sel)
                    time.sleep(1.0)
                    return True
                except Exception as click_error:
                    logger.debug("XHS: 关注按钮点击失败 {}: {}", follow_sel, str(click_error))
                    continue

        except Exception as e:
            logger.debug("XHS: 关注选择器失败 {}: {}", follow_sel, str(e))
            continue

    logger.warning("XHS: 未找到可用的关注按钮")
    return False


def comment_post(page: Page, comment_text: str = None) -> bool:
    """在当前页面评论笔记 - 优化版本"""
    logger.info("XHS: 尝试评论...")

    # 小红书评论区通常在页面底部，需要先滚动到底部
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.0)  # 等待评论区加载
    except Exception:
        pass

    # 第一步：尝试点击评论按钮激活评论区
    comment_activated = False
    comment_button_selectors = [
        # 小红书特定的评论按钮
        "[class*='interaction'] [class*='comment']",
        "[class*='sidebar'] [class*='comment']",
        "[class*='bottom-bar'] [class*='comment']",
        "[class*='action-bar'] [class*='comment']",

        # 通用评论按钮
        "button:has-text('评论')",
        "span:has-text('评论')",
        "div:has-text('评论')",
        "[aria-label*='评论']",
        "[data-testid*='comment']",
        "text=评论",
    ]

    for comment_btn_sel in comment_button_selectors:
        try:
            btn = page.locator(comment_btn_sel).first
            if btn and btn.count() > 0 and btn.is_visible():
                btn.click(timeout=5000)
                logger.info("XHS: 点击评论按钮成功 - 使用选择器: {}", comment_btn_sel)
                time.sleep(1.0)  # 等待评论输入框出现
                comment_activated = True
                break
        except Exception as e:
            logger.debug("XHS: 评论按钮点击失败 {}: {}", comment_btn_sel, str(e))
            continue

    # 第二步：寻找评论输入框
    comment_input_selectors = [
        # 小红书最新的评论输入框选择器（2024年版本）
        ".comment-input textarea",
        ".comment-input input",
        "[class*='CommentInput'] textarea",
        "[class*='CommentInput'] input",
        "[class*='comment-input'] textarea",
        "[class*='comment-input'] input",

        # 小红书特定的评论输入框
        "[class*='comment'] textarea[placeholder*='评论']",
        "[class*='comment'] input[placeholder*='评论']",
        "[class*='comment-box'] textarea",
        "[class*='comment-box'] input",

        # 通用评论输入框选择器
        "textarea[placeholder*='评论']",
        "input[placeholder*='评论']",
        "textarea[placeholder*='友善']",
        "input[placeholder*='友善']",
        "textarea[placeholder*='写评论']",
        "input[placeholder*='写评论']",
        "textarea[placeholder*='说点什么']",
        "input[placeholder*='说点什么']",
        "textarea[placeholder*='写下']",
        "input[placeholder*='写下']",
        "div[contenteditable='true'][placeholder*='评论']",
        "[aria-label*='评论输入']",
        "[data-testid*='comment-input']",

        # 更通用的输入框（排除搜索框）
        "textarea:not([placeholder*='搜索']):not([placeholder*='search'])",
        "input[type='text']:not([placeholder*='搜索']):not([placeholder*='search'])",
        "[role='textbox']:not([placeholder*='搜索']):not([placeholder*='search'])",
        "div[contenteditable='true']:not([placeholder*='搜索']):not([placeholder*='search'])",

        # 最后的兜底选择器
        "textarea",
        "input[type='text']",
        "[contenteditable='true']",
    ]

    comment_box = None
    for i, sel in enumerate(comment_input_selectors):
        try:
            logger.debug("XHS: [{}] 尝试选择器 {}/{}: {}", time.strftime("%H:%M:%S"), i+1, len(comment_input_selectors), sel)
            loc = page.locator(sel).first
            if loc and loc.count() > 0:
                logger.debug("XHS: [{}] 找到元素，检查可见性...", time.strftime("%H:%M:%S"))
                if loc.is_visible():
                    # 检查是否是搜索框
                    placeholder = loc.get_attribute("placeholder") or ""
                    aria_label = loc.get_attribute("aria-label") or ""
                    tag_name = loc.evaluate("el => el.tagName.toLowerCase()")

                    logger.debug("XHS: [{}] 元素详情 - 标签:{} placeholder:'{}' aria-label:'{}'",
                               time.strftime("%H:%M:%S"), tag_name, placeholder, aria_label)

                    if any(keyword in (placeholder + aria_label).lower() for keyword in ["搜索", "search"]):
                        logger.debug("XHS: [{}] 跳过搜索框", time.strftime("%H:%M:%S"))
                        continue

                    logger.info("XHS: [{}] ✅ 找到评论输入框 - 使用选择器: {}", time.strftime("%H:%M:%S"), sel)
                    comment_box = loc
                    break
                else:
                    logger.debug("XHS: [{}] 元素不可见", time.strftime("%H:%M:%S"))
            else:
                logger.debug("XHS: [{}] 未找到元素或元素数量为0", time.strftime("%H:%M:%S"))
        except Exception as e:
            logger.debug("XHS: [{}] 选择器失败 {}: {}", time.strftime("%H:%M:%S"), sel, str(e))
            continue

    if not comment_box:
        logger.warning("XHS: 未找到评论输入框")
        return False

    # 第三步：输入评论内容
    # 提取笔记内容用于AI评论生成
    if not comment_text:
        try:
            post_content = extract_post_content(page)
            text = random_comment(post_content)  # 传递实际内容给AI
        except Exception as e:
            logger.warning("XHS: 内容提取失败，使用默认评论: {}", str(e))
            text = random_comment("")
    else:
        text = comment_text
    try:
        # 点击输入框获得焦点
        try:
            comment_box.scroll_into_view_if_needed()
            time.sleep(0.3)
            comment_box.click(timeout=5000)
        except Exception:
            comment_box.click(force=True)

        time.sleep(0.5)

        # 清空输入框并输入新内容
        comment_box.fill("")  # 清空
        time.sleep(0.2)
        comment_box.type(text, delay=30)  # 慢速输入，模拟真人
        logger.info("XHS: 已输入评论内容: {}", text)

        time.sleep(0.5)

        # 第四步：提交评论
        submit_success = False

        # 尝试键盘快捷键提交
        for key_combo in ["Control+Enter", "Enter"]:
            try:
                comment_box.press(key_combo)
                logger.info("XHS: 使用快捷键 {} 提交评论", key_combo)
                time.sleep(1.0)
                submit_success = True
                break
            except Exception as e:
                logger.debug("XHS: 快捷键 {} 提交失败: {}", key_combo, str(e))
                continue

        # 如果快捷键失败，尝试找提交按钮
        if not submit_success:
            submit_button_selectors = [
                # 小红书特定的提交按钮
                "[class*='comment'] button:has-text('发布')",
                "[class*='comment'] button:has-text('提交')",
                "[class*='comment'] button:has-text('发送')",
                "[class*='comment-submit']",
                "[class*='submit-btn']",

                # 通用提交按钮
                "button:has-text('发布')",
                "button:has-text('提交')",
                "button:has-text('发送')",
                "button:has-text('确定')",
                "[aria-label*='发布']",
                "[aria-label*='提交']",
                "[data-testid*='submit']",
                "[data-testid*='send']",
            ]

            for submit_sel in submit_button_selectors:
                try:
                    submit_btn = page.locator(submit_sel).first
                    if submit_btn and submit_btn.count() > 0 and submit_btn.is_visible():
                        submit_btn.click(timeout=5000)
                        logger.info("XHS: 点击提交按钮成功 - 使用选择器: {}", submit_sel)
                        time.sleep(1.0)
                        submit_success = True
                        break
                except Exception as e:
                    logger.debug("XHS: 提交按钮点击失败 {}: {}", submit_sel, str(e))
                    continue

        if submit_success:
            logger.info("XHS: 评论提交成功")
            time.sleep(1.5)  # 等待提交完成
            return True
        else:
            logger.warning("XHS: 评论提交失败，未找到有效的提交方式")
            return False

    except Exception as e:
        logger.warning("XHS: 评论过程失败: {}", str(e))
        return False


def xhs_interact_with_post(page: Page, do_comment: bool = True, do_like: bool = True,
                          do_collect: bool = True, do_share: bool = False, do_follow: bool = False,
                          comment_text: str = None) -> dict:
    """与小红书笔记进行完整交互（评论、点赞、收藏、分享）"""
    results = {
        "content": {},
        "comment": False,
        "like": False,
        "collect": False,
        "share": False,
        "follow": False,
        "success": False
    }

    try:
        # 等待页面加载
        time.sleep(2.0)

        # 提取内容信息（如果在详情页）
        try:
            content = {
                "title": "",
                "text": "",
                "url": page.url
            }

            # 提取标题
            for title_sel in ["h1", "h2", "[class*='title']", "[class*='content']"]:
                try:
                    title_elem = page.locator(title_sel).first
                    if title_elem and title_elem.count() > 0:
                        title = title_elem.inner_text().strip()
                        if title and len(title) > 3:
                            content["title"] = title[:100]
                            break
                except Exception:
                    continue

            # 提取页面文本
            try:
                text = page.locator("body").inner_text()
                if text:
                    content["text"] = text[:500]
            except Exception:
                pass

            results["content"] = content
            logger.info("XHS: 提取内容 - 标题: {}", content.get("title", "无标题")[:50])

        except Exception as e:
            logger.warning("XHS: 提取内容失败: {}", str(e))

        # 执行交互操作
        if do_like:
            results["like"] = like_post(page)

        if do_collect:
            results["collect"] = collect_post(page)

        if do_share:
            results["share"] = share_post(page)

        if do_comment:
            results["comment"] = comment_post(page, comment_text)

        if do_follow:
            results["follow"] = follow_user(page)

        # 判断整体成功
        results["success"] = any([
            results["comment"] if do_comment else True,
            results["like"] if do_like else True,
            results["collect"] if do_collect else True,
            results["share"] if do_share else True,
            results["follow"] if do_follow else True,
        ])

        logger.info("XHS: 交互完成 - 评论:{} 点赞:{} 收藏:{} 分享:{} 关注:{}",
                   results["comment"], results["like"], results["collect"], results["share"], results["follow"])

    except Exception as e:
        logger.error("XHS: 交互过程出错: {}", str(e))
        results["success"] = False

    return results

