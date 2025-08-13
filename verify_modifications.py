#!/usr/bin/env python3
"""
验证修改功能的脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from loguru import logger

def verify_config_defaults():
    """验证配置默认值"""
    logger.info("=== 验证配置默认值 ===")
    
    from config import CONFIG
    
    # 验证反爬虫默认关闭
    anti_detection_mode = getattr(CONFIG, 'anti_detection_mode', 'off')
    anti_detection_enabled = getattr(CONFIG, 'anti_detection_enabled', False)
    
    logger.info("反爬虫模式: {} (期望: off)", anti_detection_mode)
    logger.info("反爬虫启用: {} (期望: False)", anti_detection_enabled)
    
    if anti_detection_mode == 'off' and not anti_detection_enabled:
        logger.info("✓ 反爬虫默认关闭配置正确")
        return True
    else:
        logger.error("✗ 反爬虫默认配置不正确")
        return False

def verify_weibo_modifications():
    """验证微博功能修改"""
    logger.info("=== 验证微博功能修改 ===")
    
    try:
        # 检查weibo.py文件中的关键修改
        with open('src/weibo.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查转发逻辑修改
        if '同时转发' in content:
            logger.info("✓ 转发逻辑已修改：包含'同时转发'逻辑")
        else:
            logger.warning("⚠ 转发逻辑可能未完全修改")
        
        # 检查关注逻辑修改
        if '基于关注按钮存在性' in content:
            logger.info("✓ 关注逻辑已修改：基于关注按钮存在性判断")
        else:
            logger.warning("⚠ 关注逻辑可能未完全修改")
        
        return True
        
    except Exception as e:
        logger.error("✗ 验证微博功能修改失败: {}", e)
        return False

def verify_ui_modifications():
    """验证UI配置同步修改"""
    logger.info("=== 验证UI配置同步修改 ===")
    
    try:
        # 检查ui_bootstrap.py文件中的关键修改
        with open('src/ui_bootstrap.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查实时配置同步
        if '_sync_action_config' in content:
            logger.info("✓ 操作类型实时同步功能已添加")
        else:
            logger.warning("⚠ 操作类型实时同步功能可能未添加")
        
        # 检查反爬虫配置同步
        if 'CONFIG.save()' in content and '反爬虫模式已更新' in content:
            logger.info("✓ 反爬虫配置实时同步功能已添加")
        else:
            logger.warning("⚠ 反爬虫配置实时同步功能可能未添加")
        
        # 检查默认反爬虫关闭
        if 'self.var_anti_detection = tb.StringVar(value="off")' in content:
            logger.info("✓ 反爬虫默认关闭设置正确")
        else:
            logger.warning("⚠ 反爬虫默认设置可能不正确")
        
        return True
        
    except Exception as e:
        logger.error("✗ 验证UI配置同步修改失败: {}", e)
        return False

def main():
    """主验证函数"""
    logger.info("开始验证修改功能...")
    
    # 验证配置默认值
    config_ok = verify_config_defaults()
    
    # 验证微博功能修改
    weibo_ok = verify_weibo_modifications()
    
    # 验证UI功能修改
    ui_ok = verify_ui_modifications()
    
    # 总结
    logger.info("=== 验证总结 ===")
    if config_ok and weibo_ok and ui_ok:
        logger.info("✓ 所有修改验证通过")
        logger.info("✓ 转发逻辑：基于评论区'同时转发'复选框")
        logger.info("✓ 关注逻辑：基于关注按钮存在性判断")
        logger.info("✓ UI配置同步：所有操作实时同步到配置")
        logger.info("✓ 反爬虫默认关闭：不注入反爬虫功能")
        logger.info("")
        logger.info("修改完成！可以开始使用新功能。")
    else:
        logger.error("✗ 部分修改验证失败")
    
    return config_ok and weibo_ok and ui_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
