# Conversation evidence

Captured from the real running Gradio app with Furen-large on 26 October 2026.
The source code and model configuration were unchanged from the supplied project.

- `screenshot-main.jpg`: opening hours from `get_rental_info`.
- `screenshot-1-answer.jpg`: original Corolla/three days/GPS question and answer.
- `screenshot-1.jpg`: follow-up adds 600 km; visible `calculate_rental` arguments
  retain Corolla, three days and GPS. The result is EUR 192 plus a separate EUR 300 deposit.
- `screenshot-2.jpg`: missing pet policy followed by `transfer_to_staff`; no message sent.
- `screenshot-3.jpg`: unrelated football question declined without tools.
- `routing-test-results.png`: a readable rendering of the real baseline JSON in
  `../evidence/`, not a new run or an original console screenshot.

Long single-line fields can extend beyond the visible Gradio code panel. The
original routing-test JSON includes the complete tool returns for the same four
scenario types. None of these screenshots has been generated or altered by AI.
