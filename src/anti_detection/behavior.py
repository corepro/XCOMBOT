"""
人类行为模拟模块
提供各种人类行为模拟功能
"""

import random
import time
import math
from typing import Tuple, List, Optional
from playwright.sync_api import Page
from ..logger import logger


class HumanBehaviorSimulator:
    """人类行为模拟器"""
    
    def __init__(self):
        self.last_mouse_position = (0, 0)
        self.typing_speed_wpm = random.randint(40, 80)  # 每分钟字数
        
    def simulate_mouse_movement(self, page: Page, target_x: int, target_y: int, 
                              duration: float = 1.0, curve_intensity: float = 0.3) -> None:
        """模拟人类鼠标移动轨迹"""
        try:
            start_x, start_y = self.last_mouse_position
            
            # 计算移动步数
            distance = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
            steps = max(10, int(distance / 10))
            
            # 生成贝塞尔曲线路径
            points = self._generate_bezier_curve(
                start_x, start_y, target_x, target_y, steps, curve_intensity
            )
            
            # 执行移动
            step_duration = duration / len(points)
            for x, y in points:
                page.mouse.move(int(x), int(y))
                time.sleep(step_duration + random.uniform(-0.01, 0.01))
            
            self.last_mouse_position = (target_x, target_y)
            logger.debug("人类行为: 鼠标移动到 ({}, {})", target_x, target_y)
            
        except Exception as e:
            logger.warning("人类行为: 鼠标移动失败: {}", str(e))
    
    def _generate_bezier_curve(self, start_x: int, start_y: int, end_x: int, end_y: int,
                              steps: int, curve_intensity: float) -> List[Tuple[float, float]]:
        """生成贝塞尔曲线路径"""
        # 控制点
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # 添加随机偏移
        offset_x = random.uniform(-100, 100) * curve_intensity
        offset_y = random.uniform(-100, 100) * curve_intensity
        
        control_x = mid_x + offset_x
        control_y = mid_y + offset_y
        
        points = []
        for i in range(steps + 1):
            t = i / steps
            
            # 二次贝塞尔曲线公式
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * end_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * end_y
            
            points.append((x, y))
        
        return points
    
    def simulate_human_typing(self, page: Page, element_selector: str, text: str,
                            typing_errors: bool = True) -> None:
        """模拟人类打字行为"""
        try:
            element = page.locator(element_selector).first
            if not element.is_visible():
                logger.warning("人类行为: 输入元素不可见: {}", element_selector)
                return
            
            # 点击元素获得焦点
            element.click()
            time.sleep(random.uniform(0.1, 0.3))
            
            # 清空现有内容
            element.fill("")
            
            # 计算打字间隔
            chars_per_second = self.typing_speed_wpm * 5 / 60  # 平均每个字符的时间
            base_interval = 1.0 / chars_per_second
            
            typed_text = ""
            for i, char in enumerate(text):
                # 随机打字间隔
                interval = base_interval * random.uniform(0.5, 2.0)
                
                # 模拟打字错误和修正
                if typing_errors and random.random() < 0.05:  # 5%概率打错
                    wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                    typed_text += wrong_char
                    element.fill(typed_text)
                    time.sleep(interval)
                    
                    # 删除错误字符
                    typed_text = typed_text[:-1]
                    element.fill(typed_text)
                    time.sleep(interval * 0.5)
                
                # 输入正确字符
                typed_text += char
                element.fill(typed_text)
                
                # 随机暂停（思考时间）
                if char in ".,!?;:" and random.random() < 0.3:
                    time.sleep(random.uniform(0.3, 0.8))
                else:
                    time.sleep(interval)
            
            logger.debug("人类行为: 完成文本输入: {}", text[:20] + "...")
            
        except Exception as e:
            logger.warning("人类行为: 模拟打字失败: {}", str(e))
    
    def simulate_reading_behavior(self, page: Page, reading_speed: str = "normal") -> None:
        """模拟阅读行为"""
        try:
            # 根据阅读速度设置参数
            speed_config = {
                "fast": {"base_time": 1.0, "scroll_probability": 0.8, "pause_probability": 0.2},
                "normal": {"base_time": 3.0, "scroll_probability": 0.6, "pause_probability": 0.4},
                "slow": {"base_time": 6.0, "scroll_probability": 0.4, "pause_probability": 0.6}
            }
            
            config = speed_config.get(reading_speed, speed_config["normal"])
            
            # 基础阅读时间
            reading_time = config["base_time"] * random.uniform(0.5, 1.5)
            logger.debug("人类行为: 模拟阅读 {:.2f} 秒", reading_time)
            
            start_time = time.time()
            while time.time() - start_time < reading_time:
                # 随机滚动
                if random.random() < config["scroll_probability"]:
                    self.simulate_natural_scrolling(page)
                
                # 随机暂停
                if random.random() < config["pause_probability"]:
                    pause_time = random.uniform(0.5, 2.0)
                    time.sleep(pause_time)
                else:
                    time.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            logger.warning("人类行为: 阅读行为模拟失败: {}", str(e))
    
    def simulate_natural_scrolling(self, page: Page) -> None:
        """模拟自然滚动行为"""
        try:
            # 随机滚动方向和距离
            scroll_direction = random.choice(["down", "up"])
            scroll_distance = random.randint(100, 500)
            
            if scroll_direction == "up":
                scroll_distance = -scroll_distance
            
            # 分段滚动，模拟真实滚动
            segments = random.randint(2, 5)
            segment_distance = scroll_distance // segments
            
            for _ in range(segments):
                page.mouse.wheel(0, segment_distance)
                time.sleep(random.uniform(0.1, 0.3))
            
            logger.debug("人类行为: 滚动 {} 像素", scroll_distance)
            
        except Exception as e:
            logger.warning("人类行为: 滚动行为模拟失败: {}", str(e))
    
    def simulate_hesitation(self, duration: Optional[float] = None) -> None:
        """模拟犹豫行为"""
        if duration is None:
            duration = random.uniform(0.5, 2.0)
        
        logger.debug("人类行为: 模拟犹豫 {:.2f} 秒", duration)
        time.sleep(duration)
    
    def simulate_click_with_hesitation(self, page: Page, element_selector: str,
                                     hesitation_probability: float = 0.3) -> bool:
        """模拟带犹豫的点击"""
        try:
            element = page.locator(element_selector).first
            if not element.is_visible():
                logger.warning("人类行为: 点击元素不可见: {}", element_selector)
                return False
            
            # 获取元素位置
            box = element.bounding_box()
            if not box:
                logger.warning("人类行为: 无法获取元素位置: {}", element_selector)
                return False
            
            # 计算点击位置（添加随机偏移）
            click_x = box["x"] + box["width"] / 2 + random.uniform(-10, 10)
            click_y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            
            # 移动鼠标到目标位置
            self.simulate_mouse_movement(page, int(click_x), int(click_y))
            
            # 随机犹豫
            if random.random() < hesitation_probability:
                self.simulate_hesitation(random.uniform(0.3, 1.0))
            
            # 执行点击
            page.mouse.click(int(click_x), int(click_y))
            logger.debug("人类行为: 点击元素: {}", element_selector)
            
            return True
            
        except Exception as e:
            logger.warning("人类行为: 模拟点击失败: {}", str(e))
            return False
    
    def simulate_page_exploration(self, page: Page, duration: float = 5.0) -> None:
        """模拟页面探索行为"""
        try:
            logger.debug("人类行为: 开始页面探索 {:.2f} 秒", duration)
            
            start_time = time.time()
            while time.time() - start_time < duration:
                action = random.choice(["scroll", "mouse_move", "pause"])
                
                if action == "scroll":
                    self.simulate_natural_scrolling(page)
                elif action == "mouse_move":
                    # 随机移动鼠标
                    x = random.randint(100, 1200)
                    y = random.randint(100, 800)
                    self.simulate_mouse_movement(page, x, y, duration=0.5)
                else:  # pause
                    time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            logger.warning("人类行为: 页面探索失败: {}", str(e))


# 全局行为模拟器实例
behavior_simulator = HumanBehaviorSimulator()


def simulate_human_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """模拟人类延时的便捷函数"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def simulate_thinking_pause() -> None:
    """模拟思考暂停"""
    pause_time = random.uniform(1.0, 3.0)
    time.sleep(pause_time)
