#   AUTO-MAS: A Multi-Script, Multi-Config Management and Automation Software
#   Copyright © 2024-2025 DLmaster361
#   Copyright © 2025-2026 AUTO-MAS Team

#   This file is part of AUTO-MAS.

#   AUTO-MAS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.

#   AUTO-MAS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with AUTO-MAS. If not, see <https://www.gnu.org/licenses/>.

#   Contact: DLmaster_361@163.com


import asyncio
from collections.abc import Awaitable, Callable
from functools import partial
from html import escape

from app.core import Config
from app.services import Notify
from app.utils.logger import get_logger

logger = get_logger("游戏签到通知")

NOTIFICATION_MAX_ATTEMPTS = 2
NOTIFICATION_RETRY_DELAY_SECONDS = 1


def build_game_sign_notification(results: list[dict]) -> tuple[str, str, str]:
    """构建游戏签到通知的标题、纯文本和 HTML 内容。"""
    title = "📅 游戏社区签到"

    grouped: dict[tuple[str, str], list[dict]] = {}
    for item in results:
        account = str(item.get("account", "未知"))
        alias = account.split("/")[0] if "/" in account else account
        account_key = str(item.get("account_uid") or alias)
        grouped.setdefault((account_key, alias), []).append(item)

    lines = []
    html_lines = []
    success_count = 0
    fail_count = 0

    for (_, alias), items in grouped.items():
        lines.append(f"No.{alias}:")
        html_lines.append(f"<p><strong>No.{escape(alias)}:</strong></p>")
        html_lines.append("<ul>")
        for item in items:
            game = str(item.get("game", "未知"))
            status = item.get("status", "失败")
            reward = str(item.get("reward", ""))
            reason = str(item.get("reason", ""))

            if status == "成功":
                reward_text = f" ({reward})" if reward else ""
                html_reward_text = f" ({escape(reward)})" if reward else ""
                lines.append(f"  ✅ {game}: 成功{reward_text}")
                html_lines.append(
                    '<li><span style="background:green;color:white;padding:2px 6px;'
                    'border-radius:3px;">✅</span> '
                    f"{escape(game)}: 成功{html_reward_text}</li>"
                )
                success_count += 1
            elif status == "已签到":
                lines.append(f"  ✅ {game}: 已签")
                html_lines.append(
                    '<li><span style="background:green;color:white;padding:2px 6px;'
                    'border-radius:3px;">✅</span> '
                    f"{escape(game)}: 已签</li>"
                )
                success_count += 1
            else:
                reason_text = f" ({reason})" if reason else ""
                html_reason_text = f" ({escape(reason)})" if reason else ""
                lines.append(f"  ❌ {game}: 失败{reason_text}")
                html_lines.append(
                    '<li><span style="background:red;color:white;padding:2px 6px;'
                    'border-radius:3px;">❌</span> '
                    f"{escape(game)}: 失败{html_reason_text}</li>"
                )
                fail_count += 1
        html_lines.append("</ul>")

    summary = f"共 {len(grouped)} 个账号，成功 {success_count}，失败 {fail_count}"
    lines.extend([f"\n{summary}", "AUTO-MAS 敬上"])
    html_lines.extend([f"<p>{summary}</p>", "<p>AUTO-MAS 敬上</p>"])
    return title, "\n".join(lines), "".join(html_lines)


async def _send_with_retry(
    channel: str, sender: Callable[[], Awaitable[object]]
) -> str | None:
    """发送单个通知渠道，失败时进行一次自动重试。"""
    for attempt in range(1, NOTIFICATION_MAX_ATTEMPTS + 1):
        try:
            result = await sender()
            if result is False:
                raise RuntimeError("通知服务返回失败状态")
            return None
        except Exception as e:
            if attempt < NOTIFICATION_MAX_ATTEMPTS:
                logger.warning(f"推送{channel}通知失败，将自动重试: {e}")
                await asyncio.sleep(NOTIFICATION_RETRY_DELAY_SECONDS)
            else:
                logger.error(f"推送{channel}通知失败: {e}")
    return channel


async def push_game_sign_notification(results: list[dict]) -> list[str]:
    """推送游戏签到结果通知

    遵循 Skland-Sign-In 通知格式风格：
    - 标题：📅 游戏社区签到
    - 按别名分组：No.{别名}:
    - 成功：✅ 游戏名: 成功 (奖励)
    - 失败：❌ 游戏名: 失败 (原因)
    - 已签到：✅ 游戏名: 已签
    - 底部：AUTO-MAS 敬上

    Args:
        results: 签到结果列表
    """
    if not results:
        return []

    title, plain_text, html_content = build_game_sign_notification(results)
    senders: list[tuple[str, Callable[[], Awaitable[object]]]] = []

    if Config.get("Notify", "IfPushPlyer"):
        senders.append(
            ("系统", partial(Notify.push_plyer, title, plain_text, title, 5))
        )

    if Config.get("Notify", "IfSendMail"):
        to_address = Config.get("Notify", "ToAddress")
        senders.append(
            ("邮件", partial(Notify.send_mail, "网页", title, html_content, to_address))
        )

    if Config.get("Notify", "IfServerChan"):
        send_key = Config.get("Notify", "ServerChanKey")
        senders.append(
            ("Server酱", partial(Notify.ServerChanPush, title, plain_text, send_key))
        )

    for uid, webhook in Config.Notify_CustomWebhooks.items():
        if webhook.get("Info", "Enabled"):
            senders.append(
                (
                    f"Webhook {uid}",
                    partial(Notify.WebhookPush, title, plain_text, webhook),
                )
            )

    if Config.get("Notify", "IfKoishiSupport"):
        senders.append(("Koishi", partial(Notify.send_koishi, plain_text)))

    delivery_results = await asyncio.gather(
        *(_send_with_retry(channel, sender) for channel, sender in senders)
    )
    failures = [channel for channel in delivery_results if channel is not None]
    if failures:
        logger.warning(f"游戏签到通知部分发送失败: {', '.join(failures)}")
    return failures
