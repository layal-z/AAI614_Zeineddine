# Recruitment workspace

A local browser interface for the four-agent GPT recruitment workflow.
The backend model, prompts, schemas, MCP retrieval and approval gates were
extracted from **Multi-Agent Recruitment System-GPT-v10.ipynb**. The notebook
is not required to launch the app. No API key is included. A deidentified demonstration case with both candidates’ completed reviews is included.

## Start on Windows

1. Extract this ZIP into:
   `C:\Users\layal\OneDrive\Documents\Infinite\LAU\Agentic AI`
2. Open the extracted `recruitment_app` folder.
3. Double-click **Start_Recruitment.bat**.
4. The first launch creates a separate Python environment and installs packages.
   Python 3.10 or newer must already be installed; your Python 3.13 is suitable.
5. Leave the launcher window open. The app opens in a browser on your computer.
   If the browser does not open, use the Local URL printed in that window.

No notebook cells or Python editing are needed to use the interface.
Installation requires internet access. Model requests require OpenAI API credits.

## Inspect the saved demonstration — no API key needed

Click **Open saved demonstration** in the sidebar. The app opens the saved
Evaluation page. Choose **Candidate_001** or **Candidate_002** to inspect their
CV evidence, interview plans, transcripts, model drafts and approved reviews.
Use **Tracker & checks** for quality and safeguard checks. Candidate_002 has
a saved tracker update; Candidate_001’s final review is approved but its tracker
update has not been confirmed. Viewing records and running these checks makes
no API requests. Generate buttons require your own API key and API credits.
The demonstration uses candidate IDs and generic employer/university labels.
It is copied to the app’s data folder when opened; the bundled original is preserved.

## Resume the completed notebook case

1. Choose **Create or import a case**, then **Import saved case**.
2. Upload:
   `C:\Users\layal\OneDrive\Documents\Infinite\LAU\Agentic AI\recruitment_case_gpt.json`
3. Click **Import case copy**.
4. Select the candidate in the sidebar. Saved drafts, reviews and approvals are
   restored. A gate will block any approval whose source records have changed.
5. For a completed case, select **Evaluation** directly. There is no need to
   approve the role again or generate a new assessment just to view saved work.

Import creates an independent file under `recruitment_app\data\cases`.
It never modifies the uploaded original case or the notebook. Imported cases
must come from this recruitment workflow and should contain deidentified data.

Reconfirming unchanged approved role materials preserves the original approval
and downstream records. Real edits still require a new approval and invalidate
outdated screening. If an older imported copy says the scorecard changed, the
app explains whether content versions differ or only the approval event changed.
Import the latest valid notebook case as a fresh copy to resume its records;
do not change approval fingerprints to bypass a gate.

## Use the interface

Enter your reviewer name in the sidebar. Under **API settings**, paste an
unexposed OpenAI API key into the password field. It is held in the browser
session on this local server, never saved into the case. An `OPENAI_API_KEY`
environment variable is also supported. A browser refresh may require entering
the key again. Reviewing imported records does not require an API key.

- **Role:** paste a hiring brief when creating a new case. Edit the JD, outreach,
  search terms, criteria and supporting requirements. Confirm and approve.
- **Screening:** select or add a candidate, upload TXT/PDF/DOCX, check the extracted
  CV text, then generate and review screening. Approve the reviewed assessment.
- **Interview:** generate a plan and edit its reasons, questions and answer
  signals. Approve the plan, upload/paste the transcript, choose actual or
  simulated, check the text and save reviewed evidence.
- **Evaluation:** generate an independent CV/interview assessment. Edit statuses,
  citations, explanations, open questions and summary. Approve the final report.
- **Tracker & checks:** confirm the tracker action separately. Inspect coverage
  and exact-quotation checks, run the eight approval safeguard checks, and
  download the approved report.

All changes take effect on the explicit save/approval buttons. Unsaved form
edits are not approved records. Candidate-specific forms use separate keys so
switching candidates does not carry another candidate's text into the review.

Use **Download case backup** to keep a copy of current records. Keep the
original notebook as the course development/test artifact.

## Files

- `app.py`: Streamlit forms and browser navigation.
- `engine.py`: persistence and browser-independent review adapters.
- `workflow.py`: the tested model, validation and approval functions from v10.
- `recruitment_mcp_server.py`: the scoped read-only MCP server.
- `requirements.txt`: dependency versions used for testing.
- `Start_Recruitment.bat`: Windows setup and launcher.
- `test_app.py`, `test_ui.py`: offline workflow and interface tests.

## Validation

Tests use fixed synthetic API responses and actual local MCP subprocess calls.
They cover all four stages, saved case restoration, tool-message conversion,
report export, tracker duplicate prevention, eight approval safeguards,
invalid citations, missing human confirmation, all five pages and candidate
switching. They do not establish model quality or make paid API requests.
Eight offline tests pass, including repeated approval of unchanged role content
and rejection of existing screening after a real role change.

To run the tests from the extracted folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v
```

## Scope and limitations

This is a local, single-recruiter application. Use one browser session per case;
concurrent editing, hosted multi-user access, authentication and deployment are
not implemented. It binds to the local computer, not the public network.

The model sees the supplied deidentified brief and candidate evidence through
OpenAI requests. MCP scopes retrieval to the selected candidate and permitted
read-only tool. Python attaches exact source quotations and checks approval
versions; it cannot prove that a quotation supports an interpretation. Human
review remains necessary. PDF scans need OCR or pasted text; OCR is not included.

Changing approved upstream records can invalidate later results. The app blocks
silently replacing an approved screening with a different CV; use a new
candidate ID for a new CV version. An approved final evaluation is not silently
regenerated against changed records.

No candidate-contact messages are sent and no final hiring decision is automated.

The bundled final case was checked for valid approval chains for both candidates. Both candidates’ saved records were opened on all five pages without API requests.
