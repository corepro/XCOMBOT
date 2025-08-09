from __future__ import annotations
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from queue import SimpleQueue, Empty
from .logger import attach_ui_queue, logger
from .run_tasks import run_monitor_loop
import time


class AppUI:
    def __init__(self):
        from .config import CONFIG
        self.root = tk.Tk()
        self.root.title("XComBot - 随机评论监控")
        self.queue: SimpleQueue[str] = SimpleQueue()
        attach_ui_queue(self.queue)

        # 顶部配置区
        cfg = tk.LabelFrame(self.root, text="配置 (修改后点击保存)")
        cfg.pack(fill=tk.X, padx=6, pady=6)

        # 行1：模式、只评论/只转发
        row1 = tk.Frame(cfg); row1.pack(fill=tk.X)
        tk.Label(row1, text="评论模式").pack(side=tk.LEFT)
        self.var_mode = tk.StringVar(value=CONFIG.comment.mode)
        tk.OptionMenu(row1, self.var_mode, "local", "ai").pack(side=tk.LEFT, padx=4)

        self.var_do_comment = tk.BooleanVar(value=CONFIG.action.do_comment)
        self.var_do_retweet = tk.BooleanVar(value=CONFIG.action.do_retweet)
        tk.Checkbutton(row1, text="评论", variable=self.var_do_comment).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(row1, text="转发", variable=self.var_do_retweet).pack(side=tk.LEFT, padx=6)

        # 行2：间隔、限速
        row2 = tk.Frame(cfg); row2.pack(fill=tk.X)
        tk.Label(row2, text="轮询间隔(秒)").pack(side=tk.LEFT)
        self.var_interval = tk.StringVar(value=str(CONFIG.poll_interval_sec))
        tk.Entry(row2, textvariable=self.var_interval, width=8).pack(side=tk.LEFT, padx=4)

        tk.Label(row2, text="每小时最多评论").pack(side=tk.LEFT)
        self.var_max_cmt = tk.StringVar(value=str(CONFIG.action.max_comments_per_hour))
        tk.Entry(row2, textvariable=self.var_max_cmt, width=6).pack(side=tk.LEFT, padx=4)

        tk.Label(row2, text="每小时最多转发").pack(side=tk.LEFT)
        self.var_max_rt = tk.StringVar(value=str(CONFIG.action.max_retweets_per_hour))
        tk.Entry(row2, textvariable=self.var_max_rt, width=6).pack(side=tk.LEFT, padx=4)

        # 行3：代理、慢动作
        row3 = tk.Frame(cfg); row3.pack(fill=tk.X)
        tk.Label(row3, text="代理(可选)").pack(side=tk.LEFT)
        self.var_proxy = tk.StringVar(value=CONFIG.proxy or "")
        tk.Entry(row3, textvariable=self.var_proxy, width=28).pack(side=tk.LEFT, padx=4)

        tk.Label(row3, text="慢动作(ms)").pack(side=tk.LEFT)
        self.var_slowmo = tk.StringVar(value=str(CONFIG.slow_mo_ms))
        tk.Entry(row3, textvariable=self.var_slowmo, width=8).pack(side=tk.LEFT, padx=4)

        # 行4：保存按钮
        row4 = tk.Frame(cfg); row4.pack(fill=tk.X)
        tk.Button(row4, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=6, pady=6)

        # 控制区
        ctrl = tk.Frame(self.root)
        ctrl.pack(fill=tk.X)
        self.btn_start = tk.Button(ctrl, text="开始监控", command=self.start_loop)
        self.btn_stop = tk.Button(ctrl, text="停止监控", command=self.stop_loop, state=tk.DISABLED)
        self.btn_start.pack(side=tk.LEFT, padx=6, pady=6)
        self.btn_stop.pack(side=tk.LEFT, padx=6, pady=6)

        # 统计区
        stats = tk.Frame(self.root)
        stats.pack(fill=tk.X)
        self.lbl_cmt = tk.Label(stats, text="已评论：0")
        self.lbl_rt = tk.Label(stats, text="已转发：0")
        self.lbl_cmt.pack(side=tk.LEFT, padx=6)
        self.lbl_rt.pack(side=tk.LEFT, padx=6)

        # 日志区
        self.log = ScrolledText(self.root, height=18)
        self.log.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._worker: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._count_comment = 0
        self._count_retweet = 0

        self.root.after(300, self._drain_logs)

    def save_config(self):
        from .config import CONFIG
        try:
            CONFIG.comment.mode = self.var_mode.get()
            CONFIG.action.do_comment = bool(self.var_do_comment.get())
            CONFIG.action.do_retweet = bool(self.var_do_retweet.get())
            CONFIG.poll_interval_sec = int(self.var_interval.get())
            CONFIG.action.max_comments_per_hour = int(self.var_max_cmt.get())
            CONFIG.action.max_retweets_per_hour = int(self.var_max_rt.get())
            CONFIG.proxy = self.var_proxy.get() or None
            CONFIG.slow_mo_ms = int(self.var_slowmo.get())
            CONFIG.save()
            logger.info("配置已保存。")
        except Exception as e:
            logger.warning("保存失败：{}", e)

    def _drain_logs(self):
        # 每 300ms 刷新一次 UI 日志
        try:
            while True:
                msg = self.queue.get_nowait()
                # 统计消息
                if msg.startswith("[STAT]"):
                    if "评论+1" in msg:
                        self._update_stats(cmt_delta=1)
                    if "转发+1" in msg:
                        self._update_stats(rt_delta=1)
                    continue
                self.log.insert(tk.END, msg + "\n")
                self.log.see(tk.END)
        except Empty:
            pass
        self.root.after(300, self._drain_logs)

    def _loop_target(self):
        try:
            run_monitor_loop()
        except Exception as e:
            logger.exception("UI loop thread error: {}", e)
        finally:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

    def start_loop(self):
        if self._worker and self._worker.is_alive():
            return
        self._count_comment = 0
        self._count_retweet = 0
        self._worker = threading.Thread(target=self._loop_target, daemon=True)
        self._worker.start()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        logger.info("已开始监控循环（UI）")

    def stop_loop(self):
        logger.info("停止请求：请在终端 Ctrl+C 或关闭窗口来中止当前监控线程。后续版本会支持 UI 内部安全停止。")

    def _update_stats(self, cmt_delta=0, rt_delta=0):
        self._count_comment += cmt_delta
        self._count_retweet += rt_delta
        self.lbl_cmt.config(text=f"已评论：{self._count_comment}")
        self.lbl_rt.config(text=f"已转发：{self._count_retweet}")

    def start_loop(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop_flag.clear()
        self._worker = threading.Thread(target=self._loop_target, daemon=True)
        self._worker.start()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        logger.info("已开始监控循环（UI）")

    def stop_loop(self):
        # 当前 run_monitor_loop 无限循环，这里提供提示；后续可扩展为可感知 stop_flag 的循环
        logger.info("停止请求：请在终端 Ctrl+C 或关闭窗口来中止当前监控线程。后续版本会支持 UI 内部安全停止。")

    def run(self):
        logger.info("UI 已启动。")
        self.root.mainloop()

