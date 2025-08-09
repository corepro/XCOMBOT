from __future__ import annotations
import threading
import time
from queue import SimpleQueue, Empty
import ttkbootstrap as tb
from ttkbootstrap.constants import LEFT, RIGHT, BOTH, X, Y, YES, W, END, DISABLED, NORMAL, PRIMARY, SECONDARY, SUCCESS, INFO, DANGER, WARNING, HORIZONTAL
from ttkbootstrap.scrolled import ScrolledText
from tkinter import filedialog as fd
import os, sys, subprocess
from .logger import attach_ui_queue, logger
from .config import CONFIG
from .run_tasks import (
    run_monitor_loop, STOP_EVENT, comment_once, like_once, retweet_once, run_follow_once,
    process_links, run_random_batch, xhs_comment_once, xhs_like_once, xhs_collect_once, xhs_share_once, xhs_follow_once,
    zhihu_comment_once, zhihu_like_once, zhihu_collect_once, zhihu_follow_once,
    toutiao_comment_once, toutiao_like_once, toutiao_collect_once, toutiao_follow_once
)
from .browser import BrowserManager
from .login import login_flow
from .login_weibo import ensure_login_weibo
from .login_xhs import ensure_login_xhs, ensure_login_xhs_with_save
from .login_zhihu import ensure_login_zhihu, ensure_login_zhihu_with_save
from .login_toutiao import ensure_login_toutiao, ensure_login_toutiao_with_save



class AppUIBoot:
    """更现代化的 ttkbootstrap 界面

    结构：
    - 顶部导航（标题、搜索、头像占位）
    - 左侧导航（占位）
    - 内容区（左：控制卡片 + 日志，右：配置）
    - 底部状态统计
    """

    def __init__(self):
        self.app = tb.Window(themename="cosmo")
        self.app.title("XComBot - 控制台")
        self.app.geometry("1200x720")

        # 先创建与顶部相关的变量（平台/模式）
        self.var_platform = tb.StringVar(value=getattr(CONFIG, "platform", "twitter"))
        self.var_mode = tb.StringVar(value=CONFIG.comment.mode)

        # 顶部导航条（放置 平台/模式 固定位置）
        top = tb.Frame(self.app, padding=(14, 10))
        top.pack(fill=X)
        tb.Label(top, text="XComBot", font=("Segoe UI", 14, "bold")).pack(side=LEFT)
        # 平台/模式固定在顶部工具条
        tb.Label(top, text="平台:").pack(side=LEFT, padx=(16,4))
        platform_menu = tb.OptionMenu(top, self.var_platform, "twitter", "weibo", "xhs", "zhihu", "toutiao")
        platform_menu.pack(side=LEFT)

        # 当主平台选择改变时，同步更新评论模板平台选择
        def _on_main_platform_change(*_):
            try:
                selected_platform = self.var_platform.get()
                # 同步模板平台选择器
                if hasattr(self, 'var_template_platform'):
                    self.var_template_platform.set(selected_platform)
                    # 触发模板更新
                    if hasattr(self, 'txt_prompt'):
                        platform_templates = getattr(CONFIG.comment, "platform_templates", {})
                        template = platform_templates.get(selected_platform, CONFIG.comment.prompt_template)
                        self.txt_prompt.delete("1.0", END)
                        self.txt_prompt.insert(END, template)
                        logger.info("已同步切换到 {} 平台的评论模板", selected_platform.upper())
            except Exception as e:
                logger.warning("同步平台选择失败：{}", e)

        self.var_platform.trace("w", _on_main_platform_change)

        tb.Label(top, text="模式:").pack(side=LEFT, padx=(12,4))
        tb.OptionMenu(top, self.var_mode, "local", "ai").pack(side=LEFT)
        # 占位搜索框
        search = tb.Entry(top, width=28)
        search.insert(0, "搜索…(占位)")
        search.pack(side=LEFT, padx=14)
        # 登录/退出按钮区
        top_actions = tb.Frame(top)
        top_actions.pack(side=RIGHT)
        tb.Button(top_actions, text="退出", bootstyle=DANGER, command=self.logout_account).pack(side=RIGHT, padx=6)
        tb.Button(top_actions, text="登录", bootstyle=SECONDARY, command=self.login_account).pack(side=RIGHT)

        # 主体：左侧边栏 + 内容
        body = tb.Frame(self.app)
        body.pack(fill=BOTH, expand=YES)

        # 左侧导航
        sidebar = tb.Frame(body, padding=10)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)
        sidebar.configure(width=180)

        self._nav_active = None
        self._nav_buttons = {}

        def add_nav(text: str):
            btn = tb.Button(sidebar, text=text, bootstyle=(PRIMARY if not self._nav_buttons else SECONDARY), width=16)
            btn.pack(fill=X, pady=4)
            self._nav_buttons[text] = btn
            if self._nav_active is None:
                self._nav_active = text
            def on_click():
                self._set_nav_active(text)
            btn.configure(command=on_click)

        add_nav("监控台")
        add_nav("机器人管理")
        add_nav("监控配置")
        add_nav("日志查看")

        # 内容区（左右两栏）
        content = tb.Frame(body, padding=10)
        content.pack(side=LEFT, fill=BOTH, expand=YES)

        # 左侧：控制卡片 + 日志
        left_col = tb.Frame(content)
        left_col.pack(side=LEFT, fill=BOTH, expand=YES)

        # 控制卡片
        card = tb.Labelframe(left_col, text="控制面板", padding=10)
        card.pack(fill=X)

        self.btn_start = tb.Button(card, text="开始监控", bootstyle=SUCCESS, command=self.start_loop)
        self.btn_stop = tb.Button(card, text="停止监控", bootstyle=DANGER, state=DISABLED, command=self.stop_loop)
        self.btn_start.pack(side=LEFT, padx=6, pady=2)
        self.btn_stop.pack(side=LEFT, padx=6, pady=2)

        # 一次性动作快捷键 - 第一行（通用）
        actions_row1 = tb.Frame(card)
        actions_row1.pack(fill=X, pady=2)
        tb.Button(actions_row1, text="评1次", bootstyle=PRIMARY, command=lambda: threading.Thread(target=self._run_comment_once, daemon=True).start()).pack(side=LEFT, padx=4)
        tb.Button(actions_row1, text="赞1次", bootstyle=WARNING, command=lambda: threading.Thread(target=self._run_like_once, daemon=True).start()).pack(side=LEFT, padx=4)
        tb.Button(actions_row1, text="转1次", bootstyle=INFO, command=lambda: threading.Thread(target=self._run_retweet_once, daemon=True).start()).pack(side=LEFT, padx=4)
        tb.Button(actions_row1, text="关1次", bootstyle=SECONDARY, command=lambda: threading.Thread(target=self._run_follow_once, daemon=True).start()).pack(side=LEFT, padx=4)

        # 一次性动作快捷键 - 第二行（小红书专用）
        actions_row2 = tb.Frame(card)
        actions_row2.pack(fill=X, pady=2)
        tb.Label(actions_row2, text="小红书:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=4)
        tb.Button(actions_row2, text="XHS评论", bootstyle="primary-outline", command=lambda: threading.Thread(target=self._run_xhs_comment_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row2, text="XHS点赞", bootstyle="warning-outline", command=lambda: threading.Thread(target=self._run_xhs_like_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row2, text="XHS收藏", bootstyle="success-outline", command=lambda: threading.Thread(target=self._run_xhs_collect_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row2, text="XHS分享", bootstyle="info-outline", command=lambda: threading.Thread(target=self._run_xhs_share_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row2, text="XHS关注", bootstyle="secondary-outline", command=lambda: threading.Thread(target=self._run_xhs_follow_once, daemon=True).start()).pack(side=LEFT, padx=2)

        # 一次性动作快捷键 - 第三行（知乎专用）
        actions_row3 = tb.Frame(card)
        actions_row3.pack(fill=X, pady=2)
        tb.Label(actions_row3, text="知乎:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=4)
        tb.Button(actions_row3, text="知乎评论", bootstyle="primary-outline", command=lambda: threading.Thread(target=self._run_zhihu_comment_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row3, text="知乎点赞", bootstyle="warning-outline", command=lambda: threading.Thread(target=self._run_zhihu_like_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row3, text="知乎收藏", bootstyle="success-outline", command=lambda: threading.Thread(target=self._run_zhihu_collect_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row3, text="知乎关注", bootstyle="secondary-outline", command=lambda: threading.Thread(target=self._run_zhihu_follow_once, daemon=True).start()).pack(side=LEFT, padx=2)

        # 一次性动作快捷键 - 第四行（今日头条专用）
        actions_row4 = tb.Frame(card)
        actions_row4.pack(fill=X, pady=2)
        tb.Label(actions_row4, text="头条:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=4)
        tb.Button(actions_row4, text="头条评论", bootstyle="primary-outline", command=lambda: threading.Thread(target=self._run_toutiao_comment_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row4, text="头条点赞", bootstyle="warning-outline", command=lambda: threading.Thread(target=self._run_toutiao_like_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row4, text="头条收藏", bootstyle="success-outline", command=lambda: threading.Thread(target=self._run_toutiao_collect_once, daemon=True).start()).pack(side=LEFT, padx=2)
        tb.Button(actions_row4, text="头条关注", bootstyle="secondary-outline", command=lambda: threading.Thread(target=self._run_toutiao_follow_once, daemon=True).start()).pack(side=LEFT, padx=2)
        self.lbl_status = tb.Label(card, text="状态：空闲", bootstyle=INFO)
        self.lbl_status.pack(side=LEFT, padx=12)

        # 日志
        log_box = tb.Labelframe(left_col, text="运行日志", padding=8)
        log_box.pack(fill=BOTH, expand=YES, pady=(10, 0))
        self.queue: SimpleQueue[str] = SimpleQueue()
        attach_ui_queue(self.queue)
        self.log = ScrolledText(log_box, height=24, autohide=True)
        self.log.pack(fill=BOTH, expand=YES)

        # 右侧：配置
        right = tb.Labelframe(content, text="配置", padding=10)
        right.pack(side=LEFT, fill=Y, padx=(10, 0))

        # 绑定变量（其余）
        self.var_comment = tb.BooleanVar(value=CONFIG.action.do_comment)
        self.var_like = tb.BooleanVar(value=getattr(CONFIG.action, "do_like", True))
        self.var_rt = tb.BooleanVar(value=CONFIG.action.do_retweet)
        self.var_follow = tb.BooleanVar(value=getattr(CONFIG.action, "do_follow", True))
        self.var_collect = tb.BooleanVar(value=getattr(CONFIG.action, "do_collect", True))
        self.var_interval = tb.IntVar(value=CONFIG.poll_interval_sec)
        self.var_max_cmt = tb.IntVar(value=CONFIG.action.max_comments_per_hour)
        self.var_max_rt = tb.IntVar(value=CONFIG.action.max_retweets_per_hour)
        self.var_proxy = tb.StringVar(value=CONFIG.proxy or "")
        self.var_slowmo = tb.IntVar(value=CONFIG.slow_mo_ms)

        # 反爬虫配置变量
        self.var_anti_detection = tb.StringVar(value=getattr(CONFIG, "anti_detection_mode", "off"))

        form = tb.Frame(right)
        form.pack(fill=Y)

        def row(label, widget):
            r = tb.Frame(form)
            r.pack(fill=X, pady=6)
            tb.Label(r, text=label, width=14, anchor=W).pack(side=LEFT)
            # 固定位置：用 Frame 容器承载控件，避免下拉溢出导致错位
            holder = tb.Frame(r, width=220)
            holder.pack_propagate(False)
            holder.pack(side=LEFT)
            widget.master = holder
            widget.pack(side=LEFT)
            return r

        # 平台/模式已移到顶部工具条
        ai_box = tb.Labelframe(form, text="AI配置", padding=6); ai_box.pack(fill=X)

        # API Key 行
        key_row = tb.Frame(ai_box); key_row.pack(fill=X, pady=2)
        tb.Label(key_row, text="API Key:", width=10, anchor=W).pack(side=LEFT)
        self.var_ai_key = tb.StringVar(value=CONFIG.comment.hf_api_key or "")
        ent_key = tb.Entry(key_row, textvariable=self.var_ai_key, width=30, show="*")
        ent_key.pack(side=LEFT, padx=6)

        # AI 模型选择行
        model_row = tb.Frame(ai_box); model_row.pack(fill=X, pady=2)
        tb.Label(model_row, text="AI 模型:", width=10, anchor=W).pack(side=LEFT)
        self.var_ai_model = tb.StringVar(value=getattr(CONFIG.comment, "model", "Qwen/QwQ-32B"))
        model_combo = tb.Combobox(model_row, textvariable=self.var_ai_model,
                                 values=["Qwen/QwQ-32B", "deepseek-ai/DeepSeek-V3", "gpt-3.5-turbo", "gpt-4"],
                                 width=25, state="readonly")
        model_combo.pack(side=LEFT, padx=6)

        # AI 参数行
        params_row = tb.Frame(ai_box); params_row.pack(fill=X, pady=2)

        # 温度参数
        tb.Label(params_row, text="温度:", width=6, anchor=W).pack(side=LEFT)
        self.var_ai_temperature = tb.DoubleVar(value=getattr(CONFIG.comment, "temperature", 0.8))
        temp_scale = tb.Scale(params_row, variable=self.var_ai_temperature, from_=0.1, to=2.0,
                             length=80, bootstyle=INFO, orient="horizontal")
        temp_scale.pack(side=LEFT, padx=(4,5))
        temp_label = tb.Label(params_row, text="0.8", width=4)
        temp_label.pack(side=LEFT, padx=(0,10))

        # 最大令牌数
        tb.Label(params_row, text="最大令牌:", width=8, anchor=W).pack(side=LEFT)
        self.var_ai_max_tokens = tb.IntVar(value=getattr(CONFIG.comment, "max_tokens", 200))
        tb.Entry(params_row, textvariable=self.var_ai_max_tokens, width=8).pack(side=LEFT, padx=(4,0))

        # 温度值实时更新
        def _update_temp_label(*_):
            temp_label.configure(text=f"{self.var_ai_temperature.get():.1f}")
        self.var_ai_temperature.trace("w", _update_temp_label)
        # 实时保存 AI 配置
        def _save_ai_config(*_):
            try:
                CONFIG.comment.hf_api_key = (self.var_ai_key.get() or "").strip()
                CONFIG.comment.model = self.var_ai_model.get()
                CONFIG.comment.temperature = float(self.var_ai_temperature.get())
                CONFIG.comment.max_tokens = int(self.var_ai_max_tokens.get())
                CONFIG.save()
                logger.info("AI 配置已自动保存。")
            except Exception as e:
                logger.warning("保存 AI 配置失败：{}", e)

        # 绑定保存事件
        ent_key.bind("<FocusOut>", _save_ai_config)
        ent_key.bind("<Return>", _save_ai_config)
        model_combo.bind("<<ComboboxSelected>>", _save_ai_config)
        self.var_ai_temperature.trace("w", _save_ai_config)
        self.var_ai_max_tokens.trace("w", _save_ai_config)

        # 评论风格模版（多行可编辑）
        prompt_box = tb.Labelframe(form, text="评论风格模版（使用 {content} 作为内容占位）", padding=6); prompt_box.pack(fill=X, pady=(6,0))

        # 平台模板选择
        template_frame = tb.Frame(prompt_box)
        template_frame.pack(fill=X, pady=(0, 5))
        tb.Label(template_frame, text="模板:").pack(side=LEFT, padx=(0, 5))

        self.var_template_platform = tb.StringVar(value=CONFIG.platform)
        template_combo = tb.Combobox(template_frame, textvariable=self.var_template_platform,
                                   values=["weibo", "xhs", "zhihu", "toutiao", "twitter"],
                                   state="readonly", width=10)
        template_combo.pack(side=LEFT, padx=(0, 10))

        # 获取当前平台的默认模板
        current_platform = CONFIG.platform
        platform_templates = getattr(CONFIG.comment, "platform_templates", {})
        default_prompt = platform_templates.get(current_platform, CONFIG.comment.prompt_template)

        self.txt_prompt = ScrolledText(prompt_box, height=3, autohide=True)
        self.txt_prompt.pack(fill=X)
        self.txt_prompt.insert(END, default_prompt)

        # 当平台选择改变时，更新模板
        def _on_template_platform_change(*_):
            try:
                selected_platform = self.var_template_platform.get()
                platform_templates = getattr(CONFIG.comment, "platform_templates", {})
                template = platform_templates.get(selected_platform, CONFIG.comment.prompt_template)

                # 清空并插入新模板
                self.txt_prompt.delete("1.0", END)
                self.txt_prompt.insert(END, template)
                logger.info("已切换到 {} 平台的评论模板", selected_platform.upper())
            except Exception as e:
                logger.warning("切换评论模板失败：{}", e)

        template_combo.bind("<<ComboboxSelected>>", _on_template_platform_change)
        # 实时保存模版（失焦）
        def _save_tpl(*_):
            try:
                current_template_platform = self.var_template_platform.get()
                template_content = self.txt_prompt.get("1.0", END).strip()

                # 确保platform_templates存在
                if not hasattr(CONFIG.comment, "platform_templates"):
                    CONFIG.comment.platform_templates = {}

                # 保存到对应平台的模板
                CONFIG.comment.platform_templates[current_template_platform] = template_content

                # 如果是当前选择的平台，也更新默认模板
                if current_template_platform == CONFIG.platform:
                    CONFIG.comment.prompt_template = template_content

                CONFIG.save()
                logger.info("AI模版已自动保存到 {} 平台", current_template_platform.upper())
            except Exception as e:
                logger.warning("保存 AI 模版失败：{}", e)
        self.txt_prompt.bind("<FocusOut>", _save_tpl)

        # 测试 AI 按钮
        tb.Button(ai_box, text="测试AI生成", bootstyle=PRIMARY, command=self.test_ai).pack(side=LEFT, padx=8)

        # 操作类型选择
        ops = tb.Labelframe(form, text="操作类型", padding=8); ops.pack(fill=X, pady=(4, 6))
        tb.Checkbutton(ops, variable=self.var_comment, text="评论", bootstyle="success, switch").pack(side=LEFT, padx=6)
        tb.Checkbutton(ops, variable=self.var_like, text="点赞", bootstyle="warning, switch").pack(side=LEFT, padx=6)
        tb.Checkbutton(ops, variable=self.var_rt, text="转发", bootstyle="info, switch").pack(side=LEFT, padx=6)
        tb.Checkbutton(ops, variable=self.var_collect, text="收藏", bootstyle="primary, switch").pack(side=LEFT, padx=6)
        tb.Checkbutton(ops, variable=self.var_follow, text="关注", bootstyle="secondary, switch").pack(side=LEFT, padx=6)

        # 执行范围
        scope = tb.Labelframe(form, text="执行范围", padding=8); scope.pack(fill=X, pady=(4, 6))
        self.var_scope = tb.StringVar(value="random")
        tb.Radiobutton(scope, text="随机模式", variable=self.var_scope, value="random").pack(side=LEFT, padx=8)
        tb.Radiobutton(scope, text="精准模式（链接列表）", variable=self.var_scope, value="list").pack(side=LEFT, padx=8)

        # 反爬虫模式选择
        anti_det = tb.Labelframe(form, text="反爬虫模式", padding=8); anti_det.pack(fill=X, pady=(4, 6))
        anti_det_frame = tb.Frame(anti_det); anti_det_frame.pack(fill=X)

        tb.Label(anti_det_frame, text="模式:", width=6, anchor=W).pack(side=LEFT)
        anti_det_combo = tb.Combobox(anti_det_frame, textvariable=self.var_anti_detection,
                                    values=["off", "basic", "enhanced", "extreme"],
                                    state="readonly", width=12)
        anti_det_combo.pack(side=LEFT, padx=4)

        # 反爬虫模式说明
        anti_det_info = tb.Frame(anti_det); anti_det_info.pack(fill=X, pady=(4, 0))
        self.lbl_anti_detection_info = tb.Label(anti_det_info, text="", font=("", 8), foreground="gray")
        self.lbl_anti_detection_info.pack(side=LEFT)

        # 反爬虫模式变化时更新说明
        def _on_anti_detection_change(*_):
            mode = self.var_anti_detection.get()
            info_text = {
                "off": "关闭 - 不使用反爬虫措施",
                "basic": "基础 - 随机延时、用户代理轮换、基础行为模拟",
                "enhanced": "增强 - 浏览器指纹伪装、Canvas随机化、WebRTC防护",
                "extreme": "极限 - 代理轮换、会话隔离、高级行为随机化"
            }.get(mode, "")
            self.lbl_anti_detection_info.configure(text=info_text)

        self.var_anti_detection.trace_add("write", _on_anti_detection_change)
        _on_anti_detection_change()  # 初始化显示

        # 随机模式参数：博文数量（针对不同的 N 条博文，各执行一轮勾选的操作）
        rand = tb.Frame(form); rand.pack(fill=X)
        tb.Label(rand, text="随机博文数", width=14, anchor=W).pack(side=LEFT)
        self.var_cnt_posts = tb.IntVar(value=3)
        tb.Entry(rand, textvariable=self.var_cnt_posts, width=6).pack(side=LEFT, padx=4)

        # 精准模式参数：链接列表
        lst_box = tb.Labelframe(form, text="链接列表（每行一个）", padding=6); lst_box.pack(fill=BOTH, expand=YES, pady=(6, 4))
        self.links_text = ScrolledText(lst_box, height=6, autohide=True); self.links_text.pack(fill=BOTH, expand=YES)
        tb.Button(lst_box, text="从文件导入...", bootstyle=SECONDARY, command=self._import_links).pack(anchor="e", pady=6)

        # 系统参数
        # 轮询间隔滑块 + 数字
        interval_row = tb.Frame(form); interval_row.pack(fill=X, pady=6)
        tb.Label(interval_row, text="轮询间隔(秒)", width=14, anchor=W).pack(side=LEFT)
        tb.Scale(interval_row, variable=self.var_interval, from_=30, to=600, length=180, bootstyle=PRIMARY).pack(side=LEFT)
        self.lbl_interval = tb.Label(interval_row, text=str(self.var_interval.get()))
        self.lbl_interval.pack(side=LEFT, padx=6)
        self.var_interval.trace_add("write", lambda *a: self.lbl_interval.configure(text=str(self.var_interval.get())))

        # 每小时限制滑块
        maxc_row = tb.Frame(form); maxc_row.pack(fill=X, pady=6)
        tb.Label(maxc_row, text="每小时最多评论", width=14, anchor=W).pack(side=LEFT)
        tb.Scale(maxc_row, variable=self.var_max_cmt, from_=0, to=60, length=180, bootstyle=SUCCESS).pack(side=LEFT)
        tb.Label(maxc_row, textvariable=self.var_max_cmt).pack(side=LEFT, padx=6)

        maxr_row = tb.Frame(form); maxr_row.pack(fill=X, pady=6)
        tb.Label(maxr_row, text="每小时最多转发", width=14, anchor=W).pack(side=LEFT)
        tb.Scale(maxr_row, variable=self.var_max_rt, from_=0, to=60, length=180, bootstyle=INFO).pack(side=LEFT)
        tb.Label(maxr_row, textvariable=self.var_max_rt).pack(side=LEFT, padx=6)

        row("代理(可选)", tb.Entry(form, textvariable=self.var_proxy, width=24))

        slow_row = tb.Frame(form); slow_row.pack(fill=X, pady=6)
        tb.Label(slow_row, text="慢动作(ms)", width=14, anchor=W).pack(side=LEFT)
        tb.Scale(slow_row, variable=self.var_slowmo, from_=0, to=1000, length=180, bootstyle=SECONDARY).pack(side=LEFT)
        tb.Label(slow_row, textvariable=self.var_slowmo).pack(side=LEFT, padx=6)

        tb.Button(right, text="保存配置", bootstyle=PRIMARY, command=self.save).pack(pady=8, fill=X)
        tb.Button(right, text="执行批量", bootstyle=SUCCESS, command=self.run_batch).pack(pady=4, fill=X)
        tb.Button(right, text="打开日志目录", bootstyle=SECONDARY, command=self.open_logs).pack(pady=4, fill=X)

        # 底部统计
        status = tb.Frame(self.app, padding=8)
        status.pack(fill=X)
        self.lbl_cmt = tb.Label(status, text="已评论：0", bootstyle=SUCCESS)
        self.lbl_rt = tb.Label(status, text="已转发：0", bootstyle=INFO)
        self.lbl_cmt.pack(side=LEFT, padx=6)
        self.lbl_rt.pack(side=LEFT, padx=6)

        # 线程&计数
        self._worker: threading.Thread | None = None
        self._count_cmt = 0
        self._count_rt = 0

        self.app.after(200, self._drain)

    def _set_nav_active(self, key: str):
        if self._nav_active == key:
            return
        # 简单激活样式切换
        if self._nav_active is not None:
            self._nav_buttons[self._nav_active].configure(bootstyle=SECONDARY)
        self._nav_buttons[key].configure(bootstyle=PRIMARY)
        self._nav_active = key

    def save(self):
        try:
            CONFIG.platform = self.var_platform.get()
            CONFIG.comment.mode = self.var_mode.get()
            CONFIG.action.do_comment = bool(self.var_comment.get())
            CONFIG.action.do_retweet = bool(self.var_rt.get())
            CONFIG.action.do_like = bool(self.var_like.get())
            CONFIG.action.do_collect = bool(self.var_collect.get())
            CONFIG.action.do_follow = bool(self.var_follow.get())
            CONFIG.poll_interval_sec = int(self.var_interval.get())
            CONFIG.action.max_comments_per_hour = int(self.var_max_cmt.get())
            CONFIG.action.max_retweets_per_hour = int(self.var_max_rt.get())
            CONFIG.proxy = self.var_proxy.get() or None
            CONFIG.slow_mo_ms = int(self.var_slowmo.get())

            # 反爬虫配置
            CONFIG.anti_detection_mode = self.var_anti_detection.get()
            CONFIG.anti_detection_enabled = self.var_anti_detection.get() != "off"

            # 新增：保存 AI 配置
            CONFIG.comment.hf_api_key = (self.var_ai_key.get() or "").strip()
            if hasattr(self, 'var_ai_model'):
                CONFIG.comment.model = self.var_ai_model.get()
            if hasattr(self, 'var_ai_temperature'):
                CONFIG.comment.temperature = float(self.var_ai_temperature.get())
            if hasattr(self, 'var_ai_max_tokens'):
                CONFIG.comment.max_tokens = int(self.var_ai_max_tokens.get())

            # 保存当前编辑的模板到对应平台
            if hasattr(self, 'var_template_platform') and hasattr(self, 'txt_prompt'):
                current_template_platform = self.var_template_platform.get()
                template_content = self.txt_prompt.get("1.0", END).strip()

                # 确保platform_templates存在
                if not hasattr(CONFIG.comment, "platform_templates"):
                    CONFIG.comment.platform_templates = {}

                CONFIG.comment.platform_templates[current_template_platform] = template_content

                # 如果是当前选择的平台，也更新默认模板
                if current_template_platform == CONFIG.platform:
                    CONFIG.comment.prompt_template = template_content
            else:
                # 兼容旧版本
                if hasattr(self, 'txt_prompt'):
                    CONFIG.comment.prompt_template = self.txt_prompt.get("1.0", END).strip()

            CONFIG.save()
            # 重新加载配置以确保一致性
            CONFIG.reload()
            logger.info("配置已保存。")
        except Exception as e:
            logger.warning("保存失败：{}", e)

    def _import_links(self):
        path = fd.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.links_text.delete("1.0", END)
            self.links_text.insert("1.0", text)
            logger.info("已导入链接列表：{} 行", len([l for l in text.splitlines() if l.strip()]))
        except Exception as e:
            logger.warning("导入失败：{}", e)

    def run_batch(self):
        # 若监控线程在运行，先优雅停掉，避免抢占浏览器与关闭冲突
        if self._worker and self._worker.is_alive():
            try:
                STOP_EVENT.set()
                logger.info("检测到有监控线程在运行，正在停止…")
                self._worker.join(timeout=8.0)
            except Exception:
                pass
            finally:
                STOP_EVENT.clear()
                self._worker = None
        self._apply_runtime_config()
        self._worker = threading.Thread(target=self._batch_target, daemon=True)
        self._worker.start()

    def _exec_random_posts(self):
        # 随机 N 条不同博文，对每条执行一次勾选的操作集合（会话内不关浏览器）
        self._apply_runtime_config()
        platform = self.var_platform.get()
        n = max(1, int(self.var_cnt_posts.get()))
        do_c = bool(self.var_comment.get())
        do_l = bool(self.var_like.get())
        do_r = bool(self.var_rt.get())
        do_collect = bool(self.var_collect.get())
        logger.info("随机模式：准备对 {} 条博文执行 操作=[评:{} 赞:{} 转:{} 藏:{}]", n, do_c, do_l, do_r, do_collect)
        # 先关闭可能仍在运行的监控线程，避免竞争
        try:
            STOP_EVENT.set()
            if self._worker and self._worker.is_alive():
                logger.info("等待监控线程停止…")
                self._worker.join(timeout=6.0)
        except Exception:
            pass
        finally:
            STOP_EVENT.clear()
            self._worker = None
        # 顶部按钮与状态条：显示“运行中”，并恢复为“空闲”在 finally
        try:
            self.btn_start.configure(state=DISABLED)
            self.btn_stop.configure(state=NORMAL)
            self.lbl_status.configure(text="状态：运行中(随机模式)", bootstyle=SUCCESS)
            # 进度条 + 文本
            progress = tb.Frame(self.app)
            progress.place(relx=0.5, rely=0.97, anchor='s')
            var_txt = tb.StringVar(value=f"0/{n}")
            bar = tb.Progressbar(progress, length=360, bootstyle=INFO, mode='determinate', maximum=max(1, n))
            bar.grid(row=0, column=0, padx=6)
            lab = tb.Label(progress, textvariable=var_txt)
            lab.grid(row=0, column=1)
            def on_progress(p, total):
                try:
                    bar.configure(value=p)
                    var_txt.set(f"{p}/{total}")
                    self.app.update_idletasks()
                except Exception:
                    pass
            if platform == 'weibo':
                # 简单模式：每次都回到首页第一条卡片，不滚动，执行勾选操作
                from .run_tasks import run_weibo_firstcard_repeat
                run_weibo_firstcard_repeat(n, do_comment=do_c, do_like=do_l, do_retweet=do_r, keep_open=True, on_progress=on_progress)
            elif platform == 'xhs':
                from .run_tasks import run_xhs_firstcard_repeat
                run_xhs_firstcard_repeat(n, do_comment=do_c, do_like=do_l, do_collect=do_collect, do_share=do_r, keep_open=True, on_progress=on_progress)
            elif platform == 'zhihu':
                from .run_tasks import run_zhihu_firstcard_repeat
                run_zhihu_firstcard_repeat(n, do_comment=do_c, do_like=do_l, do_collect=do_collect, keep_open=True, on_progress=on_progress)
            elif platform == 'toutiao':
                from .run_tasks import run_toutiao_firstcard_repeat
                run_toutiao_firstcard_repeat(n, do_comment=do_c, do_like=do_l, do_collect=do_collect, keep_open=True, on_progress=on_progress)
            else:
                from .run_tasks import run_random_n_posts
                run_random_n_posts(n, do_comment=do_c, do_like=do_l, do_retweet=do_r, keep_open=True, on_progress=on_progress)
            logger.info("批量执行完成。")
        finally:
            try:
                self.btn_start.configure(state=NORMAL)
                self.btn_stop.configure(state=DISABLED)
                self.lbl_status.configure(text="状态：空闲", bootstyle=INFO)
            except Exception:
                pass
        return

    def _exec_precise_mode(self):
        """精准模式：读取链接并逐条执行"""
        logger.info("=== 开始精准模式执行 ===")

        # 读取链接列表
        links = [l.strip() for l in self.links_text.get("1.0", END).splitlines() if l.strip()]
        if not links:
            logger.warning("精准模式：未提供任何链接。")
            return

        logger.info("精准模式：准备处理 {} 条链接", len(links))
        for i, link in enumerate(links, 1):
            logger.info("精准模式：[{}/{}] 准备处理链接: {}", i, len(links), link)

        # 获取操作配置
        do_comment = bool(self.var_comment.get())
        do_like = bool(self.var_like.get())
        do_retweet = bool(self.var_rt.get())
        do_collect = bool(self.var_collect.get())
        do_follow = bool(self.var_follow.get())

        logger.info("精准模式：操作配置 - 评论:{} 点赞:{} 转发:{} 收藏:{} 关注:{}",
                   do_comment, do_like, do_retweet, do_collect, do_follow)

        # 先关闭可能仍在运行的监控线程，避免竞争
        try:
            STOP_EVENT.set()
            if self._worker and self._worker.is_alive():
                logger.info("等待监控线程停止…")
                self._worker.join(timeout=6.0)
        except Exception:
            pass
        finally:
            STOP_EVENT.clear()
            self._worker = None

        # 更新UI状态
        try:
            self.btn_start.configure(state=DISABLED)
            self.btn_stop.configure(state=NORMAL)
            self.lbl_status.configure(text="状态：运行中(精准模式)", bootstyle=SUCCESS)

            # 进度条
            progress = tb.Frame(self.app)
            progress.place(relx=0.5, rely=0.97, anchor='s')
            var_txt = tb.StringVar(value=f"0/{len(links)}")
            bar = tb.Progressbar(progress, length=360, bootstyle=INFO, mode='determinate', maximum=max(1, len(links)))
            bar.grid(row=0, column=0, padx=6)
            lab = tb.Label(progress, textvariable=var_txt)
            lab.grid(row=0, column=1)

            def on_progress(p, total):
                try:
                    bar.configure(value=p)
                    var_txt.set(f"{p}/{total}")
                    self.app.update_idletasks()
                except Exception:
                    pass

            # 执行精准模式处理
            try:
                from .run_tasks import process_links

                # 创建一个包装函数来处理进度更新
                def process_links_with_progress(links, do_like, do_retweet, do_comment, do_follow):
                    from .run_tasks import BrowserManager
                    from .login_weibo import ensure_login_weibo
                    from .run_tasks import weibo_act_on_url

                    platform = getattr(CONFIG, "platform", "weibo")
                    bm = BrowserManager()
                    try:
                        bm.launch()
                        bm.new_context(use_storage=True)

                        if platform == "weibo":
                            ensure_login_weibo(bm.page)

                            for i, url in enumerate(links):
                                logger.info("精准模式: [{}] 正在处理链接: {}", time.strftime("%H:%M:%S"), url)
                                try:
                                    weibo_act_on_url(bm, url, do_like, do_retweet, do_comment, do_collect)
                                    logger.info("精准模式: [{}] ✅ 链接处理完成: {}", time.strftime("%H:%M:%S"), url)
                                except Exception as e:
                                    logger.error("精准模式: [{}] ❌ 链接处理失败: {} - {}", time.strftime("%H:%M:%S"), url, str(e))

                                # 更新进度
                                on_progress(i + 1, len(links))

                                # 间隔等待（除最后一次）
                                if i < len(links) - 1:
                                    wait_time = CONFIG.poll_interval_sec
                                    logger.info("精准模式: [{}] 等待 {} 秒后处理下一个链接...", time.strftime("%H:%M:%S"), wait_time)
                                    for _ in range(wait_time):
                                        time.sleep(1)
                        else:
                            # 其他平台使用更新的process_links函数
                            process_links(links, do_like, do_retweet, do_comment, do_follow, keep_open=True, do_collect=do_collect)
                    finally:
                        bm.close()

                # 执行处理
                process_links_with_progress(links, do_like, do_retweet, do_comment, do_follow)

                logger.info("精准模式：✅ 已完成对 {} 条链接的处理。", len(links))

            except Exception as e:
                logger.exception("精准模式执行失败：{}", e)

            # 清理进度条
            try:
                progress.destroy()
            except Exception:
                pass

        finally:
            try:
                self.btn_start.configure(state=NORMAL)
                self.btn_stop.configure(state=DISABLED)
                self.lbl_status.configure(text="状态：空闲", bootstyle=INFO)
            except Exception:
                pass

    def _run_comment_once(self):
        self._apply_runtime_config()
        try:
            comment_once()
        except Exception as e:
            logger.warning("评1次失败：{}", e)

    def _run_like_once(self):
        self._apply_runtime_config()
        try:
            like_once()
        except Exception as e:
            logger.warning("赞1次失败：{}", e)

    def _run_retweet_once(self):
        self._apply_runtime_config()
        try:
            retweet_once()
        except Exception as e:
            logger.warning("转1次失败：{}", e)

    def _run_follow_once(self):
        self._apply_runtime_config()
        try:
            run_follow_once()
        except Exception as e:
            logger.warning("关1次失败：{}", e)

    def _run_xhs_comment_once(self):
        self._apply_runtime_config()
        try:
            xhs_comment_once()
        except Exception as e:
            logger.warning("XHS评论1次失败：{}", e)

    def _run_xhs_like_once(self):
        self._apply_runtime_config()
        try:
            xhs_like_once()
        except Exception as e:
            logger.warning("XHS点赞1次失败：{}", e)

    def _run_xhs_collect_once(self):
        self._apply_runtime_config()
        try:
            xhs_collect_once()
        except Exception as e:
            logger.warning("XHS收藏1次失败：{}", e)

    def _run_xhs_share_once(self):
        self._apply_runtime_config()
        try:
            xhs_share_once()
        except Exception as e:
            logger.warning("XHS分享1次失败：{}", e)

    def _run_xhs_follow_once(self):
        self._apply_runtime_config()
        try:
            xhs_follow_once()
        except Exception as e:
            logger.warning("XHS关注1次失败：{}", e)

    def _run_zhihu_comment_once(self):
        self._apply_runtime_config()
        try:
            zhihu_comment_once()
        except Exception as e:
            logger.warning("知乎评论1次失败：{}", e)

    def _run_zhihu_like_once(self):
        self._apply_runtime_config()
        try:
            zhihu_like_once()
        except Exception as e:
            logger.warning("知乎点赞1次失败：{}", e)

    def _run_zhihu_collect_once(self):
        self._apply_runtime_config()
        try:
            zhihu_collect_once()
        except Exception as e:
            logger.warning("知乎收藏1次失败：{}", e)

    def _run_zhihu_follow_once(self):
        self._apply_runtime_config()
        try:
            zhihu_follow_once()
        except Exception as e:
            logger.warning("知乎关注1次失败：{}", e)

    def _run_toutiao_comment_once(self):
        self._apply_runtime_config()
        try:
            toutiao_comment_once()
        except Exception as e:
            logger.warning("今日头条评论1次失败：{}", e)

    def _run_toutiao_like_once(self):
        self._apply_runtime_config()
        try:
            toutiao_like_once()
        except Exception as e:
            logger.warning("今日头条点赞1次失败：{}", e)

    def _run_toutiao_collect_once(self):
        self._apply_runtime_config()
        try:
            toutiao_collect_once()
        except Exception as e:
            logger.warning("今日头条收藏1次失败：{}", e)

    def _run_toutiao_follow_once(self):
        self._apply_runtime_config()
        try:
            toutiao_follow_once()
        except Exception as e:
            logger.warning("今日头条关注1次失败：{}", e)


    def _drain(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg.startswith("[STAT]"):
                    if "评论+1" in msg:
                        self._count_cmt += 1
                        self.lbl_cmt.configure(text=f"已评论：{self._count_cmt}")
                    if "转发+1" in msg:
                        self._count_rt += 1
                        self.lbl_rt.configure(text=f"已转发：{self._count_rt}")
                    continue
                self.log.insert(END, msg + "\n")
                self.log.see(END)
        except Empty:
            pass
        self.app.after(200, self._drain)

    def _apply_runtime_config(self):
        try:
            CONFIG.platform = self.var_platform.get()
            CONFIG.comment.mode = self.var_mode.get()
            CONFIG.action.do_comment = bool(self.var_comment.get())
            CONFIG.action.do_retweet = bool(self.var_rt.get())
            CONFIG.action.do_like = bool(self.var_like.get())
            CONFIG.action.do_collect = bool(self.var_collect.get())
            CONFIG.action.do_follow = bool(self.var_follow.get())
            CONFIG.poll_interval_sec = int(self.var_interval.get())
            CONFIG.proxy = self.var_proxy.get() or None
            CONFIG.slow_mo_ms = int(self.var_slowmo.get())

            # 反爬虫配置
            CONFIG.anti_detection_mode = self.var_anti_detection.get()
            CONFIG.anti_detection_enabled = self.var_anti_detection.get() != "off"

            # AI配置
            if hasattr(self, 'var_ai_key'):
                CONFIG.comment.hf_api_key = (self.var_ai_key.get() or '').strip()
            if hasattr(self, 'var_ai_model'):
                CONFIG.comment.model = self.var_ai_model.get()
            if hasattr(self, 'var_ai_temperature'):
                CONFIG.comment.temperature = float(self.var_ai_temperature.get())
            if hasattr(self, 'var_ai_max_tokens'):
                CONFIG.comment.max_tokens = int(self.var_ai_max_tokens.get())
            if hasattr(self, 'txt_prompt'):
                # 保存当前编辑的模板到对应平台
                if hasattr(self, 'var_template_platform'):
                    current_template_platform = self.var_template_platform.get()
                    template_content = self.txt_prompt.get('1.0', END).strip()

                    # 确保platform_templates存在
                    if not hasattr(CONFIG.comment, "platform_templates"):
                        CONFIG.comment.platform_templates = {}

                    CONFIG.comment.platform_templates[current_template_platform] = template_content

                    # 如果是当前选择的平台，也更新默认模板
                    if current_template_platform == CONFIG.platform:
                        CONFIG.comment.prompt_template = template_content
                else:
                    # 兼容旧版本
                    CONFIG.comment.prompt_template = self.txt_prompt.get('1.0', END).strip()
        except Exception as e:
            logger.warning("应用运行时配置失败：{}", e)

    def start_loop(self):
        if self._worker and self._worker.is_alive():
            return
        try:
            STOP_EVENT.clear()
        except Exception:
            pass
        self._apply_runtime_config()
        # 在随机模式下，“开始监控”应等价于执行随机博文数，并且不改变按钮状态（避免误以为持续监控）
        scope = self.var_scope.get()
        if scope == 'random':
            threading.Thread(target=self._exec_random_posts, daemon=True).start()
            return
        elif scope == 'list':
            threading.Thread(target=self._exec_precise_mode, daemon=True).start()
            return
        self._worker = threading.Thread(target=self._loop_target, daemon=True)
        self._worker.start()
        self.btn_start.configure(state=DISABLED)
        self.btn_stop.configure(state=NORMAL)
        self.lbl_status.configure(text="状态：运行中", bootstyle=SUCCESS)
        logger.info("已开始监控循环（UI）")

    def stop_loop(self):
        try:
            STOP_EVENT.set()
        except Exception:
            pass
        logger.info("停止请求：已发出停止信号。")
        # 仅停止循环，不主动关闭浏览器，由 run_monitor_loop 管理

    def _loop_target(self):
        try:
            run_monitor_loop()
        except Exception as e:
            logger.exception("UI loop thread error: {}", e)
        finally:
            # 在线程结束时刷新按钮状态
            try:
                self.app.after(0, self._on_loop_finished)
            except Exception:
                pass

    def _on_loop_finished(self):
        self._worker = None
        self.btn_start.configure(state=NORMAL)
        self.btn_stop.configure(state=DISABLED)
        self.lbl_status.configure(text="状态：空闲", bootstyle=INFO)

    def login_account(self):
        # 根据选择的平台启动对应登录流程
        platform = self.var_platform.get()
        logger.info("准备登录：平台={}", platform)
        try:
            if platform == "weibo":
                bm = BrowserManager()
                try:
                    bm.launch(); bm.new_context(use_storage=True)
                    ensure_login_weibo(bm.page)
                    logger.info("Weibo 登录流程完成/已登录")
                finally:
                    bm.close()
            elif platform == "xhs":
                bm = BrowserManager()
                try:
                    bm.launch(); bm.new_context(use_storage=True)
                    ensure_login_xhs_with_save(bm)
                    logger.info("XHS 登录流程完成/已登录")
                finally:
                    bm.close()
            elif platform == "zhihu":
                bm = BrowserManager()
                try:
                    bm.launch(); bm.new_context(use_storage=True)
                    ensure_login_zhihu_with_save(bm)
                    logger.info("Zhihu 登录流程完成/已登录")
                finally:
                    bm.close()
            elif platform == "toutiao":
                bm = BrowserManager()
                try:
                    bm.launch(); bm.new_context(use_storage=True)
                    ensure_login_toutiao_with_save(bm)
                    logger.info("Toutiao 登录流程完成/已登录")
                finally:
                    bm.close()
            else:
                bm = BrowserManager()
                try:
                    bm.launch(); bm.new_context(use_storage=True)
                    login_flow(bm)
                finally:
                    bm.close()
        except Exception as e:
            logger.warning("登录失败：{}", e)

            self.btn_start.configure(state=NORMAL)
            self.btn_stop.configure(state=DISABLED)
            self.lbl_status.configure(text="状态：空闲", bootstyle=INFO)


    def open_logs(self):
        path = os.path.abspath("logs")
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            logger.warning("打开日志目录失败：{}", e)

    def test_ai(self):
        # 使用当前模版与 Key 调用一次 SiliconFlow 并在日志实时展示
        try:
            from .ai import gen_comment_by_ai
            sample = "示例内容：今天的分享很棒，受益匪浅！"
            text = gen_comment_by_ai(sample)
            self.log.insert(END, f"[AI测试] {text}\n"); self.log.see(END)
            logger.info("测试AI成功：{}", text)
        except Exception as e:
            self.log.insert(END, f"[AI测试] 失败：{e}\n"); self.log.see(END)
            logger.warning("测试AI失败：{}", e)

        except Exception as e:
            logger.warning("打开日志目录失败：{}", e)

    def logout_account(self):
        # 清除存储的登录状态并提示需要重新登录
        try:
            from pathlib import Path
            p = Path(CONFIG.storage_state_path)
            if p.exists():
                p.unlink()
                logger.info("登录状态已清除。下次操作将要求重新登录。")
            else:
                logger.info("未找到已保存的登录状态文件。")
        except Exception as e:
            logger.warning("退出失败：{}", e)

    def run(self):
        logger.info("UI 已启动。")
        self.app.mainloop()

