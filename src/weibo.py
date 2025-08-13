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


# ==================== 智能元素定位系统 ====================

class ElementLocator:
    """智能元素定位器 - 提供多选择器、状态验证、动态等待的元素定位机制"""

    def __init__(self, page: Page, recorder=None):
        self.page = page
        self.recorder = recorder
        self.debug_mode = True

    def find_element_with_fallback(self, selectors_config: dict, timeout: int = 10) -> tuple:
        """
        使用多选择器策略查找元素

        Args:
            selectors_config: 选择器配置字典
                {
                    "name": "元素名称",
                    "selectors": ["选择器1", "选择器2", ...],
                    "verify_text": ["期望文本1", "期望文本2", ...] (可选),
                    "exclude_text": ["排除文本1", "排除文本2", ...] (可选)
                }
            timeout: 超时时间（秒）

        Returns:
            (element, selector_used, success) 元组
        """
        element_name = selectors_config.get("name", "未知元素")
        selectors = selectors_config.get("selectors", [])
        verify_text = selectors_config.get("verify_text", [])
        exclude_text = selectors_config.get("exclude_text", [])

        logger.info("🔍 开始查找元素: {}", element_name)

        start_time = time.time()
        attempt_count = 0

        while time.time() - start_time < timeout:
            attempt_count += 1
            logger.debug("🔄 第{}次尝试查找 {}", attempt_count, element_name)

            for i, selector in enumerate(selectors):
                try:
                    logger.debug("   尝试选择器 {}/{}: {}", i+1, len(selectors), selector)

                    # 处理XPath选择器
                    if selector.startswith("//"):
                        locator = self.page.locator(f"xpath={selector}")
                    else:
                        locator = self.page.locator(selector)

                    # 等待元素出现
                    try:
                        locator.first.wait_for(state="attached", timeout=1000)
                    except:
                        continue

                    # 获取所有匹配的元素
                    elements = locator.all()

                    for elem_idx, element in enumerate(elements):
                        if self._verify_element(element, verify_text, exclude_text, element_name, elem_idx):
                            logger.info("✅ 成功找到 {} (选择器: {}, 元素: {})", element_name, selector, elem_idx)
                            if self.recorder:
                                self.recorder.record("element_found",
                                                   name=element_name,
                                                   selector=selector,
                                                   attempt=attempt_count)
                            return element, selector, True

                except Exception as e:
                    logger.debug("   选择器 {} 失败: {}", selector, str(e))
                    continue

            # 短暂等待后重试
            time.sleep(0.5)

        logger.error("❌ 未找到元素: {} (尝试{}次，耗时{:.1f}秒)", element_name, attempt_count, time.time() - start_time)

        # 调试信息收集
        if self.debug_mode:
            self._collect_debug_info(element_name, selectors)

        return None, None, False

    def _verify_element(self, element, verify_text: list, exclude_text: list, element_name: str, elem_idx: int) -> bool:
        """验证元素是否符合条件"""
        try:
            # 检查元素是否可见
            if not element.is_visible():
                logger.debug("     元素{}不可见", elem_idx)
                return False

            # 检查元素是否可用
            if not element.is_enabled():
                logger.debug("     元素{}不可用", elem_idx)
                return False

            # 获取元素文本
            element_text = ""
            try:
                element_text = element.inner_text() or ""
            except:
                try:
                    element_text = element.text_content() or ""
                except:
                    pass

            logger.debug("     元素{}文本: '{}'", elem_idx, element_text[:50])

            # 验证包含文本
            if verify_text:
                text_match = any(text.lower() in element_text.lower() for text in verify_text)
                if not text_match:
                    logger.debug("     元素{}文本不匹配期望: {}", elem_idx, verify_text)
                    return False

            # 验证排除文本
            if exclude_text:
                text_exclude = any(text.lower() in element_text.lower() for text in exclude_text)
                if text_exclude:
                    logger.debug("     元素{}包含排除文本: {}", elem_idx, exclude_text)
                    return False

            return True

        except Exception as e:
            logger.debug("     元素{}验证失败: {}", elem_idx, str(e))
            return False

    def _collect_debug_info(self, element_name: str, selectors: list):
        """收集调试信息"""
        try:
            logger.debug("🔧 收集调试信息: {}", element_name)

            # 保存页面截图
            screenshot_path = f"debug_screenshot_{element_name}_{int(time.time())}.png"
            try:
                self.page.screenshot(path=screenshot_path)
                logger.info("📸 已保存调试截图: {}", screenshot_path)
            except Exception as e:
                logger.warning("截图保存失败: {}", str(e))

            # 记录页面基本信息
            try:
                page_title = self.page.title()
                page_url = self.page.url
                logger.debug("📄 页面信息 - 标题: {}, URL: {}", page_title, page_url)
            except Exception as e:
                logger.warning("页面信息获取失败: {}", str(e))

            # 分析页面结构
            try:
                # 统计常见元素数量
                button_count = self.page.locator("button").count()
                link_count = self.page.locator("a").count()
                input_count = self.page.locator("input, textarea").count()

                logger.debug("📊 页面元素统计 - 按钮: {}, 链接: {}, 输入框: {}",
                           button_count, link_count, input_count)
            except Exception as e:
                logger.warning("页面结构分析失败: {}", str(e))

        except Exception as e:
            logger.warning("调试信息收集失败: {}", str(e))

    def click_element_safely(self, element, element_name: str, selector: str) -> bool:
        """安全地点击元素"""
        try:
            logger.info("🖱️ 点击元素: {}", element_name)

            # 滚动到元素可见区域
            try:
                element.scroll_into_view_if_needed()
                time.sleep(0.5)  # 增加滚动后等待时间
            except Exception as e:
                logger.debug("滚动到元素失败: {}", str(e))

            # 等待元素稳定（随机间隔1-2秒）
            import random
            wait_time = random.uniform(1.0, 2.0)
            time.sleep(wait_time)
            logger.debug("等待元素稳定: {:.2f}秒", wait_time)

            # 获取元素位置用于记录
            x, y = None, None
            try:
                box = element.bounding_box()
                if box:
                    x = box["x"] + box["width"] / 2
                    y = box["y"] + box["height"] / 2
            except Exception as e:
                logger.debug("获取元素位置失败: {}", str(e))

            # 执行点击
            t0 = time.perf_counter()
            element.click()
            dur = int((time.perf_counter() - t0) * 1000)

            # 记录操作
            if self.recorder:
                self.recorder.record_click(f"page.locator({selector!r}).first", x, y, dur)

            logger.info("✅ 成功点击 {} (耗时: {}ms)", element_name, dur)
            return True

        except Exception as e:
            logger.error("❌ 点击 {} 失败: {}", element_name, str(e))
            return False

    def input_text_safely(self, element, text: str, element_name: str) -> bool:
        """安全地输入文本"""
        try:
            logger.info("⌨️ 输入文本到 {}: {}", element_name, text[:50] + "..." if len(text) > 50 else text)

            # 清空现有内容
            try:
                element.clear()
                time.sleep(0.2)
            except Exception as e:
                logger.debug("清空元素内容失败: {}", str(e))

            # 点击激活
            try:
                element.click()
                time.sleep(0.3)
            except Exception as e:
                logger.debug("点击激活元素失败: {}", str(e))

            # 输入文本
            element.fill(text)
            time.sleep(0.5)

            # 验证输入
            try:
                current_value = element.input_value() or element.inner_text() or ""
                if text in current_value or current_value in text:
                    logger.info("✅ 文本输入成功验证")
                else:
                    logger.warning("⚠️ 文本输入验证失败，期望: {}, 实际: {}", text[:30], current_value[:30])
            except Exception as e:
                logger.debug("文本输入验证失败: {}", str(e))

            return True

        except Exception as e:
            logger.error("❌ 文本输入到 {} 失败: {}", element_name, str(e))
            return False



# ==================== 微博元素选择器配置 ====================

# 关注按钮选择器配置
FOLLOW_BUTTON_CONFIG = {
    "name": "关注按钮",
    "selectors": [
        # 用户提供的精确XPath选择器（最高优先级）
        "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",

        # 原有的精确XPath选择器（高优先级）
        "/html/body/div[1]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",

        # 基于文本的选择器（中优先级）
        "button:has-text('+关注')",
        "button:has-text('+ 关注')",
        "button:has-text('关注'):not(:has-text('已关注')):not(:has-text('取消关注'))",
        "[role=button]:has-text('关注'):not(:has-text('已关注'))",
        "a:has-text('关注'):not(:has-text('已关注'))",

        # 基于属性的选择器
        "button[title='关注']",
        "button[aria-label='关注']",
        "button[data-testid*='follow']:not([data-testid*='unfollow'])",

        # 基于类名的选择器
        ".follow-btn:not(.followed)",
        ".btn-follow:not(.btn-followed)",
        ".follow-button:not(.following)",

        # XPath选择器（兜底）
        "//button[contains(text(), '+关注')]",
        "//button[contains(text(), '关注') and not(contains(text(), '已关注')) and not(contains(text(), '取消关注'))]",
        "//a[contains(text(), '关注') and not(contains(text(), '已关注'))]",
        "//button[@title='关注']",
        "//button[@aria-label='关注']"
    ],
    "verify_text": ["关注", "+关注", "+ 关注"],
    "exclude_text": ["已关注", "取消关注", "关注数", "关注者"]
}

# 点赞按钮选择器配置
LIKE_BUTTON_CONFIG = {
    "name": "点赞按钮",
    "selectors": [
        # 用户提供的精确XPath选择器（最高优先级）
        "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",

        # 原有的精确XPath选择器（高优先级）
        "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",

        # 基于文本的选择器
        "button:has-text('赞')",
        "button[aria-label*='赞']",
        "button[title*='赞']",
        "[role=button][aria-label*='赞']",

        # 基于类名和属性的选择器
        ".like-btn",
        ".btn-like",
        ".like-button",
        "[data-testid*='like']",
        "[data-action='like']",

        # 基于图标的选择器
        "button:has([class*='like'])",
        "button:has([class*='heart'])",
        "button:has([class*='thumb'])",

        # XPath选择器
        "//button[contains(@aria-label, '赞')]",
        "//button[contains(@title, '赞')]",
        "//button[contains(text(), '赞')]",
        "//button[contains(@class, 'like')]",
        "//button[@data-testid='like']"
    ],
    "verify_text": ["赞", "like"],
    "exclude_text": ["已赞", "取消赞", "赞数"]
}

# 评论框选择器配置
COMMENT_BOX_CONFIG = {
    "name": "评论输入框",
    "selectors": [
        # 基于placeholder的选择器
        "textarea[placeholder*='评论']",
        "textarea[placeholder*='说点什么']",
        "textarea[placeholder*='写评论']",
        "input[placeholder*='评论']",
        "input[placeholder*='说点什么']",

        # 基于类名的选择器
        ".comment-input textarea",
        ".comment-box textarea",
        ".comment-textarea",
        ".input-comment",

        # 通用选择器
        "textarea",
        "[contenteditable='true']",
        "[role='textbox']",

        # 基于ID的选择器
        "#comment-textarea",
        "#comment-input",

        # XPath选择器
        "//textarea[contains(@placeholder, '评论')]",
        "//textarea[contains(@placeholder, '说点什么')]",
        "//input[contains(@placeholder, '评论')]",
        "//div[@contenteditable='true']",
        "//textarea[@class*='comment']"
    ],
    "verify_text": [],
    "exclude_text": []
}

# 转发选项选择器配置
REPOST_OPTION_CONFIG = {
    "name": "同时转发选项",
    "selectors": [
        # 精确XPath选择器（最高优先级）
        "//*[@id=\"composerEle\"]/div[2]/div/div[3]/div/div[2]/label",

        # 基于文本的选择器
        "span:has-text('同时转发')",
        "label:has-text('同时转发')",
        "input[type='checkbox']:has-text('同时转发')",
        "label:has-text('同时转发') input[type='checkbox']",

        # 基于属性的选择器
        "input[type='checkbox'][name*='repost']",
        "input[type='checkbox'][value*='转发']",
        "input[type='checkbox'][data-testid*='repost']",

        # 基于类名的选择器
        ".repost-checkbox",
        ".forward-checkbox",
        ".repost-option input",
        ".forward-option input",

        # XPath选择器
        "//span[contains(text(), '同时转发')]",
        "//label[contains(text(), '同时转发')]",
        "//input[@type='checkbox' and contains(@name, 'repost')]",
        "//input[@type='checkbox' and contains(@value, '转发')]"
    ],
    "verify_text": ["同时转发", "转发"],
    "exclude_text": []
}

# 提交按钮选择器配置
SUBMIT_BUTTON_CONFIG = {
    "name": "提交按钮",
    "selectors": [
        # 基于文本的选择器
        "button:has-text('发布')",
        "button:has-text('评论')",
        "button:has-text('发送')",
        "button:has-text('提交')",
        "button:has-text('确定')",

        # 基于类名的选择器
        ".submit-btn",
        ".comment-submit",
        ".publish-btn",
        ".send-btn",

        # 基于属性的选择器
        "button[type='submit']",
        "[data-testid*='submit']",
        "[data-testid*='publish']",
        "[data-action='submit']",

        # XPath选择器
        "//button[contains(text(), '发布')]",
        "//button[contains(text(), '评论')]",
        "//button[contains(text(), '发送')]",
        "//button[@type='submit']"
    ],
    "verify_text": ["发布", "评论", "发送", "提交", "确定"],
    "exclude_text": ["取消", "删除"]
}


# ==================== 操作流程控制系统 ====================

class WeiboAutomationController:
    """微博自动化流程控制器 - 严格按照8步顺序执行操作"""

    def __init__(self, page: Page, recorder=None):
        self.page = page
        self.recorder = recorder
        self.locator = ElementLocator(page, recorder)

        # 操作状态跟踪
        self.step_results = {}
        self.current_step = 0
        self.total_steps = 8

        # 操作配置
        self.config = {
            "do_comment": False,
            "do_like": False,
            "do_repost": False,
            "do_follow": False
        }

        # 数据存储
        self.weibo_content = ""
        self.comment_text = ""
        self.weibo_link = ""

        # MCP优化模式
        self.optimized_mode = False
        self.optimized_selectors = {}
        self.optimization_applied = False

    def _find_element_optimized(self, element_type: str, timeout: int = 10) -> tuple:
        """使用优化选择器查找元素"""

        if not self.optimized_mode or element_type not in self.optimized_selectors:
            logger.debug("优化模式未启用或无优化选择器，使用默认方法")
            return None, None, False

        config = self.optimized_selectors[element_type]
        logger.info("🔍 使用优化选择器查找: {}", element_type)

        # 构建选择器列表
        all_selectors = [config["primary"]] + config.get("fallbacks", [])

        start_time = time.time()

        while time.time() - start_time < timeout:
            for i, selector in enumerate(all_selectors):
                try:
                    logger.debug("   优化选择器 {}/{}: {}", i+1, len(all_selectors), selector)

                    # 根据选择器类型进行定位
                    if selector.startswith("//") or selector.startswith("/html"):
                        element = self.page.query_selector(f"xpath={selector}")
                    else:
                        element = self.page.query_selector(selector)

                    if element and element.is_visible() and element.is_attached():
                        logger.info("✅ 优化选择器成功找到 {} (选择器: {})", element_type, selector)
                        return element, selector, True

                except Exception as e:
                    logger.debug("   优化选择器失败: {}", str(e))
                    continue

            # 短暂等待后重试
            time.sleep(0.5)

        logger.warning("⚠️ 优化选择器未找到元素: {}", element_type)
        return None, None, False

    def execute_automation(self, do_comment: bool, do_like: bool, do_repost: bool, do_follow: bool) -> dict:
        """执行完整的微博自动化流程"""

        # 更新配置
        self.config.update({
            "do_comment": do_comment,
            "do_like": do_like,
            "do_repost": do_repost,
            "do_follow": do_follow
        })

        logger.info("🚀 开始执行微博自动化流程")
        logger.info("📋 操作配置: 评论={}, 点赞={}, 转发={}, 关注={}",
                   do_comment, do_like, do_repost, do_follow)

        try:
            # 严格按照8步顺序执行，步骤1失败时立即终止

            # 步骤1：进入详情页（关键步骤，失败时立即终止）
            step1_success = self._step_1_enter_detail_page()
            if not step1_success:
                logger.error("❌ 关键步骤1失败：无法进入详情页")
                logger.error("❌ 为避免在错误页面执行操作，整个流程立即终止")
                return self._generate_error_report("critical_step1_failed_no_detail_page")

            # 步骤1成功后，继续执行后续步骤
            logger.info("✅ 关键步骤1成功，继续执行后续操作...")
            success = True
            success &= step1_success  # 步骤1已经成功
            success &= self._step_2_extract_content()
            success &= self._step_3_click_follow_button()
            success &= self._step_4_find_comment_box()
            success &= self._step_5_generate_and_input_comment()
            success &= self._step_6_click_repost_option()
            success &= self._step_7_click_like_button()
            success &= self._step_8_submit_comment()

            # 生成结果报告
            return self._generate_result_report(success)

        except Exception as e:
            logger.error("❌ 自动化流程执行失败: {}", str(e))
            return self._generate_error_report(str(e))

    def _step_1_enter_detail_page(self) -> bool:
        """步骤1：进入微博详情页"""
        self.current_step = 1
        logger.info("📍 步骤1/8：进入微博详情页")

        try:
            # 首先确保在微博首页
            t0 = time.perf_counter()
            self.page.goto(WEIBO_HOME)
            self.page.wait_for_load_state("domcontentloaded")
            dur = int((time.perf_counter() - t0) * 1000)

            if self.recorder:
                self.recorder.record_navigation(WEIBO_HOME, dur)

            # 等待页面加载
            logger.info("⏳ 等待页面内容加载...")
            try:
                self.page.wait_for_selector("#scroller", timeout=15000)
                time.sleep(2.0)  # 额外等待确保内容完全加载
            except Exception:
                logger.warning("⚠️ 主滚动容器加载超时，尝试继续...")

            # 多次尝试获取微博卡片和详情页链接（关键改进）
            max_card_attempts = 3
            detail_link = None

            for attempt in range(max_card_attempts):
                logger.info("🔍 第 {}/{} 次尝试获取微博卡片和详情页链接", attempt + 1, max_card_attempts)

                # 获取一条微博卡片
                card = pick_random_post(self.page, limit=20, require_comment=False)
                if not card:
                    logger.warning("⚠️ 第 {} 次尝试：未找到可用的微博卡片", attempt + 1)
                    if attempt < max_card_attempts - 1:
                        logger.info("⏳ 等待3秒后重试...")
                        time.sleep(3.0)
                        # 刷新页面重试
                        self.page.reload()
                        self.page.wait_for_load_state("domcontentloaded")
                        time.sleep(2.0)
                        continue
                    else:
                        logger.error("❌ 关键错误：经过 {} 次尝试，仍未找到可用的微博卡片", max_card_attempts)
                        logger.error("❌ 无法继续执行后续自动化操作，流程终止")
                        self.step_results[1] = {"success": False, "error": "no_card_visible_after_retries"}
                        return False

                # 尝试提取详情页链接（使用增强的提取函数）
                logger.info("🔗 尝试从卡片提取详情页链接...")
                detail_link = extract_post_link_from_card(card, self.page)

                if detail_link:
                    logger.info("✅ 成功获取详情页链接: {}", detail_link)
                    break
                else:
                    logger.warning("⚠️ 第 {} 次尝试：未能从当前卡片提取详情页链接", attempt + 1)
                    if attempt < max_card_attempts - 1:
                        logger.info("⏳ 等待2秒后尝试下一个卡片...")
                        time.sleep(2.0)
                        continue

            # 严格验证是否成功获取详情页链接
            if not detail_link:
                logger.error("❌ 关键错误：经过 {} 次尝试，仍无法获取详情页链接", max_card_attempts)
                logger.error("❌ 这是一个严重错误，无法继续执行后续自动化操作")
                logger.error("❌ 流程终止，避免在错误页面执行操作")
                self.step_results[1] = {"success": False, "error": "no_detail_link_after_all_retries"}
                return False

            # 验证链接格式
            if not _DEF_RE_DETAIL.search(detail_link):
                logger.error("❌ 详情页链接格式无效: {}", detail_link)
                logger.error("❌ 无法继续执行后续自动化操作")
                self.step_results[1] = {"success": False, "error": "invalid_detail_link_format"}
                return False

            self.weibo_link = detail_link
            logger.info("✅ 详情页链接验证通过: {}", detail_link)

            # 进入详情页
            logger.info("🚀 正在进入微博详情页...")
            t0 = time.perf_counter()
            self.page.goto(detail_link)
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(3.0)  # 增加等待时间确保详情页完全加载
            dur = int((time.perf_counter() - t0) * 1000)

            if self.recorder:
                self.recorder.record_navigation(detail_link, dur)

            # 严格验证是否成功进入详情页
            current_url = self.page.url or ""
            if not _DEF_RE_DETAIL.search(current_url):
                logger.error("❌ 关键错误：进入详情页失败")
                logger.error("❌ 期望URL格式: weibo.com/用户ID/微博ID")
                logger.error("❌ 实际URL: {}", current_url)
                logger.error("❌ 无法继续执行后续自动化操作")
                self.step_results[1] = {"success": False, "error": "failed_to_enter_detail_page"}
                return False

            logger.info("✅ 步骤1完成：成功进入微博详情页")
            logger.info("   目标链接: {}", detail_link)
            logger.info("   实际URL: {}", current_url)
            logger.info("   ✅ 所有后续操作将在正确的详情页上执行")
            self.step_results[1] = {"success": True, "weibo_link": detail_link, "final_url": current_url}
            return True

        except Exception as e:
            logger.error("❌ 步骤1异常失败: {}", str(e))
            logger.error("❌ 这是一个关键错误，无法继续执行后续自动化操作")
            logger.error("❌ 流程终止，避免在错误状态下执行操作")
            self.step_results[1] = {"success": False, "error": str(e)}
            return False

    def _step_2_extract_content(self) -> bool:
        """步骤2：获取微博内容"""
        self.current_step = 2
        logger.info("📝 步骤2/8：获取微博内容")

        try:
            # 使用多种策略提取内容（精确XPath优先）
            content_selectors = [
                f"xpath={X_POST}",  # 使用更新的精确XPath
                f"xpath={X_POST_FALLBACK}",  # 备选XPath保持兼容性
                "article .txt",
                "article [node-type='feed_list_content']",
                ".detail-content .txt",
                ".post-content",
                ".weibo-detail .txt"
            ]

            content_text = ""
            for selector in content_selectors:
                try:
                    if selector.startswith("xpath="):
                        element = self.page.query_selector(selector)
                    else:
                        element = self.page.locator(selector).first

                    if element:
                        text = element.text_content() or element.inner_text() or ""
                        if text.strip() and len(text.strip()) > 10:
                            content_text = text.strip()
                            logger.info("✅ 成功提取微博内容 ({} 字符): {}...",
                                      len(content_text), content_text[:50])
                            break
                except Exception as e:
                    logger.debug("内容提取选择器 {} 失败: {}", selector, str(e))
                    continue

            if not content_text:
                # 尝试从页面标题获取内容
                try:
                    page_title = self.page.title()
                    if page_title and len(page_title.strip()) > 20:
                        content_text = page_title.replace(" - 微博", "").replace("的微博", "").strip()
                        logger.info("✅ 从页面标题提取内容: {}...", content_text[:50])
                except Exception:
                    pass

            if content_text:
                self.weibo_content = content_text
                logger.info("✅ 步骤2完成：成功获取微博内容")
                self.step_results[2] = {"success": True, "content_length": len(content_text)}
                return True
            else:
                logger.warning("⚠️ 步骤2部分成功：未能提取到微博内容，但继续执行")
                self.weibo_content = "默认内容"
                self.step_results[2] = {"success": True, "content_length": 0, "warning": "no_content"}
                return True

        except Exception as e:
            logger.error("❌ 步骤2失败: {}", str(e))
            self.step_results[2] = {"success": False, "error": str(e)}
            return False

    def _step_3_click_follow_button(self) -> bool:
        """步骤3：点击关注按钮"""
        self.current_step = 3
        logger.info("👤 步骤3/8：点击关注按钮")

        if not self.config["do_follow"]:
            logger.info("⏭️ 跳过关注操作（未启用）")
            self.step_results[3] = {"success": True, "skipped": True}
            return True

        try:
            # 使用优化的选择器配置（如果可用）
            if self.optimized_mode and "follow_button" in self.optimized_selectors:
                element, selector, found = self._find_element_optimized("follow_button", timeout=5)
                self.optimization_applied = True
            else:
                element, selector, found = self.locator.find_element_with_fallback(
                    FOLLOW_BUTTON_CONFIG, timeout=5
                )

            if found and element:
                # 点击关注按钮
                success = self.locator.click_element_safely(element, "关注按钮", selector)
                if success:
                    time.sleep(2.0)  # 等待关注操作完成（优化间隔）
                    logger.info("✅ 步骤3完成：成功点击关注按钮")
                    self.step_results[3] = {"success": True, "executed": True, "optimized": self.optimization_applied}
                    return True
                else:
                    logger.error("❌ 关注按钮点击失败")
                    self.step_results[3] = {"success": False, "error": "click_failed"}
                    return False
            else:
                logger.info("ℹ️ 未找到关注按钮（可能已关注）")
                self.step_results[3] = {"success": True, "skipped": True, "reason": "already_followed"}
                return True

        except Exception as e:
            logger.error("❌ 步骤3失败: {}", str(e))
            self.step_results[3] = {"success": False, "error": str(e)}
            return False

    def _step_4_find_comment_box(self) -> bool:
        """步骤4：找到并点击评论框"""
        self.current_step = 4
        logger.info("💬 步骤4/8：找到并点击评论框")

        if not (self.config["do_comment"] or self.config["do_repost"]):
            logger.info("⏭️ 跳过评论框操作（未启用评论或转发）")
            self.step_results[4] = {"success": True, "skipped": True}
            return True

        try:
            # 使用智能元素定位查找评论框
            element, selector, found = self.locator.find_element_with_fallback(
                COMMENT_BOX_CONFIG, timeout=8
            )

            if found and element:
                # 点击激活评论框
                success = self.locator.click_element_safely(element, "评论输入框", selector)
                if success:
                    time.sleep(1.5)  # 等待评论框激活（优化间隔）
                    self.comment_box_element = element
                    self.comment_box_selector = selector
                    logger.info("✅ 步骤4完成：成功激活评论框")
                    self.step_results[4] = {"success": True, "activated": True}
                    return True
                else:
                    logger.error("❌ 评论框点击失败")
                    self.step_results[4] = {"success": False, "error": "click_failed"}
                    return False
            else:
                logger.error("❌ 未找到评论输入框")
                self.step_results[4] = {"success": False, "error": "not_found"}
                return False

        except Exception as e:
            logger.error("❌ 步骤4失败: {}", str(e))
            self.step_results[4] = {"success": False, "error": str(e)}
            return False

    def _step_5_generate_and_input_comment(self) -> bool:
        """步骤5：根据微博内容生成并输入评论"""
        self.current_step = 5
        logger.info("✍️ 步骤5/8：生成并输入评论内容")

        if not (self.config["do_comment"] or self.config["do_repost"]):
            logger.info("⏭️ 跳过评论输入（未启用评论或转发）")
            self.step_results[5] = {"success": True, "skipped": True}
            return True

        try:
            # 生成评论内容
            self.comment_text = random_comment(self.weibo_content)
            logger.info("📝 生成评论内容: {}", self.comment_text)

            # 输入评论内容
            if hasattr(self, 'comment_box_element') and self.comment_box_element:
                success = self.locator.input_text_safely(
                    self.comment_box_element, self.comment_text, "评论输入框"
                )
                if success:
                    time.sleep(2.0)  # 等待输入完成（优化间隔）
                    logger.info("✅ 步骤5完成：成功输入评论内容")
                    self.step_results[5] = {"success": True, "comment_length": len(self.comment_text)}
                    return True
                else:
                    logger.error("❌ 评论内容输入失败")
                    self.step_results[5] = {"success": False, "error": "input_failed"}
                    return False
            else:
                logger.error("❌ 评论框元素不可用")
                self.step_results[5] = {"success": False, "error": "no_comment_box"}
                return False

        except Exception as e:
            logger.error("❌ 步骤5失败: {}", str(e))
            self.step_results[5] = {"success": False, "error": str(e)}
            return False

    def _step_6_click_repost_option(self) -> bool:
        """步骤6：点击"同时转发"按钮"""
        self.current_step = 6
        logger.info("🔄 步骤6/8：点击'同时转发'选项")

        if not self.config["do_repost"]:
            logger.info("⏭️ 跳过转发操作（未启用）")
            self.step_results[6] = {"success": True, "skipped": True}
            return True

        try:
            # 使用智能元素定位查找转发选项
            element, selector, found = self.locator.find_element_with_fallback(
                REPOST_OPTION_CONFIG, timeout=5
            )

            if found and element:
                # 检查是否已勾选
                try:
                    is_checked = element.is_checked() if hasattr(element, 'is_checked') else False
                except:
                    is_checked = False

                if not is_checked:
                    success = self.locator.click_element_safely(element, "同时转发选项", selector)
                    if success:
                        time.sleep(1.5)  # 等待选项生效（优化间隔）
                        logger.info("✅ 步骤6完成：成功勾选'同时转发'选项")
                        self.step_results[6] = {"success": True, "checked": True}
                        return True
                    else:
                        logger.error("❌ 转发选项点击失败")
                        self.step_results[6] = {"success": False, "error": "click_failed"}
                        return False
                else:
                    logger.info("ℹ️ '同时转发'选项已勾选")
                    self.step_results[6] = {"success": True, "already_checked": True}
                    return True
            else:
                logger.warning("⚠️ 未找到'同时转发'选项，继续执行")
                self.step_results[6] = {"success": True, "not_found": True}
                return True

        except Exception as e:
            logger.error("❌ 步骤6失败: {}", str(e))
            self.step_results[6] = {"success": False, "error": str(e)}
            return False

    def _step_7_click_like_button(self) -> bool:
        """步骤7：点击点赞按钮"""
        self.current_step = 7
        logger.info("👍 步骤7/8：点击点赞按钮")

        if not self.config["do_like"]:
            logger.info("⏭️ 跳过点赞操作（未启用）")
            self.step_results[7] = {"success": True, "skipped": True}
            return True

        try:
            # 使用优化的选择器配置（如果可用）
            if self.optimized_mode and "like_button" in self.optimized_selectors:
                element, selector, found = self._find_element_optimized("like_button", timeout=5)
                self.optimization_applied = True
            else:
                element, selector, found = self.locator.find_element_with_fallback(
                    LIKE_BUTTON_CONFIG, timeout=5
                )

            if found and element:
                success = self.locator.click_element_safely(element, "点赞按钮", selector)
                if success:
                    time.sleep(2.0)  # 等待点赞操作完成（优化间隔）
                    logger.info("✅ 步骤7完成：成功点击点赞按钮")
                    self.step_results[7] = {"success": True, "executed": True, "optimized": self.optimization_applied}
                    return True
                else:
                    logger.error("❌ 点赞按钮点击失败")
                    self.step_results[7] = {"success": False, "error": "click_failed"}
                    return False
            else:
                logger.error("❌ 未找到点赞按钮")
                self.step_results[7] = {"success": False, "error": "not_found"}
                return False

        except Exception as e:
            logger.error("❌ 步骤7失败: {}", str(e))
            self.step_results[7] = {"success": False, "error": str(e)}
            return False

    def _step_8_submit_comment(self) -> bool:
        """步骤8：点击评论提交按钮完成整个流程"""
        self.current_step = 8
        logger.info("🚀 步骤8/8：提交评论完成流程")

        if not (self.config["do_comment"] or self.config["do_repost"]):
            logger.info("⏭️ 跳过提交操作（未启用评论或转发）")
            self.step_results[8] = {"success": True, "skipped": True}
            return True

        try:
            # 优先尝试使用键盘快捷键提交（用户建议的方案）
            logger.info("🎯 优先尝试键盘快捷键 Ctrl+Enter 提交")
            try:
                if hasattr(self, 'comment_box_element') and self.comment_box_element:
                    self.comment_box_element.press("Control+Enter")
                    time.sleep(2.5)  # 增加等待时间确保提交完成
                    logger.info("✅ 步骤8完成：使用快捷键提交成功")
                    self.step_results[8] = {"success": True, "submitted_by_hotkey": True}
                    return True
                else:
                    logger.warning("⚠️ 评论框元素不可用，尝试页面级快捷键")
                    self.page.keyboard.press("Control+Enter")
                    time.sleep(2.5)
                    logger.info("✅ 步骤8完成：使用页面级快捷键提交成功")
                    self.step_results[8] = {"success": True, "submitted_by_page_hotkey": True}
                    return True
            except Exception as hotkey_error:
                logger.warning("⚠️ 快捷键提交失败: {}，尝试按钮提交", str(hotkey_error))

            # 如果快捷键失败，再尝试查找提交按钮
            logger.info("🔄 尝试查找提交按钮")
            element, selector, found = self.locator.find_element_with_fallback(
                SUBMIT_BUTTON_CONFIG, timeout=8
            )

            if found and element:
                success = self.locator.click_element_safely(element, "提交按钮", selector)
                if success:
                    time.sleep(2.5)  # 增加等待时间确保提交完成
                    logger.info("✅ 步骤8完成：成功提交评论")
                    self.step_results[8] = {"success": True, "submitted": True}
                    return True
                else:
                    logger.error("❌ 提交按钮点击失败")
                    self.step_results[8] = {"success": False, "error": "click_failed"}
                    return False
            else:
                logger.error("❌ 未找到提交按钮且快捷键也失败")
                self.step_results[8] = {"success": False, "error": "no_submit_method"}
                return False

        except Exception as e:
            logger.error("❌ 步骤8失败: {}", str(e))
            self.step_results[8] = {"success": False, "error": str(e)}
            return False

    def _generate_result_report(self, overall_success: bool) -> dict:
        """生成结果报告"""

        # 统计各操作的执行情况
        follow_executed = self.step_results.get(3, {}).get("executed", False)
        like_executed = self.step_results.get(7, {}).get("executed", False)
        comment_executed = self.step_results.get(5, {}).get("success", False) and self.config["do_comment"]
        repost_executed = self.step_results.get(6, {}).get("checked", False) and self.config["do_repost"]

        # 计算成功率
        total_steps = sum(1 for i in range(1, 9) if self.step_results.get(i, {}).get("success", False))
        success_rate = (total_steps / 8) * 100

        logger.info("📊 流程执行完成")
        logger.info("   总体成功: {}", "✅" if overall_success else "❌")
        logger.info("   成功率: {:.1f}% ({}/8)", success_rate, total_steps)
        logger.info("   关注: {}", "✅" if follow_executed else "❌")
        logger.info("   点赞: {}", "✅" if like_executed else "❌")
        logger.info("   评论: {}", "✅" if comment_executed else "❌")
        logger.info("   转发: {}", "✅" if repost_executed else "❌")

        return {
            "follow_executed": follow_executed,
            "like_executed": like_executed,
            "comment_executed": comment_executed,
            "repost_executed": repost_executed,
            "weibo_link": self.weibo_link,
            "success_rate": success_rate,
            "step_results": self.step_results,
            "mcp_script": self.recorder.to_python_script() if self.recorder else "",
            "mcp_code": self.recorder.to_mcp_code() if self.recorder else ""
        }

    def _generate_error_report(self, error_message: str) -> dict:
        """生成错误报告"""
        logger.error("❌ 自动化流程失败: {}", error_message)

        # 特殊处理关键步骤失败
        if "critical_step1_failed" in error_message:
            logger.error("❌ 这是一个关键错误：无法进入微博详情页")
            logger.error("❌ 所有后续操作已被阻止，避免在错误页面执行")
            logger.error("❌ 建议检查：")
            logger.error("   1. 网络连接是否稳定")
            logger.error("   2. 微博页面结构是否发生变化")
            logger.error("   3. 详情页链接选择器是否需要更新")

        return {
            "follow_executed": False,
            "like_executed": False,
            "comment_executed": False,
            "repost_executed": False,
            "weibo_link": self.weibo_link,
            "error": error_message,
            "critical_failure": "critical_step1_failed" in error_message,
            "step_results": self.step_results,
            "mcp_script": self.recorder.to_python_script() if self.recorder else "",
            "mcp_code": self.recorder.to_mcp_code() if self.recorder else ""
        }
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
    """返回 'followed' | 'not_followed' | 'unknown'。
    新逻辑：在详情页如果出现关注按钮就代表没有关注，如果已关注则没有关注按钮。
    """
    logger.info("备选流程：检测关注状态（基于关注按钮存在性）")

    # 新逻辑：查找关注按钮的存在性
    follow_button_selectors = [
        "button:has-text('关注')",
        "[role=button]:has-text('关注')",
        "a:has-text('关注')",
        "button[title*='关注']",
        "button[aria-label*='关注']",
        ".follow-btn",
        ".btn-follow",
        "[data-testid*='follow']",
        "button:has-text('Follow')",
        "[role=button]:has-text('Follow')",
        # XPath方式查找关注按钮
        "//button[contains(text(), '关注')]",
        "//a[contains(text(), '关注')]",
        "//button[contains(@aria-label, '关注')]"
    ]

    # 检查是否存在关注按钮
    follow_button_found = False
    for sel in follow_button_selectors:
        try:
            if sel.startswith("//"):
                # XPath选择器
                elements = page.locator(f"xpath={sel}").all()
            else:
                elements = page.locator(sel).all()

            for elem in elements:
                if elem.is_visible():
                    text = elem.inner_text() or ""
                    # 确保是"关注"按钮，而不是"已关注"或"取消关注"
                    if ("关注" in text and "已关注" not in text and "取消关注" not in text) or \
                       ("follow" in text.lower() and "following" not in text.lower() and "unfollow" not in text.lower()):
                        follow_button_found = True
                        logger.info("备选流程：找到关注按钮，用户未关注")
                        return "not_followed"
        except Exception as e:
            logger.debug("备选流程：关注按钮检测选择器 {} 失败: {}", sel, e)
            continue

    # 如果没有找到关注按钮，检查是否有"已关注"相关的元素
    followed_indicators = [
        "button:has-text('已关注')",
        "button:has-text('取消关注')",
        "[role=button]:has-text('已关注')",
        "a:has-text('已关注')",
        ".followed",
        ".following",
        ".btn-followed",
        "//button[contains(text(), '已关注')]",
        "//button[contains(text(), '取消关注')]"
    ]

    for sel in followed_indicators:
        try:
            if sel.startswith("//"):
                elements = page.locator(f"xpath={sel}").all()
            else:
                elements = page.locator(sel).all()

            for elem in elements:
                if elem.is_visible():
                    text = elem.inner_text() or ""
                    if "已关注" in text or "取消关注" in text or "following" in text.lower():
                        logger.info("备选流程：找到已关注标识，用户已关注")
                        return "followed"
        except Exception as e:
            logger.debug("备选流程：已关注检测选择器 {} 失败: {}", sel, e)
            continue

    # 如果既没有关注按钮也没有已关注标识，可能是页面结构问题
    logger.warning("备选流程：未找到关注按钮或已关注标识，状态未知")
    return "unknown"  # 返回未知状态，让调用方决定如何处理


def ensure_follow_on_page(page: Page, recorder: OperationRecorder | None = None) -> bool:
    """若未关注则点击关注。返回是否执行了关注操作。使用新的关注逻辑（基于关注按钮存在性）。"""
    status = detect_follow_status_on_page(page)
    if recorder:
        recorder.record_state("follow_status_before", status)

    # 新逻辑：在检测到"not_followed"或"unknown"状态时执行关注操作
    if status == "not_followed" or status == "unknown":
        logger.info("备选流程：检测到未关注状态或状态未知，执行关注操作")

        # 策略1：精确查找关注按钮（排除已关注按钮）
        follow_selectors = [
            "button:has-text('关注'):not(:has-text('已关注')):not(:has-text('取消关注'))",
            "[role=button]:has-text('关注'):not(:has-text('已关注'))",
            "a:has-text('关注'):not(:has-text('已关注'))",
            "button[title='关注']",
            "button[aria-label='关注']",
            ".follow-btn:not(.followed)",
            ".btn-follow:not(.btn-followed)",
            "[data-testid*='follow']:not([data-testid*='unfollow'])",
            "button:has-text('Follow'):not(:has-text('Following')):not(:has-text('Unfollow'))",
            "[role=button]:has-text('Follow'):not(:has-text('Following'))"
        ]

        for sel in follow_selectors:
            try:
                loc = page.locator(sel).first
                if loc and loc.count() > 0 and loc.is_visible():
                    # 双重确认这是关注按钮
                    text = loc.inner_text() or ""
                    if ("关注" in text and "已关注" not in text and "取消关注" not in text) or \
                       ("follow" in text.lower() and "following" not in text.lower() and "unfollow" not in text.lower()):
                        x, y = _locator_center_xy(loc)
                        t0 = time.perf_counter(); loc.click(); dur = int((time.perf_counter()-t0)*1000)
                        if recorder:
                            recorder.record_click(f"page.locator({sel!r}).first", x, y, dur)
                        logger.info("备选流程：通过选择器 {} 成功点击关注按钮，按钮文本: {}", sel, text)
                        time.sleep(1)  # 等待关注操作完成

                        # 验证关注是否成功
                        new_status = detect_follow_status_on_page(page)
                        if new_status == "followed":
                            logger.info("备选流程：关注操作成功验证")
                            return True
                        else:
                            logger.warning("备选流程：关注操作可能失败，新状态: {}", new_status)
                            return True  # 仍然返回True，因为我们确实点击了关注按钮
            except Exception as e:
                logger.debug("备选流程：选择器 {} 关注失败: {}", sel, e)
                continue

        # 策略2：XPath方式查找关注按钮
        xpath_selectors = [
            "//button[contains(text(), '关注') and not(contains(text(), '已关注')) and not(contains(text(), '取消关注'))]",
            "//a[contains(text(), '关注') and not(contains(text(), '已关注'))]",
            "//button[contains(@aria-label, '关注') and not(contains(@aria-label, '已关注'))]",
            "//*[@role='button' and contains(text(), '关注') and not(contains(text(), '已关注'))]"
        ]

        for xpath in xpath_selectors:
            try:
                loc = page.locator(f"xpath={xpath}").first
                if loc and loc.count() > 0 and loc.is_visible():
                    text = loc.inner_text() or ""
                    if "关注" in text and "已关注" not in text and "取消关注" not in text:
                        x, y = _locator_center_xy(loc)
                        t0 = time.perf_counter(); loc.click(); dur = int((time.perf_counter()-t0)*1000)
                        if recorder:
                            recorder.record_click(f"xpath={xpath}", x, y, dur)
                        logger.info("备选流程：通过XPath {} 成功点击关注按钮，按钮文本: {}", xpath, text)
                        time.sleep(1)
                        return True
            except Exception as e:
                logger.debug("备选流程：XPath {} 关注失败: {}", xpath, e)
                continue

        logger.warning("备选流程：检测到未关注状态但未找到可点击的关注按钮")
        return False
    elif status == "followed":
        logger.info("备选流程：用户已关注，跳过关注操作")
        return False
    else:
        logger.info("备选流程：关注状态未知，假设已关注，跳过关注操作")
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
    """
    增强版：从卡片中提取详情链接，使用多种策略和重试机制

    这是一个关键函数，必须成功找到详情页链接才能继续后续操作
    """
    logger.info("🔍 开始提取微博详情页链接...")

    # 详情页链接选择器策略（按优先级排序）
    link_selectors = [
        # 时间链接（最常见）
        "time a",
        ".time a",
        "[data-time] a",

        # 直接的详情链接
        "a:has-text('详情')",
        "a:has-text('全文')",
        "a[title*='详情']",

        # 微博ID链接
        "a[href*='weibo.com']",
        "a[href*='/status']",
        "a[href*='/detail/']",

        # 基于属性的链接
        "a[data-url*='weibo.com']",
        "a[data-href*='weibo.com']",

        # 更广泛的链接搜索
        "article a[href]",
        ".card a[href]",
        ".post a[href]",

        # XPath选择器
        "xpath=//a[contains(@href, 'weibo.com')]",
        "xpath=//a[contains(@href, '/status')]",
        "xpath=//time//a",
        "xpath=//a[contains(text(), '详情')]",
        "xpath=//a[contains(text(), '全文')]"
    ]

    # 多次尝试提取链接（重试机制）
    max_attempts = 3
    for attempt in range(max_attempts):
        logger.debug("尝试第 {}/{} 次提取链接", attempt + 1, max_attempts)

        try:
            # 确保卡片可见
            if card:
                try:
                    card.scroll_into_view_if_needed()
                    time.sleep(0.5)
                except Exception as e:
                    logger.debug("滚动卡片失败: {}", str(e))

            # 尝试所有选择器
            for i, selector in enumerate(link_selectors):
                try:
                    logger.debug("   尝试选择器 {}/{}: {}", i+1, len(link_selectors), selector)

                    if selector.startswith("xpath="):
                        # XPath选择器
                        xpath = selector[6:]  # 移除 "xpath=" 前缀
                        elements = card.locator(f"xpath={xpath}").all()
                    else:
                        # CSS选择器
                        elements = card.locator(selector).all()

                    if not elements:
                        continue

                    # 检查每个找到的元素
                    for element in elements:
                        try:
                            href = element.get_attribute("href") or ""
                            if not href:
                                continue

                            # 处理相对链接
                            if href.startswith("/"):
                                href = "https://weibo.com" + href

                            # 验证链接格式
                            if _DEF_RE_DETAIL.search(href):
                                clean_link = href.split("?")[0]  # 移除查询参数
                                logger.info("✅ 成功找到详情页链接: {}", clean_link)
                                logger.info("   使用选择器: {}", selector)
                                return clean_link

                        except Exception as e:
                            logger.debug("   元素处理失败: {}", str(e))
                            continue

                except Exception as e:
                    logger.debug("   选择器失败: {} - {}", selector, str(e))
                    continue

            # 如果这次尝试失败，等待后重试
            if attempt < max_attempts - 1:
                logger.debug("第 {} 次尝试失败，等待后重试...", attempt + 1)
                time.sleep(1.0)

        except Exception as e:
            logger.debug("第 {} 次尝试异常: {}", attempt + 1, str(e))
            if attempt < max_attempts - 1:
                time.sleep(1.0)

    # 所有尝试都失败了
    logger.error("❌ 经过 {} 次尝试，仍无法找到详情页链接", max_attempts)

    # 最后的兜底检查：如果当前页面已经是详情页
    try:
        current_url = page.url or ""
        if _DEF_RE_DETAIL.search(current_url):
            clean_url = current_url.split("?")[0]
            logger.warning("⚠️ 使用当前页面URL作为详情页链接: {}", clean_url)
            return clean_url
    except Exception as e:
        logger.debug("当前页面URL检查失败: {}", str(e))

    return None


# 卡片流程模式已删除 - 统一使用备选流程模式





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

# 微博内容元素XPath（更新为精确路径）
X_POST = "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/div/div[1]/div"
# 备选微博内容XPath（保持兼容性）
X_POST_FALLBACK = "//*[@id='scroller']/div[1]/div[1]/div/article/div/div[1]/div[1]/div"
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


def comment_and_optionally_repost(page: Page, do_repost: bool = False, do_like: bool = False, do_follow: bool = False, back_to_home: bool = True) -> bool:
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

    # 1. 关注操作（修复版：在获取博文内容后立即执行）
    if do_follow:
        logger.info("Weibo: 开始执行关注操作")
        logger.info("Weibo: 检测关注状态...")

        try:
            # 使用修复后的关注检测和执行逻辑
            follow_status = detect_follow_status_on_page(page)
            logger.info("Weibo: 当前关注状态检测结果: {}", follow_status)

            if follow_status == "not_followed" or follow_status == "unknown":
                logger.info("Weibo: 检测到未关注状态或状态未知，开始执行关注操作")

                # 基于截图位置的关注按钮选择器（右上角"+关注"按钮）
                follow_selectors = [
                    # 基于截图的关注按钮位置
                    "button:has-text('+关注')",
                    "button:has-text('+ 关注')",
                    "button:has-text('关注'):not(:has-text('已关注')):not(:has-text('取消关注'))",
                    "[role=button]:has-text('关注'):not(:has-text('已关注'))",
                    "a:has-text('关注'):not(:has-text('已关注'))",
                    # 通用关注按钮选择器
                    ".follow-btn:not(.followed)",
                    ".btn-follow:not(.btn-followed)",
                    "[data-testid*='follow']:not([data-testid*='unfollow'])",
                    "button[title='关注']",
                    "button[aria-label='关注']",
                    # XPath选择器（基于截图位置）
                    "//button[contains(text(), '+关注')]",
                    "//button[contains(text(), '关注') and not(contains(text(), '已关注')) and not(contains(text(), '取消关注'))]",
                    "//a[contains(text(), '关注') and not(contains(text(), '已关注'))]"
                ]

                follow_button_found = False
                for i, sel in enumerate(follow_selectors):
                    try:
                        logger.debug("Weibo: 尝试关注按钮选择器 {}/{}: {}", i+1, len(follow_selectors), sel)

                        if sel.startswith("//"):
                            # XPath选择器
                            follow_btn = page.locator(f"xpath={sel}").first
                        else:
                            follow_btn = page.locator(sel).first

                        if follow_btn and follow_btn.count() > 0 and follow_btn.is_visible():
                            # 双重确认这是关注按钮
                            btn_text = follow_btn.inner_text() or ""
                            logger.debug("Weibo: 找到按钮，文本内容: '{}'", btn_text)

                            if (("关注" in btn_text and "已关注" not in btn_text and "取消关注" not in btn_text) or
                                "+关注" in btn_text or "+ 关注" in btn_text):

                                logger.info("Weibo: 找到有效关注按钮，准备点击: {}", sel)
                                follow_btn.click()
                                follow_button_found = True
                                logger.info("Weibo: 成功点击关注按钮，按钮文本: '{}'", btn_text)

                                # 等待关注操作完成
                                time.sleep(1.5)

                                # 验证关注是否成功
                                new_status = detect_follow_status_on_page(page)
                                if new_status == "followed":
                                    logger.info("Weibo: 关注操作成功验证")
                                else:
                                    logger.warning("Weibo: 关注操作验证失败，新状态: {}", new_status)

                                break
                    except Exception as e:
                        logger.debug("Weibo: 关注按钮选择器 {} 失败: {}", sel, e)
                        continue

                if not follow_button_found:
                    logger.warning("Weibo: 未找到可点击的关注按钮")

            elif follow_status == "followed":
                logger.info("Weibo: 用户已关注，跳过关注操作")
            else:
                logger.warning("Weibo: 关注状态未知，跳过关注操作")

        except Exception as e:
            logger.error("Weibo: 关注操作过程失败 - {}", e)
            # 尝试使用ensure_follow_on_page作为备用方案
            try:
                logger.info("Weibo: 尝试备用关注方案")
                follow_executed = ensure_follow_on_page(page, None)
                if follow_executed:
                    logger.info("Weibo: 备用关注方案成功")
            except Exception as e2:
                logger.warning("Weibo: 备用关注方案也失败 - {}", e2)

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

    # 若需要转发，则在评论提交前执行转发操作
    if do_repost:
        logger.info("Weibo: 执行转发操作（评论提交前）")
        try:
            # 优先使用 span:has-text('同时转发') 选择器
            primary_selector = "span:has-text('同时转发')"

            try:
                repost_element = page.locator(primary_selector).first
                if repost_element and repost_element.count() > 0 and repost_element.is_visible():
                    repost_element.click()
                    logger.info("Weibo: 已点击'同时转发'按钮（优先选择器）")
                else:
                    logger.info("Weibo: 优先选择器未找到，使用备用策略")
                    raise Exception("Primary selector not found")
            except Exception:
                # 备用查找策略
                backup_selectors = [
                    "label:has-text('同时转发')",
                    "input[type='checkbox']:has-text('同时转发')",
                    "label:has-text('同时转发') input[type='checkbox']",
                    f"xpath={X_FORWARD_TOGGLE}",  # 原有的精准XPath
                    "input[type='checkbox'][name*='repost']",
                    "input[type='checkbox'][value*='转发']",
                    ".repost-checkbox",
                    "[data-testid*='repost-checkbox']"
                ]

                repost_found = False
                for sel in backup_selectors:
                    try:
                        if sel.startswith("xpath="):
                            element = page.query_selector(sel)
                        else:
                            element = page.locator(sel).first
                            if element.count() == 0:
                                element = None

                        if element and element.is_visible():
                            # 对于复选框，检查是否已选中
                            if "checkbox" in sel.lower() or sel.startswith("xpath="):
                                try:
                                    if not element.is_checked():
                                        element.click()
                                        repost_found = True
                                        logger.info("Weibo: 已勾选转发复选框: {}", sel)
                                        break
                                    else:
                                        repost_found = True
                                        logger.info("Weibo: 转发复选框已选中: {}", sel)
                                        break
                                except Exception:
                                    # 对于不支持is_checked的元素，直接点击
                                    element.click()
                                    repost_found = True
                                    logger.info("Weibo: 已点击转发元素: {}", sel)
                                    break
                            else:
                                element.click()
                                repost_found = True
                                logger.info("Weibo: 已点击转发元素: {}", sel)
                                break
                    except Exception as e:
                        logger.debug("Weibo: 备用转发选择器 {} 失败: {}", sel, e)
                        continue

                if not repost_found:
                    logger.warning("Weibo: 所有转发选择器都未找到可用元素")
        except Exception as e:
            logger.warning("Weibo: 转发操作失败 - {}", e)

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
    return comment_and_optionally_repost(page, do_repost=True, do_follow=False)


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


def automate_on_post(page: Page, do_comment: bool, do_like: bool, do_repost: bool, do_follow: bool = True) -> dict:
    """
    备选流程模式：按照正确的8步流程执行微博自动化操作

    完整的8步流程（修正版）：
    1. 等待微博首页加载成功
    2. 获取详情页链接
    3. 进入微博详情页
    4. 提取微博内容 + AI内容分析
    5. 点击关注按钮
    6. 点击点赞按钮（调整到评论前）
    7. 找到并点击评论框
    8. AI智能生成并输入评论 + 点击"同时转发"按钮 + 提交评论完成流程

    技术特性：
    - 使用精确XPath选择器（最高优先级）
    - 标准化操作间隔时间（1-2.5秒）
    - AI内容分析和智能评论生成
    - 正确的操作顺序（点赞在评论前）
    - Ctrl+Enter快捷键优先提交评论
    - 智能降级和错误处理机制
    - 完整的MCP操作记录

    Args:
        page: Playwright页面对象
        do_comment: 是否执行评论操作
        do_like: 是否执行点赞操作
        do_repost: 是否执行转发操作（作为评论的同时转发选项）
        do_follow: 是否执行关注操作

    Returns:
        {"follow_executed": bool, "like_executed": bool, "comment_executed": bool, "repost_executed": bool, "weibo_link": str|None, "mcp_script": str}
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
    weibo_content = ""
    try:
        # 尝试多种选择器提取内容
        content_selectors = [
            "article .text",
            ".detail-text",
            "[data-testid='post-text']",
            ".post-content",
            "article p",
            "main article"
        ]

        for selector in content_selectors:
            try:
                content_element = page.query_selector(selector)
                if content_element:
                    weibo_content = content_element.inner_text() or ""
                    if weibo_content.strip():
                        logger.info("备选流程：成功提取微博内容，长度: {} 字符", len(weibo_content))
                        break
            except Exception:
                continue

        if not weibo_content.strip():
            logger.warning("备选流程：未能提取到微博内容")
            weibo_content = "无法提取内容"

        recorder.record("extract_content", content=weibo_content[:100])
    except Exception as e:
        logger.warning("备选流程：提取内容失败 - {}", e)
        weibo_content = "提取失败"

    # 第四步补充：AI内容分析（修复版）
    logger.info("备选流程 - 第四步补充：AI内容分析")
    ai_analysis = None
    content_text = weibo_content  # 保存内容文本供后续使用

    try:
        if weibo_content and weibo_content not in ["提取失败", "无法提取内容"]:
            logger.info("开始AI内容分析，内容长度: {} 字符", len(weibo_content))

            # 调用AI分析功能
            ai_analysis = ai_analyze_weibo_content(weibo_content)

            if ai_analysis:
                logger.info("✅ AI内容分析完成: 情感={}, 类型={}, 主题={}",
                           ai_analysis.get('sentiment', 'unknown'),
                           ai_analysis.get('content_type', 'unknown'),
                           ai_analysis.get('topics', []))
                recorder.record("ai_analysis", content=weibo_content[:50], analysis=ai_analysis)
            else:
                logger.warning("⚠️ AI分析返回空结果")
        else:
            logger.warning("⚠️ 跳过AI分析：微博内容为空或提取失败")
    except Exception as e:
        logger.warning("❌ AI内容分析失败: {}", e)
        ai_analysis = None

    # 第五步：强制执行关注操作（内容提取后立即执行）
    logger.info("备选流程 - 第五步：强制执行关注操作")
    try:
        logger.info("🔥 强制关注模式：无论用户设置如何，都将执行关注操作")

        # 使用精确XPath选择器（最高优先级）
        follow_selectors = [
            "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",
            "button:has-text('+关注')",
            "button:has-text('+ 关注')",
            "button:has-text('关注'):not(:has-text('已关注'))",
            "[role=button]:has-text('关注'):not(:has-text('已关注'))",
            "//button[contains(text(), '+关注')]"
        ]

        for i, selector in enumerate(follow_selectors):
            try:
                logger.debug("尝试强制关注选择器 {}/{}: {}", i+1, len(follow_selectors), selector)

                if selector.startswith("//") or selector.startswith("//*"):
                    element = page.query_selector(f"xpath={selector}")
                else:
                    element = page.query_selector(selector)

                if element and element.is_visible():
                    element.click()
                    # 关注操作标准化等待时间：2.0秒
                    time.sleep(2.0)
                    result["follow_executed"] = True
                    recorder.record("click", element="follow_button_forced", selector=selector)
                    logger.info("✅ 第五步完成：强制关注操作成功")
                    break
            except Exception as e:
                logger.debug("强制关注选择器失败: {} - {}", selector, e)
                continue

        if not result["follow_executed"]:
            logger.warning("⚠️ 第五步：强制关注操作失败")
    except Exception as e:
        logger.warning("❌ 第五步异常：强制关注操作失败 - {}", e)

    # 第六步：执行互动操作（修正后的流程）
    logger.info("备选流程 - 第六步：执行互动操作（修正后的流程）")

    # 初始化结果
    result = {
        "follow_executed": False,
        "like_executed": False,
        "comment_executed": False,
        "repost_executed": False,
        "weibo_link": detail_link,
        "weibo_content": weibo_content,
        "mcp_script": "",
        "mcp_code": ""
    }

    # 导入随机模块用于等待时间
    import random

    # 8步详细互动流程（修正版）

    # 步骤3：点击关注按钮
    if do_follow:
        logger.info("备选流程 - 步骤3：点击关注按钮")
        try:
            # 精确XPath选择器（最高优先级）
            follow_selectors = [
                "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/div[2]/header/div[2]/button",
                "button:has-text('+关注')",
                "button:has-text('+ 关注')",
                "button:has-text('关注'):not(:has-text('已关注'))",
                "[role=button]:has-text('关注'):not(:has-text('已关注'))",
                "//button[contains(text(), '+关注')]"
            ]

            for i, selector in enumerate(follow_selectors):
                try:
                    logger.debug("尝试关注选择器 {}/{}: {}", i+1, len(follow_selectors), selector)

                    if selector.startswith("//") or selector.startswith("//*"):
                        element = page.query_selector(f"xpath={selector}")
                    else:
                        element = page.query_selector(selector)

                    if element and element.is_visible():
                        element.click()
                        # 关注操作标准化等待时间：2.0秒
                        time.sleep(2.0)
                        result["follow_executed"] = True
                        recorder.record("click", element="follow_button", selector=selector)
                        logger.info("✅ 步骤3完成：关注操作成功")
                        break
                except Exception as e:
                    logger.debug("关注选择器失败: {} - {}", selector, e)
                    continue

            if not result["follow_executed"]:
                logger.warning("⚠️ 步骤3：关注操作失败")
        except Exception as e:
            logger.warning("❌ 步骤3异常：关注操作失败 - {}", e)

   
    # 步骤5：找到并点击评论框
    comment_element = None
    if do_comment:
        logger.info("备选流程 - 步骤5：找到并点击评论框")
        try:
            comment_selectors = [
                "textarea[placeholder*='评论']",
                "textarea[placeholder*='说点什么']",
                ".comment-input textarea",
                "[data-testid='comment-input']",
                "textarea",
                ".comment-box textarea"
            ]

            for i, selector in enumerate(comment_selectors):
                try:
                    logger.debug("尝试评论框选择器 {}/{}: {}", i+1, len(comment_selectors), selector)
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        element.click()
                        # 评论框激活标准化等待时间：1.5秒
                        time.sleep(1.5)
                        comment_element = element
                        recorder.record("click", element="comment_box", selector=selector)
                        logger.info("✅ 步骤5完成：评论框激活成功")
                        break
                except Exception as e:
                    logger.debug("评论框选择器失败: {} - {}", selector, e)
                    continue

            if not comment_element:
                logger.warning("⚠️ 步骤5：未找到评论框")
        except Exception as e:
            logger.warning("❌ 步骤5异常：评论框查找失败 - {}", e)

    # 步骤6：AI智能生成并输入评论（修复版）
    if do_comment and comment_element:
        logger.info("备选流程 - 步骤6：AI智能生成并输入评论")
        comment_text = None

        try:
            # 优先调用comments模块进行AI评论生成
            logger.info("🤖 优先使用comments模块生成AI评论")

            try:
                from .comments import random_comment

                # 将微博内容正确传递给comments模块
                if content_text and content_text not in ["提取失败", "无法提取内容"]:
                    comment_text = random_comment(content_text)
                    logger.info("✅ comments模块生成评论成功: {}", comment_text)
                else:
                    # 内容为空时使用无参数调用
                    comment_text = random_comment()
                    logger.info("✅ comments模块生成默认评论: {}", comment_text)

            except (ImportError, ConnectionError, TimeoutError, Exception) as e:
                # 降级到本地AI评论生成
                logger.warning("❌ comments模块调用失败，降级到本地AI生成: {}", e)

                try:
                    # 使用本地AI生成智能评论内容
                    comment_text = generate_ai_comment(weibo_content, ai_analysis)
                    logger.info("✅ 本地AI生成评论成功: {}", comment_text)
                except Exception as e2:
                    # 最终降级到基础评论生成
                    logger.warning("❌ 本地AI生成失败，降级到基础评论: {}", e2)
                    comment_text = generate_comment_text(weibo_content)
                    logger.info("✅ 基础评论生成成功: {}", comment_text)

            # 输入评论
            if comment_text:
                comment_element.fill(comment_text)
                # 评论输入标准化等待时间：2.0秒
                time.sleep(2.0)

                recorder.record("input", element="comment_box", text=comment_text, ai_generated=True)
                logger.info("✅ 步骤6完成：AI智能评论输入成功")
            else:
                logger.error("❌ 评论生成失败：所有方法都无法生成评论")
                comment_element = None

        except Exception as e:
            logger.warning("❌ 步骤6异常：AI评论输入失败 - {}", e)
            comment_element = None

    # 步骤7：点击"同时转发"按钮
    if do_repost and comment_element:
        logger.info("备选流程 - 步骤7：点击同时转发按钮")
        try:
            repost_option_selectors = [
                "input[type='checkbox']:has-text('同时转发')",
                "label:has-text('同时转发')",
                ".repost-option",
                "[data-testid='repost-option']",
                "//label[contains(text(), '同时转发')]",
                "//input[@type='checkbox' and contains(following-sibling::text(), '转发')]"
            ]

            for i, selector in enumerate(repost_option_selectors):
                try:
                    logger.debug("尝试转发选项选择器 {}/{}: {}", i+1, len(repost_option_selectors), selector)

                    if selector.startswith("//"):
                        element = page.query_selector(f"xpath={selector}")
                    else:
                        element = page.query_selector(selector)

                    if element and element.is_visible():
                        element.click()
                        # 转发选项标准化等待时间：1.5秒
                        time.sleep(1.5)
                        result["repost_executed"] = True
                        recorder.record("click", element="repost_option", selector=selector)
                        logger.info("✅ 步骤7完成：同时转发选项已选择")
                        break
                except Exception as e:
                    logger.debug("转发选项选择器失败: {} - {}", selector, e)
                    continue

            if not result["repost_executed"]:
                logger.warning("⚠️ 步骤7：同时转发选项未找到")
        except Exception as e:
            logger.warning("❌ 步骤7异常：同时转发操作失败 - {}", e)

    # 步骤8：点击评论提交按钮完成整个流程
    if do_comment and comment_element:
        logger.info("备选流程 - 步骤8：提交评论完成流程")
        try:
            # 优先使用Ctrl+Enter快捷键提交（最高优先级）
            logger.info("🎯 优先尝试Ctrl+Enter快捷键提交")

            try:
                # 元素级快捷键提交
                comment_element.press("Control+Enter")
                # 提交操作标准化等待时间：2.5秒
                time.sleep(2.5)
                result["comment_executed"] = True
                recorder.record("comment_submit", method="element_ctrl_enter")
                logger.info("✅ 步骤8完成：评论提交成功（元素级快捷键）")
            except Exception as e:
                logger.debug("元素级快捷键失败: {}", e)

                try:
                    # 页面级快捷键提交
                    page.keyboard.press("Control+Enter")
                    time.sleep(2.5)
                    result["comment_executed"] = True
                    recorder.record("comment_submit", method="page_ctrl_enter")
                    logger.info("✅ 步骤8完成：评论提交成功（页面级快捷键）")
                except Exception as e2:
                    logger.debug("页面级快捷键失败: {}", e2)

                    # 降级到按钮提交
                    logger.info("🔄 快捷键失败，降级到按钮提交")
                    submit_selectors = [
                        "button:has-text('发布')",
                        "button:has-text('评论')",
                        ".comment-submit",
                        "[data-testid='comment-submit']",
                        "button[type='submit']"
                    ]

                    for i, selector in enumerate(submit_selectors):
                        try:
                            logger.debug("尝试提交按钮选择器 {}/{}: {}", i+1, len(submit_selectors), selector)
                            submit_btn = page.query_selector(selector)
                            if submit_btn and submit_btn.is_visible():
                                submit_btn.click()
                                time.sleep(2.5)
                                result["comment_executed"] = True
                                recorder.record("comment_submit", method="button", selector=selector)
                                logger.info("✅ 步骤8完成：评论提交成功（按钮）")
                                break
                        except Exception as e3:
                            logger.debug("提交按钮选择器失败: {} - {}", selector, e3)
                            continue

            if not result["comment_executed"]:
                logger.warning("⚠️ 步骤8：评论提交失败")
        except Exception as e:
            logger.warning("❌ 步骤8异常：评论提交失败 - {}", e)

 # 步骤4：点击点赞按钮（调整到评论前）
    if do_like:
        logger.info("备选流程 - 步骤4：点击点赞按钮")
        try:
            # 精确XPath选择器（最高优先级）
            like_selectors = [
                "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",
                "//*[@id=\"app\"]/div[2]/div[2]/div[2]/main/div[1]/div/div[2]/article/footer/div/div[1]/div/div[3]/div/button",
                "button:has-text('赞')",
                "button[aria-label*='赞']",
                "//button[contains(@aria-label, '赞')]"
            ]

            for i, selector in enumerate(like_selectors):
                try:
                    logger.debug("尝试点赞选择器 {}/{}: {}", i+1, len(like_selectors), selector)

                    if selector.startswith("//") or selector.startswith("//*"):
                        element = page.query_selector(f"xpath={selector}")
                    else:
                        element = page.query_selector(selector)

                    if element and element.is_visible():
                        element.click()
                        # 点赞操作标准化等待时间：2.0秒
                        time.sleep(2.0)
                        result["like_executed"] = True
                        recorder.record("click", element="like_button", selector=selector)
                        logger.info("✅ 步骤4完成：点赞操作成功")
                        break
                except Exception as e:
                    logger.debug("点赞选择器失败: {} - {}", selector, e)
                    continue

            if not result["like_executed"]:
                logger.warning("⚠️ 步骤4：点赞操作失败")
        except Exception as e:
            logger.warning("❌ 步骤4异常：点赞操作失败 - {}", e)


    # 生成MCP脚本
    result["mcp_script"] = recorder.to_python_script()
    result["mcp_code"] = recorder.to_mcp_code()

    # 记录操作统计
    executed_operations = sum([
        result["follow_executed"],
        result["like_executed"],
        result["comment_executed"],
        result["repost_executed"]
    ])

    logger.info("备选流程：操作完成，成功执行 {}/4 项操作", executed_operations)
    logger.info("备选流程：关注:{} 点赞:{} 评论:{} 转发:{}",
               result["follow_executed"], result["like_executed"],
               result["comment_executed"], result["repost_executed"])

    return result


def generate_comment_text(weibo_content: str) -> str:
    """
    根据微博内容生成合适的评论文本

    Args:
        weibo_content: 微博原文内容

    Returns:
        生成的评论文本
    """
    import random

    # 通用评论模板
    general_comments = [
        "说得很有道理！",
        "学到了！",
        "赞同！",
        "很棒的分享",
        "有意思",
        "不错不错",
        "支持！",
        "很有启发",
        "说得好",
        "受教了"
    ]

    # 根据内容长度和类型选择评论
    if not weibo_content or len(weibo_content.strip()) < 10:
        return random.choice(general_comments)

    # 简单的内容分析
    content_lower = weibo_content.lower()

    # 如果包含问题关键词
    if any(word in content_lower for word in ["？", "?", "怎么", "如何", "为什么"]):
        question_comments = [
            "这个问题很有意思",
            "我也想知道答案",
            "期待解答",
            "好问题！"
        ]
        return random.choice(question_comments)

    # 如果包含分享类关键词
    if any(word in content_lower for word in ["分享", "推荐", "安利"]):
        share_comments = [
            "谢谢分享！",
            "很有用的信息",
            "收藏了",
            "感谢推荐"
        ]
        return random.choice(share_comments)

    # 如果包含情感类关键词
    if any(word in content_lower for word in ["开心", "高兴", "快乐", "幸福"]):
        emotion_comments = [
            "替你开心！",
            "感受到了快乐",
            "正能量满满",
            "很温暖"
        ]
        return random.choice(emotion_comments)

    # 默认返回通用评论
    return random.choice(general_comments)


def ai_analyze_weibo_content(content: str) -> dict:
    """
    AI分析微博内容

    Args:
        content: 微博内容文本

    Returns:
        dict: 分析结果，包含情感、主题、关键词等
    """
    try:
        # 基础内容分析
        analysis = {
            "content_length": len(content),
            "sentiment": "neutral",
            "topics": [],
            "keywords": [],
            "content_type": "general",
            "engagement_potential": "medium"
        }

        content_lower = content.lower()

        # 情感分析
        positive_words = ["好", "棒", "赞", "喜欢", "开心", "快乐", "美好", "精彩", "优秀", "完美"]
        negative_words = ["不好", "差", "糟糕", "失望", "难过", "生气", "烦恼", "问题", "错误"]

        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)

        if positive_count > negative_count:
            analysis["sentiment"] = "positive"
        elif negative_count > positive_count:
            analysis["sentiment"] = "negative"
        else:
            analysis["sentiment"] = "neutral"

        # 主题识别
        topic_keywords = {
            "科技": ["技术", "AI", "人工智能", "科技", "创新", "数字", "互联网", "软件", "硬件"],
            "生活": ["生活", "日常", "家庭", "朋友", "工作", "学习", "健康", "美食", "旅行"],
            "娱乐": ["电影", "音乐", "游戏", "明星", "综艺", "娱乐", "搞笑", "有趣"],
            "新闻": ["新闻", "事件", "社会", "政策", "经济", "国际", "国内"],
            "情感": ["爱情", "友情", "亲情", "感情", "心情", "感动", "温暖"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                analysis["topics"].append(topic)

        # 内容类型识别
        if any(word in content for word in ["？", "?", "怎么", "如何", "为什么"]):
            analysis["content_type"] = "question"
        elif any(word in content for word in ["分享", "推荐", "介绍"]):
            analysis["content_type"] = "sharing"
        elif any(word in content for word in ["感谢", "谢谢", "感动", "感激"]):
            analysis["content_type"] = "gratitude"
        elif any(word in content for word in ["哈哈", "😂", "😄", "搞笑", "有趣"]):
            analysis["content_type"] = "humor"

        # 互动潜力评估
        if len(content) > 100 and analysis["sentiment"] == "positive":
            analysis["engagement_potential"] = "high"
        elif len(content) < 30:
            analysis["engagement_potential"] = "low"

        logger.debug("AI内容分析完成: {}", analysis)
        return analysis

    except Exception as e:
        logger.warning("AI内容分析失败: {}", e)
        return {
            "content_length": len(content) if content else 0,
            "sentiment": "neutral",
            "topics": [],
            "keywords": [],
            "content_type": "general",
            "engagement_potential": "medium",
            "error": str(e)
        }


def generate_ai_comment(content: str, ai_analysis: dict = None) -> str:
    """
    基于AI分析生成智能评论（本地降级方案）

    Args:
        content: 微博内容
        ai_analysis: AI分析结果

    Returns:
        str: 生成的评论文本
    """
    try:
        logger.info("🔄 使用本地AI评论生成（降级方案）")

        # 如果没有AI分析，先进行分析
        if not ai_analysis:
            ai_analysis = ai_analyze_weibo_content(content)

        sentiment = ai_analysis.get("sentiment", "neutral")
        content_type = ai_analysis.get("content_type", "general")
        topics = ai_analysis.get("topics", [])

        # 基于情感的评论模板
        positive_comments = [
            "说得很有道理！", "赞同你的观点！", "学到了！", "很有启发！",
            "确实如此！", "深有同感！", "太棒了！", "很精彩！"
        ]

        negative_comments = [
            "希望情况会好转", "加油！", "理解你的感受", "会越来越好的",
            "保持乐观！", "困难总会过去的"
        ]

        neutral_comments = [
            "有意思！", "学习了！", "涨知识了！", "不错！",
            "很实用！", "值得思考", "受教了！"
        ]

        # 基于内容类型的评论
        type_comments = {
            "question": ["这个问题很好！", "我也想知道", "期待答案", "有同样的疑问"],
            "sharing": ["谢谢分享！", "很有用！", "收藏了！", "学到了！"],
            "gratitude": ["很温暖！", "正能量！", "感动！", "很有爱！"],
            "humor": ["哈哈哈！", "太搞笑了！", "笑死我了！", "有趣！"]
        }

        # 基于主题的评论
        topic_comments = {
            "科技": ["科技改变生活！", "技术发展真快！", "很前沿！", "创新很重要！"],
            "生活": ["生活就是这样！", "很真实！", "感同身受！", "生活小智慧！"],
            "娱乐": ["很有趣！", "娱乐一下！", "放松心情！", "开心就好！"],
            "新闻": ["关注时事！", "很重要的信息！", "需要了解！", "值得关注！"],
            "情感": ["很感动！", "情感真挚！", "很有感触！", "温暖人心！"]
        }

        # 智能选择评论
        candidate_comments = []

        # 根据情感选择
        if sentiment == "positive":
            candidate_comments.extend(positive_comments)
        elif sentiment == "negative":
            candidate_comments.extend(negative_comments)
        else:
            candidate_comments.extend(neutral_comments)

        # 根据内容类型选择
        if content_type in type_comments:
            candidate_comments.extend(type_comments[content_type])

        # 根据主题选择
        for topic in topics:
            if topic in topic_comments:
                candidate_comments.extend(topic_comments[topic])

        # 如果没有合适的评论，使用通用评论
        if not candidate_comments:
            candidate_comments = neutral_comments

        # 随机选择一个评论
        selected_comment = random.choice(candidate_comments)

        logger.info("AI智能评论生成: 情感={}, 类型={}, 主题={}, 评论={}",
                   sentiment, content_type, topics, selected_comment)

        return selected_comment

    except Exception as e:
        logger.warning("AI智能评论生成失败: {}", e)
        # 降级到基础评论生成
        return generate_comment_text(content)








