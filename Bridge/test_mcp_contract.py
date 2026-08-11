import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("mcp") is not None, "MCP dependency is not installed")
class McpContractTests(unittest.TestCase):
    def test_required_tools_are_callable(self) -> None:
        import server

        for name in (
            "agent_ping",
            "agent_wake",
            "agent_get_context",
            "agent_git_status",
            "agent_propose_memory",
            "agent_apply_memory",
            "agent_verify",
        ):
            self.assertTrue(callable(getattr(server, name, None)), name)


if __name__ == "__main__":
    unittest.main()
