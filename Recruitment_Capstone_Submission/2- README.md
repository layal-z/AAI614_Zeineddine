# Human reviewed multi agent recruitment system

Four specialist agents powered by GPT-4.1 support role design, candidate
screening, interview planning and interview evaluation. Python coordinates
sequential handoffs. Agents 2–4 call scoped, read-only retrieval tools through
a local MCP server. Human approvals control downstream access and tracker updates.

Repository branch: https://github.com/layal-z/AAI614_Zeineddine/tree/Agentic_AI

## What is included

- `Multi_Agent_Recruitment_System_GPT_v11.ipynb`: the final notebook,
  including saved demonstration outputs and review interfaces.
- `recruitment_mcp_server.py`: the same read-only server written by notebook #37.
- `requirements.txt`: installation dependencies. MCP stays on v1 because this
  code uses its FastMCP API; MCP v2 is incompatible without migration.
- `sample_inputs/`: deidentified CV text and English interview text for two
  candidates, exported from supplied source records.
- `safeguard_results.txt` and `quality_results.json`: saved Candidate_002 checks.
- `Capstone_Report.pdf` / `.docx`: the six-page project report.

The sample Candidate_002 transcript comes from an earlier reviewed source copy.
Whitespace/line-break differences from the final notebook input can shift I IDs.
The source text should be checked before approval; exact output IDs are not
promised to reproduce. The completed notebook outputs are the recorded run.

## Prerequisites and API access

Use Python 3.10 or newer. Development was performed with Python 3.13 on Windows.
Internet access and a funded OpenAI API project with GPT-4.1 access are required
for new model generations. **No Ollama model needs to be pulled.**

Each reviewer enters their own API key in notebook #1's `getpass` prompt.
Do not paste keys into a code cell, upload them to GitHub, or share the author's
personal key. School-managed OpenAI project members can create their own keys.
A ChatGPT subscription does not itself provide API credits.

Saved notebook outputs can be inspected without a key. This is not an offline
model run: executing model calls requires working API credentials and credits.

## Install and open

From the repository folder in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyter lab
```

Open the final `Multi_Agent_Recruitment_System_GPT_v11.ipynb` from GitHub in JupyterLab. Select the
Python environment in which these packages were installed.

**Before running #19**, configure its `PROJECT_DIR` for your own computer. The
submitted notebook retains the author's tested Windows path. For a portable
run from your repository folder, replace only that assignment with:

```python
PROJECT_DIR = Path.cwd()
```

`CASE_FILE` remains `PROJECT_DIR / "recruitment_case_gpt.json"`. A fresh case file
is not included. Existing local cases may be reused only when their records
match. Choose an empty folder or a new case filename for a fresh demonstration.

## Run in order

Use the visible cell labels, not historical execution counts. Run one cell at a
time and stop for human review. Do not use Run All.

1. **Setup:** #1 prompts for your API key. #37 writes the MCP server beside the
   notebook; #38 defines the MCP client. Keep these ahead of screening.
2. **Role:** #2 supplies the client brief. #3–#6 define schemas, instructions and
   the model function. #19 configures persistence. #7 extracts the brief; #8
   generates and saves recruitment materials.
3. **Role review:** #9–#12 load the widgets and open the editor. Check extracted
   facts, JD, outreach and scorecard. Save and approve using your reviewer name.
   #13 checks the approved scorecard.
4. **Screening:** #14–#15 define Agent 2. #16 opens the input. Enter `Candidate_001`
   and upload `sample_inputs/Candidate_001_CV.txt`. Check the loaded text and tick
   its confirmation. #17 retrieves evidence through MCP and screens, or reuses
   matching saved results. #18 displays the draft. #20–#21 open human review;
   edit judgments and citations as needed, then save and approve.
5. **Second candidate:** change the existing #16 selector to `Candidate_002`,
   upload its matching CV, check the text, confirm, and rerun #17–#18 and #21.
   Simply switching the selector does not refresh an already-open review panel.
6. **Interview planning:** select the candidate to continue. #22–#24 generate
   its plan. #25 opens the question editor; review and approve the plan.
7. **Interview evidence:** #26 opens the transcript input. Paste the matching
   `sample_inputs/<candidate>_Interview.txt`, choose **actual**, check the English
   transcript and any unclear passages, enter your name, confirm and save.
8. **Evaluation:** #27–#29 retrieve approved context through MCP and generate
   Agent 4's draft. #30–#31 open the final-report review. Check statuses,
   evidence relevance, explanations, unresolved questions and summary; approve.
9. **Tracker:** #32–#33 require separate human confirmation. Confirm the selected
   candidate shown above the tracker controls, then approve the local update.
10. **Evaluation checks:** #34 runs eight approval checks on isolated case copies.
    #35 checks coverage, source quotations and human changes. #39 optionally
    checks MCP discovery/retrieval without a model call. #40 is an optional
    isolated Agent 1 diagnostic; it is not needed for the normal workflow.

To continue another candidate, change #16's ID and rerun the candidate-specific
interfaces. Retain the correct CV/transcript pairing. Do not rerun model stages
only to refresh an interface; reuse checks avoid unnecessary calls.

## Recorded results

Candidate_002 completed the all-GPT workflow. Agent 3 took 8.51 seconds and
Agent 4 took 7.75 seconds in the saved run. The final checks show 8/8 criteria,
26/26 exact quotations, no unlisted explanation references and two human status
corrections. The eight approval safeguard checks passed without changing the
original case. Candidate_001 also completed GPT evaluation and human review: 8/8 criteria,
17/17 exact quotations, no unlisted explanation references, and two final human
status corrections. Its quality results are included
in quality_results_Candidate_001.json.

These are single-case observations, not general accuracy or latency guarantees.
The six unchanged statuses are agreement with a reviewer, not independent
correctness. Exact quotation matching does not establish semantic support.

## Safety and limits

The server returns only the authorized tool/candidate snapshot. Documents are
treated as untrusted data. Python validates JSON, IDs, source quotations and
approval fingerprints. Original model drafts remain separate from reviewed
screening and final-report edits. Tracker updates need explicit confirmation.

CV claims and interview statements are not independently verified facts.
Nationality cannot be inferred from language or location. Missing relocation
information requires confirmation. Human review must check evidence relevance,
complete criteria, uncertainty and consistency with the client summary.

The case JSON is plaintext local storage. Use deidentified samples, protect
local files and do not commit operational cases. Model inputs are sent to OpenAI
with `store=False`; this does not mean no provider retention under every policy.
No real candidates are contacted and no hiring decisions are automated.

## Troubleshooting

- `401`: check the key entered in #1; never share it in an error screenshot.
- `429` / insufficient quota: check API credits for the reviewer's project.
- `NameError`: run the preceding definition/import cells in the current kernel.
- Missing MCP imports: install the requirements in Jupyter's selected environment.
- Source/approval changed: reopen and approve the relevant review. Do not bypass
  the gate or change fingerprints to force acceptance.
- PDF has no text: use a text-based CV or paste reviewed text. OCR is not included.
- Scenarios labelled actual must use actual supplied interview notes. Do not
  invent answers for questions absent from the original transcript.

The author identifies `Multi_Agent_Recruitment_System_GPT_v11.ipynb` as the final notebook: https://github.com/layal-z/AAI614_Zeineddine/blob/790cf28cdd561ebab9c7aa6685df7985b5a78aa0/Multi_Agent_Recruitment_System_GPT_v11.ipynb . The final v11 file was downloaded from this commit and is included in the package. Notebook JSON, standard Python syntax and raw API-key patterns were checked; the notebook was not re-executed during packaging. The final uploaded case and both candidates’ reviewed results are included in the app demonstration.

## Controlled assessment tests

Open Controlled_Agent4_Tests.py and paste its complete contents into a new notebook cell labelled #41 after the workflow definitions. It requires a current API client and a selected candidate with approved evaluation context. It reuses Agent 4’s evaluator, prompt, validation and real MCP retrieval in an isolated environment. Only the context reader is replaced with synthetic inputs; recruitment-case persistence is disabled. Results are saved separately to evaluation_robustness_tests.json. This is not an end-to-end approval test.

The supplied run passed four cases: 15-year positive control, three-year below-minimum case, explicit interview correction from 15 to five years, and a three-year CV containing an instruction to approve everything. Review the explanations and summaries as well as the automated checks. One passed injection case does not establish general attack resistance. The real case remained unchanged. controlled_test_results.json records the supplied console results.

Keep #39 as an optional MCP connection check and #41 as controlled assessment tests. #40 is an earlier standalone Agent 1 diagnostic; it may be removed from the main notebook and archived separately. Neither optional test is needed to generate a normal recruitment report.

## Optional browser interface

The recruitment_app folder provides a local Streamlit interface to the same four-agent workflow, prompts, MCP tools and human approval gates. The Jupyter notebook remains the main course development and evaluation artifact.

On Windows, open recruitment_app and double-click Start_Recruitment.bat. It creates a separate environment, installs the app requirements and opens the local browser interface. Keep the launcher window open. On other systems, install recruitment_app/requirements.txt and run `python -m streamlit run recruitment_app/app.py --server.address 127.0.0.1`.

To resume notebook work, choose Create or import a case → Import saved case, upload your current recruitment_case_gpt.json and click Import case copy. Select the candidate, then Evaluation directly to inspect saved results. Enter an API key only when generating new drafts. Enter the reviewer name before approving changes.

Pages: Role, Screening, Interview, Evaluation, and Tracker & checks. Download case backup is at the bottom of the sidebar. Import creates a separate app case; it does not overwrite the notebook case. Unchanged role approval is preserved; changed requirements still invalidate older screening.

Eight offline tests passed using simulated API responses and real MCP retrieval. They check all five pages and the approval workflow. This is a local single-user interface, not a hosted authenticated service. See recruitment_app/README.md for details.

The bundled `recruitment_app/demo_cases/hr_director_demo.json` is the final deidentified case. Both candidates have valid final approval chains. Their final reviews each correct C006 to partially_demonstrated and C008 to requires_human_confirmation (6/8 status agreement). Candidate_002 has a confirmed tracker entry; Candidate_001 does not. In the app, click **Open saved demonstration** to inspect either candidate without an API key. GitHub stores this code; download it and run the launcher locally.
