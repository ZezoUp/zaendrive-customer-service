"""Retrieval and tool-loop integration checks; no live model or API key."""

import json
import tempfile
import unittest
from pathlib import Path

from agent import RentalAgent, Settings
from rag import DOCUMENT_DIR, PolicyRetriever, format_sources, load_chunks
from rental_tools import RentalTools, initialize_database
from test_offline import FakeClient, response


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = PolicyRetriever()

    def test_expected_passages_for_customer_questions(self):
        cases = [
            ("Can I cancel 24 hours before pickup?", "Cancellation rules"),
            ("If I return early, will unused days be refunded?", "Early return and refunds"),
            ("What battery charge is required on return?", "Fuel and battery charging on return"),
            ("What is the exact late-return fee?", "Late return and extensions"),
            ("What is the insurance excess?", "Standard insurance and missing coverage details"),
            ("Can I drive to Austria?", "Cross border travel"),
            ("What is the minimum driver age?", "Driver eligibility and documents"),
            ("May I add an additional driver?", "Additional drivers"),
            ("Darf ich frueher zurueckgeben und bekomme ich eine Erstattung?", "Early return and refunds"),
            ("Wie viel Akku muss bei Rueckgabe vorhanden sein?", "Fuel and battery charging on return"),
            ("Darf ich nach Oesterreich fahren?", "Cross border travel"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                result = self.retriever.search(query)
                self.assertEqual(result["status"], "ok")
                self.assertIn(expected, [m["title"] for m in result["matches"]])

    def test_unknown_pet_rule_does_not_retrieve_unrelated_general_rental_text(self):
        for query in ["Can I bring my dog in the rental car?", "pets animals dog allowed in rental car"]:
            with self.subTest(query=query):
                result = self.retriever.search(query)
                self.assertEqual(result["status"], "not_found")
                self.assertEqual(result["matches"], [])

    def test_missing_amount_is_explicit_in_retrieved_evidence(self):
        result = self.retriever.search("What is the exact late-return fee?")
        passage = next(m["text"] for m in result["matches"] if m["title"] == "Late return and extensions")
        self.assertIn("not specified", passage)
        self.assertIn("must not use the normal daily rental rate", passage)

    def test_top_k_and_argument_bounds(self):
        self.assertEqual(len(self.retriever.search("return", top_k=1)["matches"]), 1)
        for query in ["", " ", None, 17, "x" * 601]:
            self.assertEqual(self.retriever.search(query)["status"], "invalid_argument")
        for top_k in [0, 6, True, "3"]:
            self.assertEqual(self.retriever.search("return", top_k)["status"], "invalid_argument")

    def test_large_section_is_chunked_with_overlap_and_end_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            words = [f"word{i}" for i in range(300)]
            (Path(temp) / "manual.md").write_text("# Manual\n\n## Long section\n" + " ".join(words))
            chunks = load_chunks(temp, max_words=120, overlap=20)
            self.assertEqual(len(chunks), 3)
            self.assertEqual(chunks[0].text.split()[-20:], chunks[1].text.split()[:20])
            self.assertTrue(chunks[-1].text.endswith("word299"))
            self.assertEqual(len({c.source_id for c in chunks}), len(chunks))

    def test_no_silent_empty_document_index(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                PolicyRetriever(temp)

    def test_retrieval_is_deterministic_and_citations_identify_real_sections(self):
        first = self.retriever.search("early return refund")
        self.assertEqual(first, self.retriever.search("early return refund"))
        for match in first["matches"]:
            self.assertTrue((DOCUMENT_DIR / match["source_file"]).is_file())
            self.assertTrue(match["source_id"].startswith(match["source_file"] + "#"))

    def test_selected_passages_are_sent_as_tool_evidence_to_generator(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "demo.db"
            initialize_database(db)
            tools = RentalTools(db, self.retriever)
            client = FakeClient([
                response(name="search_rental_policies", arguments={"query": "early return refund"}),
                response(content="Early return does not automatically create a refund. "
                         "[01_rental_handbook.md#early-return-and-refunds]"),
            ])
            settings = Settings("https://example.invalid/v1/", "scripted-test", "not-a-key", 3, 0)
            result = RentalAgent(client, settings, tools).run("Can I get unused days refunded?")
            tool_message = next(m for m in client.requests[1]["messages"] if m["role"] == "tool")
            evidence = json.loads(tool_message["content"])
            self.assertEqual(evidence["matches"][0]["title"], "Early return and refunds")
            self.assertLess(len(evidence["matches"]), len(self.retriever.chunks))
            self.assertIn(evidence["matches"][0]["source_id"], format_sources(result))
            self.assertNotIn("## Cross border travel", tool_message["content"])

    def test_missing_rule_and_staff_referral_use_real_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "demo.db"
            initialize_database(db)
            client = FakeClient([
                response(name="search_rental_policies", arguments={"query": "pets dogs"}),
                response(name="transfer_to_staff", arguments={"reason": "Pet rule not in handbook"}),
                response(content="I could not find this information in ZaenDrive's documents. "
                         "Please contact the fictional staff address yourself; no message was sent."),
            ])
            result = RentalAgent(client, Settings("https://example.invalid/v1/", "test", "test", 3, 0),
                                 RentalTools(db, self.retriever)).run("Can I bring my dog?")
            self.assertEqual(result["trace"][0]["result"]["status"], "not_found")
            self.assertFalse(result["trace"][1]["result"]["message_sent"])
            self.assertIn("no matching passage", format_sources(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
