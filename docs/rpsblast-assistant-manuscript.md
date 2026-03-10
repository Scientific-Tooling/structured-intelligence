# RPS-BLAST in the AI Era: A Natural-Language Skill for CDD Domain Annotation

## Abstract

`rpsblast` is a mature and valuable tool for conserved-domain annotation, but its practical use still assumes command-line fluency, familiarity with NCBI's CDD file layout, and knowledge of the `rpsblast -> rpsbproc` processing chain. Those assumptions create avoidable friction for biologists, research assistants, and interdisciplinary users who understand the analysis goal but do not routinely operate low-level bioinformatics tooling. This manuscript introduces `rpsblast-assistant`, a reusable skill that reframes `rpsblast` as an AI-mediated workflow. Instead of asking users to memorize download URLs, file naming conventions, archive formats, and output parsing rules, the skill lets users express intent in natural language while an AI agent translates that intent into validated setup, download, execution, and interpretation steps. The result is not a replacement for `rpsblast`, but a new interface layer around it: one that preserves the underlying NCBI workflow while making it easier to adopt, audit, and operationalize.

## 1. Introduction

The command line has always offered precision, but precision often comes at the cost of accessibility. This tradeoff is especially visible in bioinformatics, where powerful tools are frequently packaged as a set of executables, archives, index files, and loosely coupled preprocessing or postprocessing utilities. `rpsblast` is a clear example. The tool is highly capable, but running it correctly requires more than a single binary. Users must know where to obtain the CDD databases, how to unpack them, which annotation files are needed by `rpsbproc`, how to choose the right executable for protein or nucleotide queries, and which output format is compatible with downstream processing.

For experienced practitioners, this setup is normal. For new users, it is a barrier. Many do not need to become shell experts; they need to answer a biological question, inspect a domain architecture, or annotate a FASTA file. In the AI era, that distinction matters. Large language models and code agents can now function as interface translators between user intent and deterministic tooling. The opportunity is not to make `rpsblast` "automatic" in a vague sense, but to encode a correct operational playbook so an AI agent can execute it reliably on behalf of the user.

## 2. Why `rpsblast` Needs an Interface Layer

The classic local workflow around `rpsblast` contains several kinds of hidden knowledge:

- acquisition knowledge: where to download BLAST+ executables, CDD databases, and `rpsbproc` assets
- filesystem knowledge: where those files should live and what database prefix `-db` should point to
- execution knowledge: when to use `rpsblast` versus `rpstblastn`, what E-value to choose, and why `-outfmt 11` matters
- interpretation knowledge: how to understand the intermediate ASN.1 archive and the final `rpsbproc` tabular output

These are not difficult concepts individually, but they are easy to get wrong in combination. Small mistakes are common: pointing `-db` at a directory instead of a prefix, forgetting to download annotation files, producing a text BLAST report that `rpsbproc` cannot read, or treating the final `.out` file as an unstructured spreadsheet dump rather than a structured report with comments and data sections.

An AI-mediated interface can absorb this hidden knowledge and expose the tool in the language users already think in:

- "Help me download the minimal CDD database."
- "Check whether my local setup is complete."
- "Run this FASTA against CDD and explain the output."
- "What part of `sequence.out` is the real tabular data?"

This is a different mode of software use. The user specifies intent; the agent supplies parameterization, file choreography, and validation.

## 3. The `rpsblast-assistant` Skill

`rpsblast-assistant` is implemented as a local skill in this repository. It packages three layers of operational knowledge:

1. `SKILL.md`
   A concise policy and workflow document describing when the skill should be used, what inputs it expects, how it translates natural-language requests into concrete actions, and what outputs it must return.

2. Reference material
   A focused reference document captures the essential public workflow for local `rpsblast` and `rpsbproc` usage: official download sources, expected directory layout, the canonical execution pattern, and the structure of the final output.

3. Deterministic shell automation
   The bundled `scripts/run.sh` script provides subcommands for:
   - `sources`: print official acquisition URLs
   - `download`: fetch and extract CDD databases and annotation files
   - `check`: verify local setup completeness
   - `run`: execute the `rpsblast -> rpsbproc` pipeline

This design is deliberate. The language model is used where interpretation and user interaction are needed; the shell script is used where consistency and repeatability matter.

## 4. A New Interaction Model for Bioinformatics Tools

The skill introduces a practical pattern for using legacy or expert-oriented scientific software in an AI environment.

### 4.1 Natural language becomes the front end

Instead of manually assembling commands, users can ask an AI agent for outcomes:

```text
Use $rpsblast-assistant to download the minimal CDD database and rpsbproc annotation files into ./db and ./data.
```

or:

```text
Use $rpsblast-assistant to run rpsblast on ./sequence.fasta against ./db/Cdd with E-value 0.01 and then post-process with rpsbproc.
```

The agent maps these requests to explicit shell operations, while still exposing the exact command lines it runs. This matters because natural language should improve usability without erasing auditability.

### 4.2 The agent becomes a workflow governor

A useful AI interface does more than generate commands. It should also prevent common failure modes. In this skill, the agent is expected to:

- select `rpsblast` for protein queries and `rpstblastn` for nucleotide queries
- default to the article's worked local threshold of `0.01` unless told otherwise
- force ASN.1 archive output when `rpsbproc` is required
- stop early if databases or annotation files are missing
- explain the difference between intermediate and final outputs

This is a subtle but important shift. The model is not acting as an oracle; it is acting as a guardrailed operator.

### 4.3 Output interpretation becomes part of the workflow

In many command-line tools, execution and interpretation are treated as separate tasks. The AI layer makes it natural to unify them. After running `rpsblast`, the same agent that launched the workflow can explain the resulting `.out` file, identify the data-bearing section, and summarize what the reported domain hits mean. This shortens the distance between computation and understanding.

## 5. What Changes in the AI Era

The AI era does not eliminate the need for scientific rigor. It changes where complexity lives.

Previously, complexity lived mostly in the user's head. The user had to remember URLs, flags, formats, and file relationships. With skills like `rpsblast-assistant`, complexity is moved into a reusable operational layer:

- the workflow becomes inspectable
- the defaults become explicit
- the tool becomes easier to delegate
- onboarding becomes faster
- reproducible use becomes easier to standardize across a lab or team

This is especially important for mixed teams. A computational biologist may already know how to use `rpsblast`, but a bench scientist, project manager, trainee, or collaborator may not. A natural-language skill narrows that gap without flattening the underlying method into a black box.

## 6. Limitations and Guardrails

This approach improves usability, not biological validity. Several constraints remain:

- users still need the official NCBI binaries and CDD assets
- local network availability still matters for download steps
- AI agents can choose defaults, but they cannot remove the need for judgment about query quality, threshold selection, or downstream interpretation
- version changes in BLAST+, CDD, or `rpsbproc` may alter behavior or output details

Accordingly, the skill is designed to expose commands, file paths, and output types rather than hide them. The goal is assisted operation, not opaque automation.

## 7. Conclusion

`rpsblast-assistant` demonstrates a broader pattern for scientific computing in the AI era. Mature command-line tools do not need to be rewritten to benefit from modern AI systems. Instead, they can be wrapped in disciplined skills that combine public reference knowledge, deterministic scripts, and natural-language orchestration. In this model, `rpsblast` remains the engine, but the user experience changes dramatically. A task that once required detailed procedural memory can now begin with a sentence.

That shift matters. It lowers adoption barriers, reduces setup mistakes, and makes proven bioinformatics workflows available to a wider range of researchers without compromising the underlying computational method. The future of scientific tooling may not be purely graphical or purely conversational. It may be skill-based: language on the outside, validated commands underneath.
