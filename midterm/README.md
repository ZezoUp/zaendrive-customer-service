# ZaenDrive Midterm Rental Assistant

ZaenDrive is a fictional car-rental customer-service app. It extends the Unit G
homework with retrieval-augmented generation over longer rental handbooks.
Customers can compare vehicles, request exact rental estimates and ask about
rental conditions. All company information is fictional coursework data.

The default model is Furen-large at the NKUST OpenAI-compatible endpoint. The
interface is built with Gradio. Enter your own API key locally or through Colab.

## Features and limits

- Reads a 16-vehicle demo fleet and 14 short information topics from SQLite.
- Calculates prices using Python Decimal arithmetic, including requested extras,
  weekly discounts and declared excess mileage. The deposit remains separate.
- Searches three fictional handbooks, divided into 15 sections. Selected passages
  are sent to the model, which should cite the returned source IDs.
- Shows retrieved passages beside the conversation and tool details in an accordion.
- Provides a fictional staff contact for missing information and human requests.

The app cannot create, look up or modify bookings, take payments, issue refunds,
dispatch assistance or send messages. Availability is a fixed snapshot, not a
date-specific calendar. Startup imports rebuild SQLite from the CSV files;
customer records and chat messages are not saved in the database.

## How RAG works

1. rag.py reads documents/*.md and splits at section headings. Longer sections use
   220-word windows with 35-word overlap.
2. A local BM25 index ranks passages against a policy question. Stop words are
   removed; an explicit English/German synonym map helps matching.
3. The model calls search_rental_policies with a standalone query. Up to three
   passages are returned by default, with source IDs, text and retrieval scores.
4. These passages become tool context. The model generates a grounded answer and
   should cite the source. The interface shows the retrieved evidence.

This is lexical RAG, not embedding/vector search. No LangChain, vector database,
embedding API or extra model download is used. Language and synonym coverage are
limited; the system prompt asks the model to search in English when possible.
A retrieved match does not prove that every requested detail is available.
Missing rules and unspecified fees require an honest answer and staff referral.
The full handbooks are never pasted into the system prompt.

| Tool | Purpose |
| --- | --- |
| get_rental_info | Short business facts and numeric rate settings from SQLite |
| search_vehicles | Fleet features, daily prices and snapshot availability |
| calculate_rental | Exact rental price calculations |
| search_rental_policies | Selected handbook passages and source IDs |
| transfer_to_staff | Fictional contact referral; no message or live transfer |

## Start in Colab

1. Upload C115451101_Zaen_Midterm_Colab.ipynb to Google Colab.
2. Use a CPU runtime. Run the first cell and upload C115451101_Zaen_Midterm_Project.zip.
3. Run package installation. If Colab requests a restart, restart and rerun that cell.
4. Configure your existing course key through a Colab secret called NKUST_API_KEY,
   or the hidden input prompt. It stays in the runtime environment.
5. Run the offline checks and app cell. Open the temporary Gradio link.
6. Use START_HERE_DE.md for manual cases. Save genuine screenshots.
7. Optionally run the live routing checks and download JSON/CSV evidence.

## Start locally

Python 3.10 or newer is required; preparation used Python 3.12.
In the project folder on Windows PowerShell:

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
~~~

Edit .env locally and enter your own API key. Then:

~~~powershell
python -m unittest -v test_offline test_rag test_scope_guard
python app.py
~~~

On Linux/macOS use source .venv/bin/activate and cp .env.example .env.
For a temporary share link run python app.py --share; it requires a running session.

## Checks and screenshots

The offline command runs 33 tests without an API key, including checks for the observed instruction-override and role-play failures. Scripted model responses
check loop mechanics and real retrieval/calculation logic, not LLM intelligence.
To run 19 real routing questions:

~~~powershell
python tool_choice_test.py --label midterm-baseline
~~~

This checks app tool routing and exact answers for the four fixed-refusal cases. Some attacks are refused locally with zero model calls; this is not a raw model-accuracy score. Inspect complete answers, arguments, citations and
refusals manually. Any rule-breaking text counts as a failure even if routing
reports PASS. Fix failures and rerun in a fresh conversation. The assignment
does not require a test table or a particular routing score. Previous Unit G
results do not establish performance of this modified version.

Use the instructor's original template in report/. Include 2–4 real conversations,
one showing an honest missing-data or out-of-scope answer. This app does not write
business records: skip the saved-data proof and do not claim booking support.
The three documented conversations are shown below. Full originals are in images/ and evidence/.
Export the completed report as C115451101_Zaen_Midterm.pdf. A video is optional.

## GitHub submission

Publish source, both CSVs, documents/, .env.example, requirements.txt, README.md,
.gitignore and real screenshots in a public repository. Include the notebook and
tests if useful. Put the public URL on page one of the report and check it in an
incognito window. Never upload .env, keys, runtime databases or notebook outputs
containing credentials. When uploading via the GitHub website, select files
carefully; .gitignore applies to git operations.

This midterm version is published at
https://github.com/ZezoUp/zaendrive-customer-service/tree/main/midterm.
The repository root retains the earlier Unit G homework. See VALIDATION.md for
the checks and the limits of the evidence.

## Technical references

- Gradio messages/migration: https://www.gradio.app/guides/gradio-6-migration-guide
- BM25 retriever reference: https://reference.langchain.com/python/langchain-community/retrievers/bm25/BM25Retriever

These are implementation references. The rental handbooks are invented demo
material, not terms copied from a real company. API keys remain on the Python server.

## Scope checks added after live testing

scope_guard.py checks common instruction overrides, prompt-disclosure requests
and programming tasks before the API call, and code-like outputs before display.
Rejected inputs and blocked outputs are omitted from later model history; the
visible chat still shows the turn. The UI records a scope_guard event, status
guard_refusal, and the actual model-call count (zero for a preflight refusal).
These are explicit rules, not a general semantic classifier or a guarantee against
every possible prompt attack. Genuine rental questions still use the tool-calling
model. The test runner now checks the complete fixed refusal, so an unrelated
programming answer with no tools no longer receives a PASS.

For an existing Colab session: rerun the ZIP upload cell with the updated archive,
then run a new code cell containing:

~~~python
%run /content/zaendrive_midterm/ZaenDrive/restart_colab.py
~~~

The current API environment is reused. No package changes are required for this update.

## Real conversation evidence

Captured by the student on 8 November 2026 with the running app:

### Exact rental quote

Three days of Corolla Hybrid rental at EUR 59/day plus GPS at EUR 5/day gives
EUR 192. The EUR 300 refundable deposit is separate. The answer does not invent
a deposit-release procedure.

![Live quote and tool trace](images/quote.png)

### Retrieved early-return rule

The app says an early return does not automatically produce a refund. It cites
01_rental_handbook.md#early-return-and-refunds. These two panels are rendered
from the same original [saved app PDF](evidence/early-return-live-app.pdf).

![Early-return answer from the live app PDF](images/rag-answer.png)
![Retrieved passage and actual retrieval trace](images/rag-source.png)

### Missing information

There is no pet policy in the data. The app says that it cannot find that
information and supplies the fictional staff contact without inventing a rule.

![Missing pet policy and honest answer](images/missing-policy.png)

### Scope-guard repeat

The student repeated the three previously reported attack cases after the guard
was added. All three produced fixed refusals, zero model calls and
status guard_refusal. This is evidence about those application-level cases,
not a general model-robustness score.

The completed report is in report/C115451101_Zaen_Midterm.pdf. It records the
student’s approximate working time of two hours. Upload only this PDF to the
course site; the code and evidence are available through the GitHub link in it.
The Word copy is included for editing, and a demo video is optional.
