import unittest

from claw2immich.constants import build_server_instructions


class InstructionsTests(unittest.TestCase):
    def test_build_server_instructions_with_domain(self) -> None:
        instructions = build_server_instructions("https://immich.example")
        self.assertIn("External domain for link building: https://immich.example.", instructions)

    def test_build_server_instructions_without_domain(self) -> None:
        instructions = build_server_instructions(None)
        self.assertIn("External domain for link building:", instructions)
        self.assertIn("GET /api/server-config", instructions)
