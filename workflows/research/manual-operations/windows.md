# Advanced manual operations: Windows / PowerShell

Use the [quick start](../quickstart.md) for everyday PDF-to-brief work. This
reference exposes the individual RKS, APW and adapter commands for development,
debugging or connecting an existing RKS workspace. Choose this path when you
need to manage the databases, handoff files and reader process yourself.

Back to [advanced manual operations](README.md).

Use **Research Knowledge Substrate (RKS)** to keep papers and imported evidence,
and **Agent PDF Workbench (APW)** to read and annotate the original PDF.
Structured Intelligence connects their command-line tools. This walkthrough
takes one local PDF through reading, selected evidence import, and a brief with
a link back to the highlighted passage.

**You need:** Windows, PowerShell 5.1 or 7, Git, Python 3.12 or newer on PATH, an
internet connection for installation, and a local PDF you may use. Python 3.14
is recommended. No API key, MCP connection, Node.js, or shell
activation is needed for this path; APW's viewer assets are already built.

> This is a source-checkout workflow. It requires the features in RKS
> [6fc5c61](https://github.com/Scientific-Tooling/research-knowledge-substrate/commit/6fc5c61),
> APW [a435c2f](https://github.com/Scientific-Tooling/agent-pdf-workbench/commit/a435c2f),
> and Structured Intelligence
> [a673678](https://github.com/Scientific-Tooling/structured-intelligence/commit/a673678),
> or compatible later revisions. Older package releases may lack these commands.

## 1. Install in a fresh folder

Run the blocks in order in **terminal A**, keeping that terminal open. The helper
stops on a failed native command, including in Windows PowerShell 5.1. It changes
no machine-wide Python installation or global RKS configuration.
If you change `$work`, use the same path in terminal B.

```powershell
$ErrorActionPreference = "Stop"
function Invoke-Checked {
    param([string]$Exe, [string[]]$ToolArgs)
    & $Exe @ToolArgs
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Exe (exit $LASTEXITCODE)" }
}
$work = Join-Path $env:USERPROFILE "scientific-tooling-demo"
if (Test-Path -LiteralPath $work) { throw "Choose a new folder for this first run: $work" }
New-Item -ItemType Directory -Path $work | Out-Null
foreach ($repo in "research-knowledge-substrate", "agent-pdf-workbench", "structured-intelligence") {
    Invoke-Checked git @("clone", "https://github.com/Scientific-Tooling/$repo.git", (Join-Path $work $repo))
}
Invoke-Checked python @("-m", "venv", "$work\.venv")
$py = "$work\.venv\Scripts\python.exe"
Invoke-Checked $py @("-m", "pip", "install", "-e", "$work\research-knowledge-substrate", "-e", "$work\agent-pdf-workbench")
$si = "$work\structured-intelligence"
$run = "$work\review"
New-Item -ItemType Directory -Path $run | Out-Null
$env:RKS_DATA_DIR = "$run\rks-data"
$env:RKS_AUTO_EXTRACT_MODE = "none"
Invoke-Checked $py @("-m", "rks", "init-db")
```

**Expected:** both packages install and RKS initializes the new review database.
If `python` is unavailable, install Python and reopen PowerShell before continuing.

## 2. Ingest your PDF and save the handoff

Paste a full file path without surrounding quotes when prompted. Use the paper
ID returned by ingestion; do not assume it is `p_000001`. The two workspace names
used below must stay stable for this review.

```powershell
$pdf = (Resolve-Path -LiteralPath (Read-Host "Full path to your PDF")).Path
$question = Read-Host "The bounded question you are reading this paper to investigate"
$paper = (Invoke-Checked $py @("-m", "rks", "ingest", "pdf", $pdf) | Out-String) | ConvertFrom-Json
$paperId = $paper.id
$handoffFile = "$run\reading-handoff.json"
$handoffText = Invoke-Checked $py @(
    "$si\scripts\research_reading.py", $paperId,
    "--workspace-id", "windows-review", "--rks-data-dir", $env:RKS_DATA_DIR,
    "--apw-db", "$run\events.db", "--cache-dir", "$run\pdfs",
    "--rks-python", $py, "--apw-python", $py
) | Out-String
$handoffText | Set-Content -LiteralPath $handoffFile -Encoding UTF8
$handoff = $handoffText | ConvertFrom-Json
$handoff.apw.viewer_url
```

**Expected:** a viewer URL containing a session ID. The adapter preserves and
verifies a copy of this PDF revision in `review\pdfs`.

## 3. Open the reader and highlight a passage

In a **second PowerShell terminal (B)**, start the viewer and leave it running:

```powershell
$work = Join-Path $env:USERPROFILE "scientific-tooling-demo"
& "$work\.venv\Scripts\apw-viewer-server.exe" --host 127.0.0.1 --port 8790 --db-path "$work\review\events.db" --pdf-root "$work\review\pdfs"
```

Back in **terminal A**, open the session:

```powershell
Start-Process $handoff.apw.viewer_url
```

Select a short, uniquely identifiable passage in the PDF. In the small selection
toolbar, optionally enter a **Quick comment**, then click **Highlight**. Confirm
the quote and page appear under **Annotations**. The highlight is saved in APW;
it has not yet been imported into RKS.

## 4. Select the annotation and preview the import

In terminal A, list the saved annotations and copy the ID of the one you intend
to import. This local viewer request only reads the annotation list.

```powershell
$viewer = "http://127.0.0.1:8790"
$sid = [uri]::EscapeDataString($handoff.apw.session_id)
$saved = Invoke-RestMethod "$viewer/api/annotations?session_id=$sid"
$saved.annotations | ForEach-Object {
    [pscustomobject]@{ Id = $_.id; Page = $_.annotation.page; Quote = $_.annotation.quote }
} | Format-Table -Wrap
$annotationId = Read-Host "Annotation ID to import"
$bundle = "$run\evidence.json"
$plan = "$run\import-plan.json"
Invoke-Checked $py @(
    "$si\scripts\research_evidence.py", $handoffFile,
    "--source-id", "windows-reader", "--annotation-id", $annotationId,
    "--bundle", $bundle, "--plan", $plan, "--rks-python", $py, "--apw-python", $py
)
Get-Content -LiteralPath $plan
```

**Expected:** one proposed addition and zero conflicts. Inspect the selected
quote, paper identity, and plan. Nothing has been applied to RKS yet. If the
preview reports a conflict, resolve the reported cause before applying it.

## 5. Apply the plan and generate the brief

After checking the preview, explicitly import that selected evidence:

```powershell
$importArgs = @(
    "-m", "rks", "note", "import-evidence", $bundle,
    "--workspace-id", "windows-review", "--apply", "--plan", $plan
)
Invoke-Checked $py $importArgs
```

**Expected:** `added: 1`. The item remains **unreviewed**. Importing a reading
observation does not turn it into a scientifically reviewed graph claim.

```powershell
$brief = "$run\reading-brief.md"
Invoke-Checked $py @(
    "$si\scripts\research_brief.py", $paperId, "--question", $question,
    "--workspace-id", "windows-review", "--rks-data-dir", $env:RKS_DATA_DIR,
    "--source-id", "windows-reader", "--apw-db", "$run\events.db",
    "--rks-python", $py, "--apw-python", $py, "--output", $brief
)
Get-Content -LiteralPath $brief
$passage = [regex]::Match((Get-Content -LiteralPath $brief -Raw), '\[Open the supporting passage\]\(([^)]+)\)')
if (-not $passage.Success) { throw "No active passage link: inspect the brief's source warning." }
Start-Process $passage.Groups[1].Value
```

**Expected:** the brief records the interpretation, source quote, page, review
status, and provenance. Its link opens the intended PDF page and highlighted
passage. Keep terminal B running while following these local links. The brief is
an evidence inventory; it does not generate or validate a scientific answer.

## 6. Replay safely and keep your work

Repeating the exact import is safe:

```powershell
Invoke-Checked $py $importArgs
```

**Expected:** `added: 0`, `unchanged: 1`. For a new selection or edited annotation,
use new bundle, plan, and brief filenames, inspect the new preview, and follow
the [evidence update procedure](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/evidence-import.md).
Existing output files deliberately are not overwritten by the adapters.

Press **Ctrl+C in terminal B** to stop the viewer. With the viewer and other RKS/APW
processes stopped, back up the whole `review` folder together: RKS data, APW
database and sidecars, verified PDFs, handoff, exports, plans, and brief. Retain
the `windows-review` and `windows-reader` identities when restoring this workspace.

## If something stops

- **Unknown command or missing script:** check the required source revisions above.
  This walkthrough does not assume the latest PyPI package contains these features.
- **Port 8790 is occupied:** stop the old viewer if you own it, then start terminal B
  again. The handoff, brief, and annotation-list commands here all use port 8790.
- **Missing or ambiguous passage:** keep the original PDF and quote; inspect the
  warning. Select a distinctive passage in the correct source and prepare a new
  export/preview. Do not force an old anchor onto another PDF revision.
- **Existing file or stale plan:** preserve the old artifact, use a new filename,
  and regenerate the preview against current state.

For details, see [source reading](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/source-reading.md),
[selected evidence import](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/evidence-import.md),
and [passage-linked briefs](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/source-linked-brief.md).
