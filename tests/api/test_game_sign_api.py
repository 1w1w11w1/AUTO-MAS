import unittest
from unittest.mock import AsyncMock, patch

from app.api.tools import (
    GAME_SIGN_TOKEN_MASK,
    Config,
    GameSignAccountGroupConfig,
    GameSignAccountGetIn,
    GameSignAccountUpdateIn,
    get_game_sign_account,
    list_game_sign_accounts,
    manual_game_sign,
    update_game_sign_account,
)


class GameSignAccountApiTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_masks_all_account_tokens(self) -> None:
        data = {
            "instances": [{"uid": "account-1", "type": "GameSignAccountGroup"}],
            "account-1": {
                "GameSignAccount": {
                    "Name": "用户",
                    "MiyousheToken": "miyoushe-secret",
                    "KuroToken": "kuro-secret",
                    "SklandToken": "",
                }
            },
        }
        with patch.object(
            Config, "get_game_sign_accounts", AsyncMock(return_value=data)
        ):
            response = await list_game_sign_accounts()

        account = response.data["account-1"]["GameSignAccount"]
        self.assertEqual(account["MiyousheToken"], GAME_SIGN_TOKEN_MASK)
        self.assertEqual(account["KuroToken"], GAME_SIGN_TOKEN_MASK)
        self.assertEqual(account["SklandToken"], "")

    async def test_get_masks_account_tokens(self) -> None:
        data = {
            "GameSignAccount": {
                "Name": "用户",
                "MiyousheToken": "secret",
            }
        }
        with patch.object(
            Config, "get_game_sign_account", AsyncMock(return_value=data)
        ):
            response = await get_game_sign_account(
                GameSignAccountGetIn(accountId="account-1")
            )

        self.assertEqual(response.data.MiyousheToken, GAME_SIGN_TOKEN_MASK)

    async def test_update_treats_masked_tokens_as_unchanged(self) -> None:
        update = AsyncMock()
        request = GameSignAccountUpdateIn(
            accountId="account-1",
            data=GameSignAccountGroupConfig(
                Name="新名称",
                MiyousheToken=GAME_SIGN_TOKEN_MASK,
                KuroToken=GAME_SIGN_TOKEN_MASK,
            ),
        )
        with patch.object(Config, "update_game_sign_account", update):
            response = await update_game_sign_account(request)

        self.assertEqual(response.code, 200)
        update.assert_awaited_once_with(
            "account-1", {"GameSignAccount": {"Name": "新名称"}}
        )


class ManualGameSignApiTest(unittest.IsolatedAsyncioTestCase):
    async def test_empty_result_is_reported_as_failure(self) -> None:
        with (
            patch(
                "app.tools.game_sign.execute_game_sign",
                AsyncMock(return_value=([], True)),
            ),
            patch.object(Config.ToolsConfig, "set", AsyncMock()),
        ):
            response = await manual_game_sign()

        self.assertEqual(response.code, 400)
        self.assertEqual(response.status, "error")

    async def test_notification_failures_are_reported_as_warning(self) -> None:
        results = [{"account_uid": "account-1"}]
        with (
            patch(
                "app.tools.game_sign.execute_game_sign",
                AsyncMock(return_value=(results, True)),
            ),
            patch(
                "app.tools.game_sign_notify.push_game_sign_notification",
                AsyncMock(return_value=["邮件"]),
            ),
            patch.object(Config.ToolsConfig, "set", AsyncMock()),
            patch.object(Config.ToolsConfig, "get", return_value=True),
        ):
            response = await manual_game_sign()

        self.assertEqual(response.code, 200)
        self.assertEqual(response.status, "warning")
        self.assertIn("邮件", response.message)


if __name__ == "__main__":
    unittest.main()
