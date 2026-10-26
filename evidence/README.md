# Real test evidence

The baseline JSON and CSV were exported by `tool_choice_test.py` during the real
Furen-large run on 26 October 2026 at 13:42:39 UTC. All 14 questions completed;
14 passed, giving **100% tool-routing accuracy**. The JSON includes the actual
answers, arguments, tool returns and source hashes. All five recorded source
hashes match this project. The score does not grade every answer or argument.

`routing-test-output.html` is a readable presentation of that saved JSON, not a
new run. `../images/routing-test-results.png` is a rendering of the actual saved
results, not an original Colab console screenshot.
No routing correction or after-fix run was needed.
