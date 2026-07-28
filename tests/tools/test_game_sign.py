import asyncio
import unittest
from unittest.mock import patch

from app.tools import game_sign


class GameSignFormatTest(unittest.TestCase):
    def test_same_alias_with_different_uids_stays_separate(self) -> None:
        results = [
            {
                "account": "同名用户",
                "account_uid": "account-1",
                "game": "原神",
                "platform": "米游社",
                "status": "成功",
                "reward": "奖励一",
                "reason": "",
            },
            {
                "account": "同名用户",
                "account_uid": "account-2",
                "game": "崩坏：星穹铁道",
                "platform": "米游社",
                "status": "成功",
                "reward": "奖励二",
                "reason": "",
            },
        ]

        formatted = game_sign.format_sign_results(results)

        self.assertEqual(len(formatted["米游社"]), 2)
        self.assertEqual(
            {item["account_uid"] for item in formatted["米游社"]},
            {"account-1", "account-2"},
        )


class GameSignConcurrencyTest(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_calls_share_the_active_sign_task(self) -> None:
        started = asyncio.Event()
        release = asyncio.Event()
        expected = [{"account_uid": "account-1"}]

        async def execute_once(force: bool) -> list[dict]:
            started.set()
            await release.wait()
            return expected

        game_sign._active_game_sign_task = None
        try:
            with patch.object(
                game_sign, "_execute_game_sign_once", side_effect=execute_once
            ) as execute_mock:
                first = asyncio.create_task(game_sign.execute_game_sign(force=False))
                await started.wait()
                second = asyncio.create_task(game_sign.execute_game_sign(force=True))
                await asyncio.sleep(0)
                release.set()

                first_result, second_result = await asyncio.gather(first, second)

            self.assertEqual(execute_mock.call_count, 1)
            self.assertEqual(first_result, (expected, True))
            self.assertEqual(second_result, (expected, False))
        finally:
            game_sign._active_game_sign_task = None


if __name__ == "__main__":
    unittest.main()
