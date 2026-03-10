# RPS-BLAST Reference

This reference is distilled from the public HTML article at `https://pmc.ncbi.nlm.nih.gov/articles/PMC7378889/`, especially Basic Protocol 3 and Figures 19 to 21.

## What To Download

Standalone local execution uses four resource groups:

1. `rpsblast` or `rpstblastn`
   - Prebuilt BLAST+ executables:
     `https://ftp.ncbi.nih.gov/blast/executables/LATEST/`
   - The paper notes that the standalone executables are also available through the NCBI C++ toolkit distribution:
     `https://ftp.ncbi.nih.gov/toolbox`

2. `rpsbproc`
   - Binary downloads:
     `https://ftp.ncbi.nih.gov/pub/mmdb/cdd/rpsbproc/`
   - README with platform-specific setup notes:
     `https://ftp.ncbi.nih.gov/pub/mmdb/cdd/rpsbproc/README`

3. Preformatted CDD search databases
   - `https://ftp.ncbi.nih.gov/pub/mmdb/cdd/little_endian/`
   - The Windows example expands archives such as:
     - `Cdd_LE.tar.gz`
     - `Cdd_NCBI_LE.tar.gz`
     - `Cog_LE.tar.gz`
     - `Kog_LE.tar.gz`
     - `Pfam_LE.tar.gz`
     - `Prk_LE.tar.gz`
     - `Smart_LE.tar.gz`
     - `Tigr_LE.tar.gz`
   - In this repository's skill script, `download --db-set minimal` fetches `Cdd_LE.tar.gz` and `Cdd_NCBI_LE.tar.gz`; `download --db-set full` fetches the full list above.

4. CDD annotation/data files for `rpsbproc`
   - `https://ftp.ncbi.nih.gov/pub/mmdb/cdd/`
   - The paper's example lists:
     - `bitscore_specific.txt`
     - `cddannot.dat.gz`
     - `cddannot_generic.dat.gz`
     - `cddid.tbl.gz`
     - `cdtrack.txt`
     - `family_superfamily_links`
   - In this repository's skill script, `download` fetches these files by default unless `--include-data no` is used.

## Folder Layout

The paper's example uses a project folder with:

- query FASTA file, such as `sequence.fasta`
- executables: `rpsblast` or `rpstblastn`, plus `rpsbproc`
- `db/` holding the unpacked CDD database files
- `data/` holding the annotation files used by `rpsbproc`

Typical database prefix for the full CDD search is `db/Cdd`.

## Download Helper

The bundled script can download and unpack the files for you:

```bash
./skills/rpsblast-assistant/scripts/run.sh download --db-dir db --data-dir data
```

Useful variants:

```bash
# Download only the CDD core database subset and annotation files
./skills/rpsblast-assistant/scripts/run.sh download --db-set minimal --db-dir db --data-dir data

# Download the broader set of source databases listed in the article
./skills/rpsblast-assistant/scripts/run.sh download --db-set full --db-dir db --data-dir data

# Keep archives only, without extracting yet
./skills/rpsblast-assistant/scripts/run.sh download --extract no --download-dir downloads/cdd
```

## How To Run

The article's Windows example is:

```bash
rpsblast.exe -query sequence.fasta -db .\\db\\Cdd -evalue 0.01 -outfmt 11 -out sequence.asn
rpsbproc.exe -i sequence.asn -o sequence.out -e 0.01 -m re
```

Portable form on Unix-like shells is the same idea:

```bash
rpsblast -query sequence.fasta -db ./db/Cdd -evalue 0.01 -outfmt 11 -out sequence.asn
rpsbproc -i sequence.asn -o sequence.out -e 0.01 -m re
```

For nucleotide queries, switch from `rpsblast` to `rpstblastn`.

## Output Formats

- Raw standalone `rpsblast`/`rpstblastn` output must be saved as ASN.1 archive output when `rpsbproc` is needed.
  - The paper's command uses `-outfmt 11`.
  - The example file extension is `.asn`.
- `rpsbproc` reads that ASN.1 output and produces a compact, nonredundant tab-delimited flat file.
  - The example output file extension is `.out`.
  - The paper states this tab-delimited file can be opened in spreadsheet-style tools such as Excel.
  - The HTML article adds an important structural detail: the `.out` file has two sections.
    - First section: comment/template lines starting with `#`
    - Second section: the real tab-delimited data section, which starts with `DATA` and ends with `ENDDATA`
    - Inside the data section there can be multiple `SESSION` ... `ENDSESSION` blocks
    - Each query block may contain optional domains, sites, and motifs sections

## What The Result Contains

The paper describes the post-processed tabular output as suitable for further processing and containing items such as:

- domain hit intervals on the query
- E-values and scores
- domain model names and accessions
- domain superfamily information
- functional site positions
- structural motif information
- In the domains section, the HTML article explicitly says rows can include values such as session ID, query ID, hit type, PSSM ID, start and end position, E-value, bit score, accession, short name, terminal incompleteness flags, and superfamily PSSM ID.

## Operational Notes

- Running `rpsblast -help` or `rpsbproc -help` is the first local sanity check.
- The paper notes that standalone `rpsblast` sorts hits by E-value and that the BLAST default E-value threshold is 10, although the worked protocol uses `0.01`.
- The paper says `rpsblast` is the slower step for large batches: about 2 seconds per sequence on average in their note, so 10,000 sequences may take roughly 5 to 6 hours; `rpsbproc` is much faster on the resulting archive.
- The paper warns that updated versions of the CDD database, BLAST executables, or `rpsbproc` may yield slightly different results.
