from __future__ import annotations
from playwright.sync_api import Page
from .logger import logger
from .comments import random_comment
from .config import CONFIG
import time, re, random

ZHIHU_HOME = "https://www.zhihu.com"


def open_home_zhihu(page: Page):
    """打开知乎首页"""
    page.goto(ZHIHU_HOME)
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_selector(".Topstory-container", timeout=20000)
    except Exception:
        logger.warning("Zhihu: .Topstory-container not visible in 20s, continue anyway.")


def list_visible_posts(page: Page, limit: int = 20):
    """获取可见的知乎内容"""
    # 知乎的内容选择器
    selectors = [
        ".TopstoryItem",  # 首页推荐内容
        ".QuestionItem",  # 问题
        ".AnswerItem",    # 回答
        ".ArticleItem",   # 文章
    ]
    
    cards = []
    for selector in selectors:
        try:
            loc = page.locator(selector)
            count = min(loc.count(), limit - len(cards))
            for i in range(count):
                cards.append(loc.nth(i))
            if len(cards) >= limit:
                break
        except Exception:
            continue
    
    logger.info("Zhihu: 可见内容数 {}", len(cards))
    return cards


def pick_random_post(page: Page, limit: int = 20):
    """随机选择一个知乎内容"""
    cards = list_visible_posts(page, limit=limit)
    if not cards:
        return None
    return random.choice(cards)


def extract_post_content(page: Page) -> str:
    """提取当前页面的知乎内容，用于AI评论生成"""
    logger.info("Zhihu: 提取内容...")
    
    content_parts = []
    
    # 提取标题
    title_selectors = [
        ".QuestionHeader-title",
        ".Post-Title", 
        ".ContentItem-title",
        ".AnswerItem-title",
        "h1",
        ".RichText h1",
        "[data-testid='question-title']",
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
        ".RichText",
        ".AnswerItem-content",
        ".QuestionRichText",
        ".Post-RichText", 
        ".ContentItem-content",
        "[data-testid='answer']",
        ".css-1yuhvjn",  # 知乎的内容区域
    ]
    
    for content_sel in content_selectors:
        try:
            elements = page.locator(content_sel).all()
            for elem in elements[:2]:  # 最多取前2个元素
                if elem.is_visible():
                    text = elem.inner_text().strip()
                    if text and len(text) > 20 and len(text) < 800:  # 过滤太短或太长的文本
                        content_parts.append(text)
        except Exception:
            continue
    
    # 合并内容
    if content_parts:
        full_content = " ".join(content_parts)
        # 清理和截断内容
        full_content = full_content.replace("\n", " ").replace("\t", " ")
        full_content = " ".join(full_content.split())  # 去除多余空格
        result = full_content[:300]  # 截取前300字符，适合AI处理
        logger.info("Zhihu: 提取到内容: {}...", result[:50])
        return result
    else:
        logger.warning("Zhihu: 未能提取到内容")
        return "知乎内容"  # 默认内容


def like_post(page: Page) -> bool:
    """点赞当前页面的知乎内容"""
    logger.info("Zhihu: 尝试点赞...")

    like_selectors = [
        # 知乎特定的点赞按钮选择器
        "button[aria-label*='赞同']",
        "button[aria-label*='点赞']", 
        ".VoteButton--up",
        ".Button.VoteButton.VoteButton--up",
        "[data-testid='vote-up']",
        "button:has-text('赞同')",
        "button:has-text('点赞')",
        
        # 通用点赞按钮
        "[aria-label*='赞']",
        "[data-testid*='like']",
        "button[title*='赞']",
        ".like-button",
        ".vote-up",
    ]

    for like_sel in like_selectors:
        try:
            loc = page.locator(like_sel).first
            if loc and loc.count() > 0:
                # 检查元素是否可见
                if loc.is_visible():
                    # 检查是否已经点赞
                    class_name = loc.get_attribute("class") or ""
                    aria_pressed = loc.get_attribute("aria-pressed") or ""
                    
                    if "is-pressed" in class_name or aria_pressed == "true":
                        logger.info("Zhihu: 已经点过赞了")
                        return True
                    
                    # 尝试点击点赞按钮
                    try:
                        loc.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        loc.click(timeout=5000)
                        logger.info("Zhihu: 点赞成功 - 使用选择器: {}", like_sel)
                        time.sleep(0.8)
                        return True
                        
                    except Exception as click_error:
                        try:
                            loc.click(force=True)
                            logger.info("Zhihu: 强制点赞成功 - 使用选择器: {}", like_sel)
                            time.sleep(0.8)
                            return True
                        except Exception:
                            logger.debug("Zhihu: 点赞失败 {}: {}", like_sel, str(click_error))
                            continue
                            
        except Exception as e:
            logger.debug("Zhihu: 点赞选择器失败 {}: {}", like_sel, str(e))
            continue
    
    logger.warning("Zhihu: 未找到可用的点赞按钮")
    return False


def collect_post(page: Page) -> bool:
    """收藏当前页面的知乎内容"""
    logger.info("Zhihu: 尝试收藏...")
    
    collect_selectors = [
        # 知乎特定的收藏按钮选择器
        "button[aria-label*='收藏']",
        "button[aria-label*='收藏夹']",
        ".Button.FavButton",
        "[data-testid='collect']",
        "[data-testid='favorite']",
        "button:has-text('收藏')",
        "button:has-text('收藏夹')",
        
        # 通用收藏按钮
        "[aria-label*='收藏']",
        "[data-testid*='collect']",
        "[data-testid*='favorite']",
        "button[title*='收藏']",
        ".collect-button",
        ".favorite-button",
    ]
    
    for collect_sel in collect_selectors:
        try:
            loc = page.locator(collect_sel).first
            if loc and loc.count() > 0:
                if loc.is_visible():
                    # 检查是否已经收藏
                    class_name = loc.get_attribute("class") or ""
                    aria_pressed = loc.get_attribute("aria-pressed") or ""
                    
                    if "is-pressed" in class_name or aria_pressed == "true":
                        logger.info("Zhihu: 已经收藏过了")
                        return True
                    
                    try:
                        loc.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        loc.click(timeout=5000)
                        logger.info("Zhihu: 收藏成功 - 使用选择器: {}", collect_sel)
                        time.sleep(0.8)
                        
                        # 知乎收藏可能会弹出收藏夹选择，尝试选择第一个
                        try:
                            first_collection = page.locator(".FavoritesSelector-item").first
                            if first_collection and first_collection.count() > 0:
                                first_collection.click(timeout=3000)
                                logger.info("Zhihu: 已选择收藏夹")
                        except Exception:
                            pass
                        
                        return True
                        
                    except Exception as click_error:
                        try:
                            loc.click(force=True)
                            logger.info("Zhihu: 强制收藏成功 - 使用选择器: {}", collect_sel)
                            time.sleep(0.8)
                            return True
                        except Exception:
                            logger.debug("Zhihu: 收藏失败 {}: {}", collect_sel, str(click_error))
                            continue
                            
        except Exception as e:
            logger.debug("Zhihu: 收藏选择器失败 {}: {}", collect_sel, str(e))
            continue
    
    logger.warning("Zhihu: 未找到可用的收藏按钮")
    return False


def comment_post(page: Page, comment_text: str = None) -> bool:
    """在当前页面评论知乎内容"""
    logger.info("Zhihu: 尝试评论...")

    # 第一步：尝试点击评论按钮激活评论区
    comment_activated = False
    comment_button_selectors = [
        # 知乎特定的评论按钮
        "button[aria-label*='评论']",
        "button:has-text('评论')",
        "button:has-text('添加评论')",
        ".Button.CommentButton",
        "[data-testid='comment']",
        ".ContentItem-action button:has-text('评论')",

        # 通用评论按钮
        "span:has-text('评论')",
        "div:has-text('评论')",
        "[aria-label*='评论']",
        "text=评论",
    ]

    for comment_btn_sel in comment_button_selectors:
        try:
            btn = page.locator(comment_btn_sel).first
            if btn and btn.count() > 0 and btn.is_visible():
                btn.click(timeout=5000)
                logger.info("Zhihu: 点击评论按钮成功 - 使用选择器: {}", comment_btn_sel)
                time.sleep(1.0)
                comment_activated = True
                break
        except Exception as e:
            logger.debug("Zhihu: 评论按钮点击失败 {}: {}", comment_btn_sel, str(e))
            continue

    # 第二步：寻找评论输入框
    comment_input_selectors = [
        # 知乎特定的评论输入框
        ".CommentEditor textarea",
        ".CommentEditor-input",
        ".Input.CommentEditor-input",
        "[placeholder*='写下你的评论']",
        "[placeholder*='添加评论']",
        "[placeholder*='说点什么']",
        "[data-testid='comment-input']",

        # 通用评论输入框选择器
        "textarea[placeholder*='评论']",
        "input[placeholder*='评论']",
        "textarea[placeholder*='写下']",
        "input[placeholder*='写下']",
        "[role='textbox']:not([placeholder*='搜索']):not([placeholder*='search'])",
        "textarea:not([placeholder*='搜索']):not([placeholder*='search'])",
    ]

    comment_box = None
    for sel in comment_input_selectors:
        try:
            loc = page.locator(sel).first
            if loc and loc.count() > 0 and loc.is_visible():
                # 检查是否是搜索框
                placeholder = loc.get_attribute("placeholder") or ""
                aria_label = loc.get_attribute("aria-label") or ""
                if any(keyword in (placeholder + aria_label).lower() for keyword in ["搜索", "search"]):
                    continue

                logger.info("Zhihu: 找到评论输入框 - 使用选择器: {}", sel)
                comment_box = loc
                break
        except Exception as e:
            logger.debug("Zhihu: 评论输入框查找失败 {}: {}", sel, str(e))
            continue

    if not comment_box:
        logger.warning("Zhihu: 未找到评论输入框")
        return False

    # 第三步：输入评论内容
    # 提取内容用于AI评论生成
    if not comment_text:
        try:
            post_content = extract_post_content(page)
            text = random_comment(post_content)  # 传递实际内容给AI
        except Exception as e:
            logger.warning("Zhihu: 内容提取失败，使用默认评论: {}", str(e))
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
        logger.info("Zhihu: 已输入评论内容: {}", text)

        time.sleep(0.5)

        # 第四步：提交评论
        submit_success = False

        # 尝试键盘快捷键提交
        for key_combo in ["Control+Enter", "Enter"]:
            try:
                comment_box.press(key_combo)
                logger.info("Zhihu: 使用快捷键 {} 提交评论", key_combo)
                time.sleep(1.0)
                submit_success = True
                break
            except Exception as e:
                logger.debug("Zhihu: 快捷键 {} 提交失败: {}", key_combo, str(e))
                continue

        # 如果快捷键失败，尝试找提交按钮
        if not submit_success:
            submit_button_selectors = [
                # 知乎特定的提交按钮
                ".CommentEditor button:has-text('发布')",
                ".CommentEditor button:has-text('提交')",
                ".CommentEditor button:has-text('评论')",
                ".Button.Button--primary:has-text('发布')",
                "[data-testid='submit-comment']",

                # 通用提交按钮
                "button:has-text('发布')",
                "button:has-text('提交')",
                "button:has-text('发送')",
                "button:has-text('确定')",
                "[aria-label*='发布']",
                "[aria-label*='提交']",
                "[data-testid*='submit']",
            ]

            for submit_sel in submit_button_selectors:
                try:
                    submit_btn = page.locator(submit_sel).first
                    if submit_btn and submit_btn.count() > 0 and submit_btn.is_visible():
                        submit_btn.click(timeout=5000)
                        logger.info("Zhihu: 点击提交按钮成功 - 使用选择器: {}", submit_sel)
                        time.sleep(1.0)
                        submit_success = True
                        break
                except Exception as e:
                    logger.debug("Zhihu: 提交按钮点击失败 {}: {}", submit_sel, str(e))
                    continue

        if submit_success:
            logger.info("Zhihu: 评论提交成功")
            time.sleep(1.5)
            return True
        else:
            logger.warning("Zhihu: 评论提交失败，未找到有效的提交方式")
            return False

    except Exception as e:
        logger.warning("Zhihu: 评论过程失败: {}", str(e))
        return False


def follow_user(page: Page, user_id: str = None) -> bool:
    """关注用户 - 可以在详情页关注作者，或者访问指定用户主页关注"""
    logger.info("Zhihu: 尝试关注用户...")

    # 如果提供了用户ID，先访问用户主页
    if user_id:
        try:
            user_url = f"https://www.zhihu.com/people/{user_id}"
            logger.info("Zhihu: 访问用户主页: {}", user_url)
            page.goto(user_url, timeout=30000)
            time.sleep(2.0)
        except Exception as e:
            logger.warning("Zhihu: 访问用户主页失败: {}", str(e))
            return False

    # 查找关注按钮
    follow_selectors = [
        # 知乎特定的关注按钮
        "button:has-text('关注')",
        "button:has-text('+ 关注')",
        ".Button.FollowButton",
        "[data-testid='follow']",
        "button[aria-label*='关注']",

        # 通用关注按钮
        "[aria-label*='关注']",
        "[data-testid*='follow']",
        "button[title*='关注']",
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
                    logger.info("Zhihu: 已经关注过该用户")
                    return True

                if any(keyword in class_name.lower() for keyword in ["followed", "following"]):
                    logger.info("Zhihu: 已经关注过该用户")
                    return True

                # 点击关注按钮
                try:
                    loc.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    loc.click(timeout=5000)
                    logger.info("Zhihu: 关注成功 - 使用选择器: {}", follow_sel)
                    time.sleep(1.0)
                    return True
                except Exception as click_error:
                    logger.debug("Zhihu: 关注按钮点击失败 {}: {}", follow_sel, str(click_error))
                    continue

        except Exception as e:
            logger.debug("Zhihu: 关注选择器失败 {}: {}", follow_sel, str(e))
            continue

    logger.warning("Zhihu: 未找到可用的关注按钮")
    return False


def zhihu_interact_with_post(page: Page, do_comment: bool = True, do_like: bool = True,
                           do_collect: bool = True, do_follow: bool = False) -> dict:
    """与知乎内容进行交互"""
    logger.info("Zhihu: 开始与内容交互...")

    results = {
        "comment": False,
        "like": False,
        "collect": False,
        "follow": False
    }

    try:
        # 提取内容信息
        content = extract_post_content(page)
        logger.info("Zhihu: 提取内容 - {}", content[:50] + "..." if len(content) > 50 else content)

        # 执行各种操作
        if do_like:
            results["like"] = like_post(page)
            time.sleep(1.0)

        if do_collect:
            results["collect"] = collect_post(page)
            time.sleep(1.0)

        if do_comment:
            results["comment"] = comment_post(page)
            time.sleep(1.0)

        if do_follow:
            results["follow"] = follow_user(page)
            time.sleep(1.0)

        logger.info("Zhihu: 交互完成 - 评论:{} 点赞:{} 收藏:{} 关注:{}",
                   results["comment"], results["like"], results["collect"], results["follow"])

        return results

    except Exception as e:
        logger.warning("Zhihu: 交互过程失败: {}", str(e))
        return results
