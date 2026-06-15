import unittest

from harbor.core.main_loop import HarborMainLoop
from harbor.core.models import HarborRequest


class FakeBridge:
    def __init__(self, requests):
        self.requests = list(requests)

    def receive(self):
        if not self.requests:
            return None

        return self.requests.pop(0)


class FakeReturnChannel:
    def __init__(self):
        self.responses = []

    def send(self, response):
        self.responses.append(response)


class TestHarborMainLoop(unittest.TestCase):
    def test_run_once_handles_one_message(self):
        bridge = FakeBridge([
            HarborRequest(
                source="test",
                sender="tester",
                text="你好",
            )
        ])
        return_channel = FakeReturnChannel()

        loop = HarborMainLoop(
            bridge=bridge,
            return_channel=return_channel,
        )

        result = loop.run_once()

        self.assertTrue(result)
        self.assertEqual(len(return_channel.responses), 1)
        self.assertIn("Harbor Core", return_channel.responses[0].text)

    def test_run_once_stops_when_no_message(self):
        bridge = FakeBridge([])
        return_channel = FakeReturnChannel()

        loop = HarborMainLoop(
            bridge=bridge,
            return_channel=return_channel,
        )

        result = loop.run_once()

        self.assertFalse(result)
        self.assertEqual(len(return_channel.responses), 0)


if __name__ == "__main__":
    unittest.main()
