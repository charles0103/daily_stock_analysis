# -*- coding: utf-8 -*-
"""
Discord 发送提醒服务

职责：
1. 通过 webhook 或 Discord bot API 发送 Discord 消息
"""
import logging
import time
from typing import Optional

import requests

from src.config import Config
from src.formatters import chunk_content_by_max_words


logger = logging.getLogger(__name__)


class DiscordSender:
    
    def __init__(self, config: Config):
        """
        初始化 Discord 配置

        Args:
            config: 配置对象
        """
        self._discord_config = {
            'bot_token': getattr(config, 'discord_bot_token', None),
            'channel_id': getattr(config, 'discord_main_channel_id', None),
            'webhook_url': getattr(config, 'discord_webhook_url', None),
        }
        self._discord_max_words = getattr(config, 'discord_max_words', 2000)
        self._webhook_verify_ssl = getattr(config, 'webhook_verify_ssl', True)
    
    def _is_discord_configured(self) -> bool:
        """检查 Discord 配置是否完整（支持 Bot 或 Webhook）"""
        # 只要配置了 Webhook 或完整的 Bot Token+Channel，即视为可用
        bot_ok = bool(self._discord_config['bot_token'] and self._discord_config['channel_id'])
        webhook_ok = bool(self._discord_config['webhook_url'])
        return bot_ok or webhook_ok
    
    def send_to_discord(self, content: str, *, timeout_seconds: Optional[float] = None) -> bool:
        """
        推送消息到 Discord（支持 Webhook 和 Bot API）
        
        Args:
            content: Markdown 格式的消息内容
            
        Returns:
            是否发送成功
        """
        # 分割内容，避免单条消息超过 Discord 限制
        try:
            chunks = chunk_content_by_max_words(content, self._discord_max_words)
        except ValueError as e:
            logger.error(f"分割 Discord 消息失败: {e}, 尝试整段发送。")
            chunks = [content]
        # 過濾空塊，避免 Discord 400 "Cannot send an empty message"
        chunks = [c for c in chunks if c.strip()]
        if not chunks:
            logger.warning("Discord 消息内容为空，跳过推送")
            return False

        # 优先使用 Webhook（配置简单，权限低）
        if self._discord_config['webhook_url']:
            success = True
            for i, chunk in enumerate(chunks):
                if i > 0:
                    time.sleep(0.5)
                if not self._send_discord_webhook(chunk, timeout_seconds=timeout_seconds):
                    success = False
            return success

        # 其次使用 Bot API（权限高，需要 channel_id）
        if self._discord_config['bot_token'] and self._discord_config['channel_id']:
            success = True
            for i, chunk in enumerate(chunks):
                if i > 0:
                    time.sleep(0.5)
                if not self._send_discord_bot(chunk, timeout_seconds=timeout_seconds):
                    success = False
            return success

        logger.warning("Discord 配置不完整，跳过推送")
        return False

  
    def _send_discord_webhook(self, content: str, *, timeout_seconds: Optional[float] = None, _retries: int = 3) -> bool:
        """
        使用 Webhook 发送消息到 Discord

        Discord Webhook 支持 Markdown 格式

        Args:
            content: Markdown 格式的消息内容

        Returns:
            是否发送成功
        """
        try:
            payload = {
                'content': content,
                'username': 'A股分析机器人',
                'avatar_url': 'https://picsum.photos/200'
            }

            response = requests.post(
                self._discord_config['webhook_url'],
                json=payload,
                timeout=timeout_seconds or 10,
                verify=self._webhook_verify_ssl
            )

            if response.status_code in [200, 204]:
                logger.info("Discord Webhook 消息发送成功")
                return True
            elif response.status_code == 429 and _retries > 0:
                try:
                    retry_after = response.json().get('retry_after', 1.0)
                except Exception:
                    retry_after = 1.0
                logger.warning(f"Discord Webhook 速率限制，等待 {retry_after}s 後重試（剩餘 {_retries} 次）")
                time.sleep(retry_after + 0.1)
                return self._send_discord_webhook(content, timeout_seconds=timeout_seconds, _retries=_retries - 1)
            else:
                logger.error(f"Discord Webhook 发送失败: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Discord Webhook 发送异常: {e}")
            return False
    
    def _send_discord_bot(self, content: str, *, timeout_seconds: Optional[float] = None, _retries: int = 3) -> bool:
        """
        使用 Bot API 发送消息到 Discord

        Args:
            content: Markdown 格式的消息内容

        Returns:
            是否发送成功
        """
        try:
            headers = {
                'Authorization': f'Bot {self._discord_config["bot_token"]}',
                'Content-Type': 'application/json'
            }

            payload = {
                'content': content
            }

            url = f'https://discord.com/api/v10/channels/{self._discord_config["channel_id"]}/messages'
            response = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds or 10)

            if response.status_code == 200:
                logger.info("Discord Bot 消息发送成功")
                return True
            elif response.status_code == 429 and _retries > 0:
                try:
                    retry_after = response.json().get('retry_after', 1.0)
                except Exception:
                    retry_after = 1.0
                logger.warning(f"Discord Bot 速率限制，等待 {retry_after}s 後重試（剩餘 {_retries} 次）")
                time.sleep(retry_after + 0.1)
                return self._send_discord_bot(content, timeout_seconds=timeout_seconds, _retries=_retries - 1)
            else:
                logger.error(f"Discord Bot 发送失败: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Discord Bot 发送异常: {e}")
            return False
