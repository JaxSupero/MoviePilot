from typing import Any, List, Dict, Tuple, Optional

from app.core.config import settings
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils


class WebHookv2(_PluginBase):
    plugin_name = "WebHookv2"
    plugin_desc = "MoviePilot V2 系统通知推送至自定义接口，支持Bearer/PathToken，POST/GET"
    plugin_icon = "webhook.png"
    plugin_version = "2.4"
    plugin_author = "WINGS"
    author_url = "https://github.com/JaxSupero/MoviePilot-Plugin"
    plugin_config_prefix = "webhookv2"
    plugin_order = 14
    auth_level = 1

    _enabled: bool = False
    _api_base: str = ""
    _token: str = ""
    _auth_mode: str = "bearer"
    _send_mode: str = "post"
    _msg_type: str = "text"

    def init_plugin(self, config: dict = None):
        self.version = settings.VERSION_FLAG if hasattr(settings, "VERSION_FLAG") else "v1"
        if config:
            self._enabled = config.get("enabled", False)
            self._api_base = config.get("api_base", "").strip()
            self._token = config.get("token", "").strip()
            self._auth_mode = config.get("auth_mode", "bearer")
            self._send_mode = config.get("send_mode", "post")
            self._msg_type = config.get("msg_type", "text")

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 7},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "api_base",
                                            "label": "接口基础地址",
                                            "placeholder": "http://192.168.1.2:818"
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 5},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "token",
                                            "label": "接口令牌 Token",
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "auth_mode",
                                            "label": "Token 位置",
                                            "items": [
                                                {"title": "Bearer Header", "value": "bearer"},
                                                {"title": "URL Path", "value": "path"}
                                            ]
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "send_mode",
                                            "label": "请求方式",
                                            "items": [
                                                {"title": "POST", "value": "post"},
                                                {"title": "GET", "value": "get"}
                                            ]
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "msg_type",
                                            "label": "消息格式",
                                            "items": [
                                                {"title": "Text", "value": "text"},
                                                {"title": "Json", "value": "json"}
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "api_base": "",
            "token": "",
            "auth_mode": "bearer",
            "send_mode": "post",
            "msg_type": "text"
        }

    def get_page(self) -> List[dict]:
        return []

    @eventmanager.register(EventType)
    def send(self, event: Event):
        if not self._enabled or not self._api_base:
            return

        event_data = event.event_data
        event_type = event.event_type.value if hasattr(event.event_type, "value") else event.event_type

        def to_dict(obj):
            if isinstance(obj, dict):
                return {k: to_dict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [to_dict(i) for i in obj]
            elif hasattr(obj, "to_dict"):
                return to_dict(obj.to_dict())
            elif hasattr(obj, "__dict__"):
                return to_dict(obj.__dict__)
            else:
                return obj

        data = {
            "event": event_type,
            "data": to_dict(event_data)
        }

        url = self._api_base
        headers = {}
        if self._auth_mode == "bearer" and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._auth_mode == "path" and self._token:
            if "?" in url:
                url += f"&token={self._token}"
            else:
                url += f"?token={self._token}"

        try:
            if self._send_mode == "post":
                res = RequestUtils(headers=headers, timeout=10).post_res(url, json=data)
            else:
                res = RequestUtils(headers=headers, timeout=10).get_res(url, params=data)

            if res and res.ok:
                logger.info(f"WebHookv2 发送成功 | {url}")
            else:
                logger.error(f"WebHookv2 发送失败 | {url}")
        except Exception as e:
            logger.error(f"WebHookv2 发送异常：{str(e)}")

    def stop_service(self):
        pass
