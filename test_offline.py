"""Meaningful local checks; these are NOT a measured LLM tool-choice score."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent import RentalAgent, Settings
from rental_tools import RentalTools, initialize_database


def response(content=None, name=None, arguments=None):
    calls = [] if name is None else [SimpleNamespace(id="call_1", function=SimpleNamespace(
        name=name, arguments=json.dumps(arguments) if not isinstance(arguments, str) else arguments))]
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=calls))])


class FakeClient:
    """Scripted responses verify loop mechanics, never model intelligence."""
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        import copy
        self.requests.append(copy.deepcopy(kwargs))
        item = next(self.responses)
        if isinstance(item, Exception):
            raise item
        return item


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.db"
        self.counts = initialize_database(self.db)
        self.tools = RentalTools(self.db)
        self.settings = Settings("https://example.invalid/v1/", "offline-test", "test-only", 3, 0)

    def tearDown(self):
        self.temp.cleanup()

    def test_database_counts_and_csv_rebuild(self):
        self.assertEqual(self.counts, {"rental_info": 14, "vehicles": 16})
        initialize_database(self.db)
        self.assertEqual(self.tools.query("SELECT COUNT(*) AS n FROM vehicles")[0]["n"], 16)

    def test_information_and_missing_policy(self):
        self.assertEqual(self.tools.get_rental_info("hours")["topic"], "opening_hours")
        self.assertEqual(self.tools.get_rental_info("pets")["status"], "not_found")

    def test_exact_quote_with_gps(self):
        quote = self.tools.calculate_rental("Corolla", 3, gps=True)
        self.assertEqual(quote["rental_total"], "192.00")
        self.assertEqual(quote["refundable_deposit_separate"], "300.00")

    def test_weekly_discount_only_on_base(self):
        quote = self.tools.calculate_rental("Golf", 7, gps=True)
        self.assertEqual(quote["discount_amount"], "38.50")
        self.assertEqual(quote["rental_total"], "381.50")
        self.assertEqual(self.tools.calculate_rental("Golf", 6)["discount_amount"], "0.00")

    def test_excess_mileage_boundary_and_charge(self):
        self.assertEqual(self.tools.calculate_rental("Spring", 2, total_km=400)["rental_total"], "70.00")
        self.assertEqual(self.tools.calculate_rental("Spring", 2, total_km=600)["rental_total"], "120.00")

    def test_input_validation(self):
        for days in (0, -1, 31, 1.5, True, "3"):
            self.assertEqual(self.tools.calculate_rental("Golf", days)["status"], "invalid_argument")
        self.assertEqual(self.tools.calculate_rental("Golf", 2, gps="yes")["status"], "invalid_argument")
        self.assertEqual(self.tools.calculate_rental("Golf", 2, total_km=-1)["status"], "invalid_argument")

    def test_ambiguity_unavailable_and_no_match(self):
        self.assertEqual(self.tools.calculate_rental("Mercedes", 2)["status"], "ambiguous")
        self.assertEqual(self.tools.calculate_rental("Model Y", 2)["status"], "unavailable")
        self.assertEqual(self.tools.calculate_rental("Spaceship", 2)["status"], "not_found")

    def test_alias_case_and_available_filter(self):
        self.assertEqual(self.tools.calculate_rental("toyota COROLLA", 1)["vehicle"], "Toyota Corolla Hybrid")
        rows = self.tools.search_vehicles("electric", True)["vehicles"]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["available"] for row in rows))

    def test_sql_injection_and_unknown_tools(self):
        self.assertEqual(self.tools.search_vehicles("' OR 1=1 --")["status"], "not_found")
        self.assertEqual(self.tools.get_rental_info("'; DROP TABLE vehicles; --")["status"], "not_found")
        self.assertEqual(self.tools.query("SELECT COUNT(*) AS n FROM vehicles")[0]["n"], 16)
        self.assertEqual(self.tools.dispatch("execute_sql", {"sql": "DROP TABLE vehicles"})["status"], "unknown_tool")

    def test_staff_referral_is_not_a_real_transfer(self):
        result = self.tools.transfer_to_staff("A complaint")
        self.assertEqual(result["status"], "referral_only")
        self.assertFalse(result["message_sent"])
        self.assertFalse(result["live_transfer_performed"])

    def test_loop_trace_and_history_are_kept(self):
        client = FakeClient([response(name="get_rental_info", arguments={"topic": "opening_hours"}),
                             response(content="Example answer."), response(content="Example follow-up.")])
        agent = RentalAgent(client, self.settings, self.tools)
        first = agent.run("Opening hours?")
        self.assertEqual(first["model_calls"], 2)
        self.assertEqual(first["trace"][0]["result"]["status"], "ok")
        agent.run("And on Sunday?", first["history"])
        self.assertTrue(any(m["role"] == "tool" for m in client.requests[-1]["messages"]))
        self.assertEqual(client.requests[-1]["messages"][-1]["content"], "And on Sunday?")

    def test_unknown_and_invalid_tools_are_visible(self):
        client = FakeClient([response(name="delete_everything", arguments={}),
                             response(name="search_vehicles", arguments="bad json"), response(content="Done.")])
        result = RentalAgent(client, self.settings, self.tools).run("Test")
        self.assertEqual(result["trace"][0]["result"]["status"], "unknown_tool")
        self.assertEqual(result["trace"][1]["result"]["status"], "invalid_arguments")

    def test_max_steps_really_stops_the_loop(self):
        client = FakeClient([response(name="get_rental_info", arguments={"topic": "hours"}) for _ in range(3)])
        result = RentalAgent(client, self.settings, self.tools).run("Test loop")
        self.assertEqual(result["status"], "max_steps")
        self.assertEqual(len(client.requests), 3)

    def test_api_error_does_not_expose_secret_or_partial_history(self):
        error = RuntimeError("secret-api-key-must-never-be-shown")
        client = FakeClient([error])
        result = RentalAgent(client, self.settings, self.tools).run("Test")
        self.assertEqual(result["status"], "api_error")
        self.assertEqual(result["history"], [])
        self.assertNotIn("secret-api-key", json.dumps(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
