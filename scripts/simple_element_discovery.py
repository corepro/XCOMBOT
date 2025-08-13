#!/usr/bin/env python3
"""
简化的元素发现工具
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime

def discover_elements():
    """发现页面元素"""
    print("启动元素发现工具...")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        
        # 加载存储状态
        try:
            context.storage_state(path="storage/storage_state.json")
            print("已加载存储状态")
        except Exception as e:
            print(f"加载存储状态失败: {e}")
        
        page = context.new_page()
        discovered_elements = {}
        
        try:
            # 导航到微博首页
            print("导航到微博首页...")
            page.goto("https://weibo.com")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # 发现首页元素
            print("分析首页元素...")
            home_elements = {}
            
            # 查找评论按钮
            print("查找评论按钮...")
            comment_selectors = [
                "button:has-text('评论')",
                "[role=button]:has-text('评论')",
                "button[title*='评论']",
                ".comment-btn"
            ]
            
            for i, selector in enumerate(comment_selectors):
                try:
                    elements = page.locator(selector).all()
                    for j, elem in enumerate(elements):
                        if elem.is_visible():
                            info = {
                                "selector": selector,
                                "text": elem.inner_text(),
                                "enabled": elem.is_enabled(),
                                "visible": elem.is_visible()
                            }
                            home_elements[f"comment_btn_{i}_{j}"] = info
                            print(f"  发现评论按钮: {selector} - {info['text']}")
                except Exception as e:
                    print(f"  评论按钮选择器 {selector} 失败: {e}")
            
            # 查找点赞按钮
            print("查找点赞按钮...")
            like_selectors = [
                "button:has-text('赞')",
                "[role=button][aria-label*='赞']",
                "button[title*='赞']",
                ".like-btn"
            ]
            
            for i, selector in enumerate(like_selectors):
                try:
                    elements = page.locator(selector).all()
                    for j, elem in enumerate(elements):
                        if elem.is_visible():
                            info = {
                                "selector": selector,
                                "text": elem.inner_text(),
                                "enabled": elem.is_enabled(),
                                "visible": elem.is_visible()
                            }
                            home_elements[f"like_btn_{i}_{j}"] = info
                            print(f"  发现点赞按钮: {selector} - {info['text']}")
                except Exception as e:
                    print(f"  点赞按钮选择器 {selector} 失败: {e}")
            
            discovered_elements["weibo_home"] = home_elements
            
            # 进入详情页
            print("获取详情页链接...")
            cards = page.locator("article").all()
            if cards:
                time_links = cards[0].locator("time a").all()
                for link in time_links:
                    href = link.get_attribute("href")
                    if href and ("weibo.com" in href or "/status/" in href):
                        if href.startswith("/"):
                            detail_link = f"https://weibo.com{href}"
                        else:
                            detail_link = href
                        detail_link = detail_link.split("?")[0]
                        
                        print(f"进入详情页: {detail_link}")
                        page.goto(detail_link)
                        page.wait_for_load_state("domcontentloaded")
                        time.sleep(3)
                        
                        # 发现详情页元素
                        print("分析详情页元素...")
                        detail_elements = {}
                        
                        # 查找评论输入框
                        print("查找评论输入框...")
                        comment_box_selectors = [
                            "textarea[placeholder*='评论']",
                            "textarea[placeholder*='说点什么']",
                            "#comment-textarea",
                            "textarea"
                        ]
                        
                        for i, selector in enumerate(comment_box_selectors):
                            try:
                                elements = page.locator(selector).all()
                                for j, elem in enumerate(elements):
                                    if elem.is_visible():
                                        info = {
                                            "selector": selector,
                                            "placeholder": elem.get_attribute("placeholder") or "",
                                            "enabled": elem.is_enabled(),
                                            "visible": elem.is_visible()
                                        }
                                        detail_elements[f"comment_box_{i}_{j}"] = info
                                        print(f"  发现评论输入框: {selector} - {info['placeholder']}")
                            except Exception as e:
                                print(f"  评论输入框选择器 {selector} 失败: {e}")
                        
                        discovered_elements["weibo_detail"] = detail_elements
                        break
            
            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discovered_elements_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(discovered_elements, f, ensure_ascii=False, indent=2)
            
            print(f"\n元素发现完成！结果已保存到: {filename}")
            print("\n发现的元素总结:")
            for page_name, elements in discovered_elements.items():
                print(f"\n{page_name}:")
                for elem_name, elem_info in elements.items():
                    print(f"  {elem_name}: {elem_info['selector']}")
            
            input("\n按回车键关闭浏览器...")
            
        except Exception as e:
            print(f"元素发现过程出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    discover_elements()
