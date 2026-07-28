import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.tools import game_sign_notify


class GameSignNotificationContentTest(unittest.TestCase):
    def test_html_content_is_escaped(self) -> None:
        results = [
            {
                "account": "<script>alert(1)</script>/账号",
                "account_uid": "account-1",
                "game": "<b>游戏</b>",
                "status": "失败",
                "reward": "",
                "reason": "<img src=x onerror=alert(1)>",
            }
        ]

        _, _, html_content = game_sign_notify.build_game_sign_notification(results)

        self.assertNotIn("<script>", html_content)
        self.assertNotIn("<b>游戏</b>", html_content)
        self.assertNotIn("<img src=x", html_content)
        self.assertIn("&lt;script&gt;", html_content)
        self.assertIn("&lt;b&gt;游戏&lt;/b&gt;", html_content)

    def test_same_alias_with_different_uids_stays_separate(self) -> None:
        results = [
            {
                "account": "同名用户",
                "account_uid": "account-1",
                "game": "原神",
                "status": "成功",
            },
            {
                "account": "同名用户",
                "account_uid": "account-2",
                "game": "鸣潮",
                "status": "成功",
            },
        ]

        _, plain_text, _ = game_sign_notify.build_game_sign_notification(results)

        self.assertEqual(plain_text.count("No.同名用户:"), 2)
        self.assertIn("共 2 个账号", plain_text)


class GameSignNotificationDeliveryTest(unittest.IsolatedAsyncioTestCase):
    async def test_failed_channel_is_retried(self) -> None:
        config = SimpleNamespace(
            get=MagicMock(
                side_effect=lambda group, name: name == "IfPushPlyer"
            ),
            Notify_CustomWebhooks={},
        )
        push_plyer = AsyncMock(side_effect=[RuntimeError("temporary"), None])
        results = [
            {
                "account": "用户",
                "account_uid": "account-1",
                "game": "原神",
                "status": "成功",
            }
        ]

        with (
            patch.object(game_sign_notify, "Config", config),
            patch.object(game_sign_notify.Notify, "push_plyer", push_plyer),
            patch.object(game_sign_notify.asyncio, "sleep", AsyncMock()),
        ):
            failures = await game_sign_notify.push_game_sign_notification(results)

        self.assertEqual(failures, [])
        self.assertEqual(push_plyer.await_count, 2)

    async def test_false_channel_result_is_retried_and_reported(self) -> None:
        config = SimpleNamespace(
            get=MagicMock(
                side_effect=lambda group, name: name == "IfPushPlyer"
            ),
            Notify_CustomWebhooks={},
        )
        push_plyer = AsyncMock(return_value=False)
        results = [
            {
                "account": "用户",
                "account_uid": "account-1",
                "game": "原神",
                "status": "成功",
            }
        ]

        with (
            patch.object(game_sign_notify, "Config", config),
            patch.object(game_sign_notify.Notify, "push_plyer", push_plyer),
            patch.object(game_sign_notify.asyncio, "sleep", AsyncMock()),
        ):
            failures = await game_sign_notify.push_game_sign_notification(results)

        self.assertEqual(failures, ["系统"])
        self.assertEqual(push_plyer.await_count, 2)


if __name__ == "__main__":
    unittest.main()
