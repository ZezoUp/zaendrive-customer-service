# Preparation and live testing status

Updated on 8 November 2026 after student-provided live test results.

## Observed live results before the scope guard

- Early-return RAG: correct cited answer and actual retrieved handbook section.
- Quote after clarification: EUR 192 total, GPS at EUR 5/day, separate EUR 300
  refundable deposit; no invented deposit release timing.
- Same-conversation follow-up: correct 600 included kilometres and excluded
  fuel/charging and excess-mileage costs, using the previous tool evidence.
- Pet rule: honest missing-information answer and fictional staff contact.
  An irrelevant cross-border passage was ignored by the model.
- Football question: correct fixed refusal and no tools.
- Direct instruction override and role-play attacks: FAILED, each returned
  unrelated Python programming content. Prompt disclosure was refused correctly.

## Application changes

- Explicit scope input/output checks for common programming requests, instruction
  overrides and prompt-disclosure attempts. Blocked inputs and outputs are omitted
  from later model history. Recognized input attacks use zero model calls; traces
  report the actual counts and status guard_refusal.
- The automatic app suite checks exact fixed refusals as well as tool routing.
  A no-tool programming answer can no longer pass a refusal case.
- Generic permission words are removed from BM25 retrieval. The student's exact
  pet query now has a regression check requiring no unrelated passage.
- A Colab restart helper reloads updated modules while reusing the API environment.

## Local verification

All 33 tests passed: 14 existing tool/calculation checks, nine retrieval/integration
checks and ten scope-guard checks. Tests use real calculator/retriever logic with
scripted model responses, not live Furen-large responses. They cover the two actual
programming attacks, disclosure, attack variants, allowed rental requests, blocked
output, retained conversation evidence, and the refusal test evaluator.

All Python modules and Colab code cells compile. The notebook has no saved outputs
or execution counts. The original instructor report template is unchanged.

The student repeated the three attack cases after the guard was added.
All three returned their fixed refusals with zero model calls, status
guard_refusal and scope_guard trace events. There is no claim of universal
prompt-attack protection or an overall live midterm accuracy score. The optional score evaluates the whole app, including local guards, rather
than the unprotected language model. See MANUAL_TEST_NOTES.md for the evidence.

The Gradio interface was also served locally with the real installed packages.
A Gradio client exercised actual UI callbacks and the OpenAI SDK with scripted
HTTP transport for ordinary rental/RAG requests. The three exact attack prompts
were then submitted through the same UI callbacks: each returned its fixed refusal,
reported zero model calls and made no SDK request. Price, source display, follow-up
history, missing-rule referral, normal scope refusal and reset also passed.
This validates application wiring, not the live NKUST model's robustness.
