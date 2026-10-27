# Advanced manual operations: Linux / macOS

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

**You need:** Linux or macOS, Bash or zsh, Git, Python 3.10–3.12 with working
`venv`/pip, internet access for installation, and a local PDF you may use. Check
`python3 --version` first. Debian/Ubuntu may require the `python3-venv` package
matching your chosen interpreter. On macOS, use a suitable installed Python 3.
No API key, MCP connection, Node.js, `jq`, or environment activation is needed
for this path; APW's viewer assets are already built.

If `python3` points to another version, use your supported interpreter (for
example `python3.12`) for the one venv-creation command below.

> This is a source-checkout workflow. It requires the features in RKS
> [6fc5c61](https://github.com/Scientific-Tooling/research-knowledge-substrate/commit/6fc5c61),
> APW [a435c2f](https://github.com/Scientific-Tooling/agent-pdf-workbench/commit/a435c2f),
> and Structured Intelligence
> [a673678](https://github.com/Scientific-Tooling/structured-intelligence/commit/a673678),
> or compatible later revisions. Older package releases may lack these commands.

## 1. Install in a fresh folder

Run the blocks in order in **terminal A**, using Bash or zsh and keeping that
terminal open. The shell stops on errors. Use a new folder; an existing folder
deliberately stops the first run. If you change `work`, use the same path in
terminal B. Packages stay inside the new environment; RKS configuration stays
inside this review.

```bash
set -euo pipefail
work="$HOME/scientific-tooling-demo"
mkdir "$work"
for repo in research-knowledge-substrate agent-pdf-workbench structured-intelligence; do
    git clone "https://github.com/Scientific-Tooling/$repo.git" "$work/$repo"
done
python3 -m venv "$work/.venv"
py="$work/.venv/bin/python"
"$py" -m pip install -e "$work/research-knowledge-substrate" -e "$work/agent-pdf-workbench"
si="$work/structured-intelligence"
run_dir="$work/review"
mkdir "$run_dir"
export RKS_DATA_DIR="$run_dir/rks-data"
export RKS_AUTO_EXTRACT_MODE=none
"$py" -m rks init-db
json_value() {
    "$py" -c 'import json, sys
with open(sys.argv[1], encoding="utf-8-sig") as stream:
    value = json.load(stream)
for key in sys.argv[2].split("."):
    value = value[key]
print(value)' "$1" "$2"
}
```

**Expected:** both packages install and RKS initializes the new review database.
If `venv` reports missing `ensurepip`, install the matching venv support through
your Python/distribution installer, then start again in a new folder.

## 2. Ingest your PDF and save the handoff

Paste the actual full path without surrounding quotes or shell escapes. Spaces
are supported. The paper ID is read from ingestion output; it is not assumed.

```bash
printf 'Full path to your PDF: '
IFS= read -r pdf
printf 'Bounded research question: '
IFS= read -r question
"$py" -m rks ingest pdf "$pdf" > "$run_dir/paper.json"
paper_id=$(json_value "$run_dir/paper.json" id)
handoff_file="$run_dir/reading-handoff.json"
"$py" "$si/scripts/research_reading.py" "$paper_id" \
    --workspace-id unix-review --rks-data-dir "$RKS_DATA_DIR" \
    --apw-db "$run_dir/events.db" --cache-dir "$run_dir/pdfs" \
    --rks-python "$py" --apw-python "$py" > "$handoff_file"
viewer_url=$(json_value "$handoff_file" apw.viewer_url)
printf '%s\n' "$viewer_url"
```

**Expected:** a viewer URL containing a session ID. The adapter preserves and
verifies a copy of this PDF revision in `review/pdfs`.

## 3. Open the reader and highlight a passage

In a **second terminal (B)**, start the viewer and leave it running:

```bash
work="$HOME/scientific-tooling-demo"
"$work/.venv/bin/apw-viewer-server" --host 127.0.0.1 --port 8790 --db-path "$work/review/events.db" --pdf-root "$work/review/pdfs"
```

Open the URL printed by terminal A in your browser. For local use, the browser
and tools share a computer. For SSH, use the tunnel note below.

Select a short, uniquely identifiable passage. In the small selection toolbar,
optionally enter a **Quick comment**, then click **Highlight**. Confirm the quote
and page appear under **Annotations**. The highlight is saved in APW and has not
yet been imported into RKS.

## 4. Select the annotation and preview the import

Back in terminal A, list the saved annotations and enter the ID of the one you
intend to import. The Python request only reads the local annotation list.

```bash
session_id=$(json_value "$handoff_file" apw.session_id)
"$py" - "$session_id" <<'PY'
import json, sys, urllib.parse, urllib.request
query = urllib.parse.urlencode({"session_id": sys.argv[1]})
with urllib.request.urlopen("http://127.0.0.1:8790/api/annotations?" + query) as response:
    saved = json.load(response)
for item in saved["annotations"]:
    annotation = item["annotation"]
    print(f'{item["id"]}\tpage {annotation["page"]}\t{annotation["quote"]}')
PY
printf 'Annotation ID to import: '
IFS= read -r annotation_id
bundle="$run_dir/evidence.json"
plan="$run_dir/import-plan.json"
"$py" "$si/scripts/research_evidence.py" "$handoff_file" \
    --source-id unix-reader --annotation-id "$annotation_id" \
    --bundle "$bundle" --plan "$plan" --rks-python "$py" --apw-python "$py"
cat "$plan"
```

**Expected:** one proposed addition and zero conflicts. Inspect the selected
quote, paper identity, and plan. Nothing has been applied to RKS yet. Resolve any
reported conflict before continuing.

## 5. Apply the plan and generate the brief

After checking the preview, explicitly import that selected evidence:

```bash
apply_evidence() {
    "$py" -m rks note import-evidence "$bundle" \
        --workspace-id unix-review --apply --plan "$plan"
}
apply_evidence
```

**Expected:** `added: 1`. The item remains **unreviewed**. Importing a reading
observation does not turn it into a scientifically reviewed graph claim.

```bash
brief="$run_dir/reading-brief.md"
"$py" "$si/scripts/research_brief.py" "$paper_id" --question "$question" \
    --workspace-id unix-review --rks-data-dir "$RKS_DATA_DIR" \
    --source-id unix-reader --apw-db "$run_dir/events.db" \
    --rks-python "$py" --apw-python "$py" --output "$brief"
cat "$brief"
"$py" - "$brief" <<'PY'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r"\[Open the supporting passage\]\(([^)]+)\)", text)
if match is None:
    raise SystemExit("No active passage link: inspect the brief's source warning.")
print("Open this passage URL in your browser:\n" + match.group(1))
PY
```

**Expected:** the brief records the interpretation, source quote, page, review
status, and provenance. Open the printed passage URL to return to the intended
PDF page and highlight. Keep terminal B running while following these local
links. The brief is an evidence inventory, not a validated scientific answer.

## 6. Replay safely and keep your work

Repeating the exact import is safe:

```bash
apply_evidence
```

**Expected:** `added: 0`, `unchanged: 1`. For a new selection or edited annotation,
use new bundle, plan, and brief filenames, inspect the new preview, and follow
the [evidence update procedure](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/evidence-import.md).
Existing output files deliberately are not overwritten by the adapters.

Press **Ctrl+C in terminal B** to stop the viewer. With the viewer and other
RKS/APW processes stopped, back up the whole `review` folder together: RKS data,
APW database and sidecars, verified PDFs, handoff, exports, plans, and brief.
Retain the `unix-review` and `unix-reader` identities when restoring this workspace.
Recreate the Python environment if moving to a different operating system.

## If something stops

- **Unknown command or missing script:** check the required source revisions above.
- **Port 8790 is occupied:** stop the old viewer if you own it, then start terminal B
  again. The handoff, brief, and annotation-list commands here all use port 8790.
- **SSH or remote host:** keep RKS, APW, the adapters and their files together on
  the remote host. On your browser computer, run
  `ssh -N -L 8790:127.0.0.1:8790 user@host` with your actual login/hostname and
  leave that connection open. Then open the printed loopback URL locally.
- **Missing or ambiguous passage:** preserve the original PDF and quote; inspect
  the warning. Select a distinctive passage in the correct source and prepare
  a new export/preview. Do not force an anchor onto another PDF revision.
- **Existing file or stale plan:** preserve the old artifact, use a new filename,
  and regenerate the preview against current state.

For details, see [source reading](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/source-reading.md),
[selected evidence import](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/evidence-import.md),
and [passage-linked briefs](https://github.com/Scientific-Tooling/structured-intelligence/blob/main/workflows/research/source-linked-brief.md).
