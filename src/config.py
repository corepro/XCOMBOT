from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Literal
import json
from pathlib import Path


class CommentConfig(BaseModel):
    mode: Literal["local", "ai"] = "local"
    local_library_path: str = "data/comments.txt"
    hf_api_url: str = ""
    hf_api_key: str = ""
    model: str = "Qwen/QwQ-32B"
    temperature: float = 0.8
    max_tokens: int = 200  # 增加到200以支持100字评论
    prompt_template: str = (
        "请你扮演小红书用户，针对以下内容生成一条真实自然的评论(100字以内)，要活泼自然，可以使用emoji：\n{content}"
    )
    # 平台特定的评论模板
    platform_templates: dict = {
        "weibo": "请你扮演微博用户，针对以下内容生成一条有趣自然的评论(50字以内)，要活泼自然，符合微博风格：\n{content}",
        "xhs": "请你扮演小红书用户，针对以下内容生成一条真实自然的评论(100字以内)，要活泼自然，可以使用emoji：\n{content}",
        "zhihu": "请你扮演知乎用户，针对以下内容生成一条有深度的评论(100字以内)，要理性客观，体现专业性：\n{content}",
        "toutiao": "请你扮演今日头条用户，针对以下内容生成一条接地气的评论(100字以内)，要通俗易懂，贴近生活：\n{content}",
        "twitter": "Please act as a Twitter user and generate a natural comment (within 280 characters) for the following content:\n{content}"
    }


class ActionConfig(BaseModel):
    # 控制执行类型
    do_comment: bool = True
    do_retweet: bool = False
    do_like: bool = True
    do_collect: bool = True
    do_follow: bool = True
    max_comments_per_hour: int = 12
    max_retweets_per_hour: int = 6


class AppConfig(BaseModel):
    platform: Literal["twitter", "weibo", "xhs", "zhihu", "toutiao"] = "twitter"
    browser_type: Literal["chrome", "firefox"] = "chrome"  # 新增浏览器类型选择
    headless: bool = False
    slow_mo_ms: int = 100
    proxy: Optional[str] = None
    storage_state_path: str = "storage/storage_state.json"
    users_to_follow: List[str] = ["jack"]
    poll_interval_sec: int = 120
    comment: CommentConfig = CommentConfig()
    action: ActionConfig = ActionConfig()

    # 反爬虫配置
    anti_detection_mode: Literal["off", "basic", "enhanced", "extreme"] = "off"
    anti_detection_enabled: bool = False

    @staticmethod
    def load(path: str | Path = "config/config.json") -> "AppConfig":
        p = Path(path)
        if not p.exists():
            # 创建默认配置文件
            default_config = AppConfig()
            try:
                default_config.save(path)
                print(f"已创建默认配置文件: {path}")
            except Exception as e:
                print(f"警告：无法创建默认配置文件: {e}")
            return default_config

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return AppConfig(**data)
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            print(f"使用默认配置，原文件已备份为: {path}.backup")
            try:
                # 备份损坏的配置文件
                backup_path = Path(str(path) + ".backup")
                p.rename(backup_path)
                # 创建新的默认配置
                default_config = AppConfig()
                default_config.save(path)
                return default_config
            except Exception as backup_e:
                print(f"备份配置文件失败: {backup_e}")
                return AppConfig()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return AppConfig()

    def save(self, path: str | Path = "config/config.json") -> None:
        import json as _json
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = self.model_dump()
        except Exception:
            # 兼容 Pydantic v1
            data = self.dict()
        p.write_text(_json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def reload(self, path: str | Path = "config/config.json"):
        """重新加载配置文件"""
        try:
            import json as _json
            p = Path(path)
            if not p.exists():
                print(f"配置文件不存在: {path}")
                return False

            data = _json.loads(p.read_text(encoding="utf-8"))

            # 验证配置数据的有效性
            if not isinstance(data, dict):
                print(f"配置文件格式错误：根对象必须是字典")
                return False

            # 更新当前实例的属性
            updated_count = 0
            for key, value in data.items():
                if hasattr(self, key):
                    try:
                        if key in ["comment", "action"]:
                            # 对于嵌套对象，需要特殊处理
                            current_obj = getattr(self, key)
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    if hasattr(current_obj, sub_key):
                                        setattr(current_obj, sub_key, sub_value)
                                        updated_count += 1
                        else:
                            setattr(self, key, value)
                            updated_count += 1
                    except Exception as e:
                        print(f"更新配置项 {key} 失败: {e}")
                        continue
                else:
                    print(f"忽略未知配置项: {key}")

            print(f"配置重新加载成功，更新了 {updated_count} 个配置项")
            return True

        except _json.JSONDecodeError as e:
            print(f"配置文件JSON格式错误: {e}")
            return False
        except Exception as e:
            print(f"重新加载配置失败: {e}")
            return False


CONFIG = AppConfig.load()

# Ensure storage dirs
Path(CONFIG.storage_state_path).parent.mkdir(parents=True, exist_ok=True)
Path(CONFIG.comment.local_library_path).parent.mkdir(parents=True, exist_ok=True)

