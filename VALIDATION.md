# Verification of the prepared project

- All 14 tests in `test_offline.py` passed during preparation.
- All Python modules parse and every notebook code cell compiles.
- The notebook contains no saved outputs, execution results or API key.
- The Gradio interface was instantiated and served locally with the pinned packages.
- A Gradio client sent a question through the UI event to the real OpenAI-compatible
  SDK, then to a local scripted HTTP endpoint. The returned tool call executed the
  real SQLite/Decimal calculator and displayed the expected EUR 192.00 quote and trace.
- A second UI request retained previous tool messages in session state. The new
  conversation action cleared the chat and trace.

The local endpoint used scripted responses, not a language model. These checks do
**not** establish model tool-choice accuracy or correctness of natural-language replies.

## Live model evidence

- The user ran the supplied code and model configuration without changes.
- The completed Furen-large baseline from 26 October 2026 at 13:42:39 UTC passed
  14 of 14 routing questions (100%). Original JSON/CSV exports are in `evidence/`.
- Every source hash recorded by the live test matches the corresponding file here.
- Real Gradio screenshots cover an information lookup, a rental calculation,
  missing information with a demo staff referral, and an off-topic refusal.
- A follow-up supplies 600 km after a three-day Corolla rental with GPS. The agent
  retains vehicle/duration/extras and calculates EUR 192 plus a separate EUR 300
  refundable deposit, with no excess-mileage charge.
- No routing correction or after-fix run was needed. The score checks called tool
  sets, successful completion and absence of invalid calls. It does not establish
  perfect answer quality or grade every argument value.
- `images/routing-test-results.png` renders the original saved results. It is not
  presented as a new run or an original Colab console screenshot.

The service is a coursework prototype with fictional inventory and contact data.
It cannot book a car, send a message, make a payment or check live availability.
