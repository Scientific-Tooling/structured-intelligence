#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run.sh sources
  ./scripts/run.sh download [--db-dir <path>] [--data-dir <path>] [--download-dir <path>] [--db-set minimal|full|comma-list] [--include-data yes|no] [--extract yes|no]
  ./scripts/run.sh check --db-prefix <path> --data-dir <path> [--rpsblast-bin <path>] [--rpstblastn-bin <path>] [--rpsbproc-bin <path>]
  ./scripts/run.sh run --query <fasta> --db-prefix <path> --out-prefix <path> [--mode protein|nucleotide] [--evalue <num>] [--post yes|no] [--post-mode <mode>] [--rpsblast-bin <path>] [--rpstblastn-bin <path>] [--rpsbproc-bin <path>]

Subcommands:
  sources   Print the acquisition URLs described in the public article workflow.
  download  Download and extract CDD databases and rpsbproc annotation files.
  check     Verify that binaries, database files, and rpsbproc data files are present.
  run       Execute rpsblast/rpstblastn and optionally post-process with rpsbproc.
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

ensure_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || die "Missing file: $path"
}

require_any_match() {
  local pattern="$1"
  compgen -G "$pattern" > /dev/null || die "Missing files matching: $pattern"
}

find_bin() {
  local preferred="$1"
  if [[ -n "$preferred" ]]; then
    [[ -x "$preferred" ]] || die "Executable not found or not executable: $preferred"
    printf '%s\n' "$preferred"
    return
  fi
  if command -v "$2" >/dev/null 2>&1; then
    command -v "$2"
    return
  fi
  if command -v "$2.exe" >/dev/null 2>&1; then
    command -v "$2.exe"
    return
  fi
  die "Executable '$2' not found in PATH"
}

find_bin_or_empty() {
  local preferred="$1"
  local name="$2"
  if [[ -n "$preferred" ]]; then
    [[ -x "$preferred" ]] || return 1
    printf '%s\n' "$preferred"
    return 0
  fi
  if command -v "$name" >/dev/null 2>&1; then
    command -v "$name"
    return 0
  fi
  if command -v "$name.exe" >/dev/null 2>&1; then
    command -v "$name.exe"
    return 0
  fi
  return 1
}

print_sources() {
  cat <<'EOF'
BLAST+ executables (contains rpsblast/rpstblastn):
  https://ftp.ncbi.nih.gov/blast/executables/LATEST/

NCBI C++ toolkit source distribution:
  https://ftp.ncbi.nih.gov/toolbox

rpsbproc binaries and README:
  https://ftp.ncbi.nih.gov/pub/mmdb/cdd/rpsbproc/
  https://ftp.ncbi.nih.gov/pub/mmdb/cdd/rpsbproc/README

CDD preformatted databases:
  https://ftp.ncbi.nih.gov/pub/mmdb/cdd/little_endian/

CDD annotation/data files:
  https://ftp.ncbi.nih.gov/pub/mmdb/cdd/
EOF
}

download_file() {
  local url="$1"
  local dest="$2"
  echo "Downloading: $url"
  curl -fL --retry 3 --retry-delay 2 -o "$dest" "$url"
}

extract_tar_gz() {
  local archive="$1"
  local dest_dir="$2"
  mkdir -p "$dest_dir"
  tar -xzf "$archive" -C "$dest_dir"
}

extract_gzip_file() {
  local archive="$1"
  local dest_file="$2"
  mkdir -p "$(dirname "$dest_file")"
  gzip -dc "$archive" > "$dest_file"
}

db_archives_for_set() {
  case "$1" in
    minimal)
      printf '%s\n' "Cdd_LE.tar.gz" "Cdd_NCBI_LE.tar.gz"
      ;;
    full)
      printf '%s\n' \
        "Cdd_LE.tar.gz" \
        "Cdd_NCBI_LE.tar.gz" \
        "Cog_LE.tar.gz" \
        "Kog_LE.tar.gz" \
        "Pfam_LE.tar.gz" \
        "Prk_LE.tar.gz" \
        "Smart_LE.tar.gz" \
        "Tigr_LE.tar.gz"
      ;;
    *)
      local archive
      local archives=()
      IFS=',' read -r -a archives <<< "$1"
      for archive in "${archives[@]}"; do
        archive="${archive#"${archive%%[![:space:]]*}"}"
        archive="${archive%"${archive##*[![:space:]]}"}"
        [[ -n "$archive" ]] && printf '%s\n' "$archive"
      done
      ;;
  esac
}

download_cdd_assets() {
  local db_dir="db" data_dir="data" download_dir="" db_set="minimal" include_data="yes" extract="yes"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --db-dir) db_dir="${2:-}"; shift 2 ;;
      --data-dir) data_dir="${2:-}"; shift 2 ;;
      --download-dir) download_dir="${2:-}"; shift 2 ;;
      --db-set) db_set="${2:-}"; shift 2 ;;
      --include-data) include_data="${2:-}"; shift 2 ;;
      --extract) extract="${2:-}"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) die "Unknown option for download: $1" ;;
    esac
  done

  ensure_cmd curl
  ensure_cmd tar
  ensure_cmd gzip

  download_dir="${download_dir:-$db_dir/downloads}"
  mkdir -p "$db_dir" "$download_dir"
  if [[ "$include_data" == "yes" ]]; then
    mkdir -p "$data_dir"
  elif [[ "$include_data" != "no" ]]; then
    die "--include-data must be 'yes' or 'no'"
  fi

  if [[ "$extract" != "yes" && "$extract" != "no" ]]; then
    die "--extract must be 'yes' or 'no'"
  fi

  local db_base_url="https://ftp.ncbi.nih.gov/pub/mmdb/cdd/little_endian"
  local data_base_url="https://ftp.ncbi.nih.gov/pub/mmdb/cdd"
  local archive

  while IFS= read -r archive; do
    [[ -n "$archive" ]] || continue
    local archive_path="$download_dir/$archive"
    download_file "$db_base_url/$archive" "$archive_path"
    if [[ "$extract" == "yes" ]]; then
      echo "Extracting: $archive_path -> $db_dir"
      extract_tar_gz "$archive_path" "$db_dir"
    fi
  done < <(db_archives_for_set "$db_set")

  if [[ "$include_data" == "yes" ]]; then
    local data_file
    for data_file in bitscore_specific.txt cddannot.dat.gz cddannot_generic.dat.gz cddid.tbl.gz cdtrack.txt family_superfamily_links; do
      local data_path="$download_dir/$data_file"
      download_file "$data_base_url/$data_file" "$data_path"
      if [[ "$extract" == "yes" ]]; then
        case "$data_file" in
          *.gz)
            echo "Extracting: $data_path -> $data_dir/${data_file%.gz}"
            extract_gzip_file "$data_path" "$data_dir/${data_file%.gz}"
            ;;
          *)
            echo "Copying: $data_path -> $data_dir/$data_file"
            cp "$data_path" "$data_dir/$data_file"
            ;;
        esac
      fi
    done
  fi

  cat <<EOF
Download completed.
db_dir=$db_dir
data_dir=$data_dir
download_dir=$download_dir
db_set=$db_set
include_data=$include_data
extract=$extract
EOF
}

check_setup() {
  local db_prefix="" data_dir="" rpsblast_bin="" rpstblastn_bin="" rpsbproc_bin=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --db-prefix) db_prefix="${2:-}"; shift 2 ;;
      --data-dir) data_dir="${2:-}"; shift 2 ;;
      --rpsblast-bin) rpsblast_bin="${2:-}"; shift 2 ;;
      --rpstblastn-bin) rpstblastn_bin="${2:-}"; shift 2 ;;
      --rpsbproc-bin) rpsbproc_bin="${2:-}"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) die "Unknown option for check: $1" ;;
    esac
  done

  [[ -n "$db_prefix" ]] || die "--db-prefix is required"
  [[ -n "$data_dir" ]] || die "--data-dir is required"

  local rb
  local pb
  local rpstblastn_path=""
  rb="$(find_bin "$rpsblast_bin" "rpsblast")"
  pb="$(find_bin "$rpsbproc_bin" "rpsbproc")"
  rpstblastn_path="$(find_bin_or_empty "$rpstblastn_bin" "rpstblastn" || true)"

  require_any_match "${db_prefix}"'*'
  require_file "$data_dir/bitscore_specific.txt"
  require_file "$data_dir/cddannot.dat"
  require_file "$data_dir/cddannot_generic.dat"
  require_file "$data_dir/cddid.tbl"
  require_file "$data_dir/cdtrack.txt"
  require_file "$data_dir/family_superfamily_links"

  cat <<EOF
Setup looks complete.
rpsblast: $rb
rpsblast_nucleotide: ${rpstblastn_path:-not found in PATH; only needed for nucleotide queries}
rpsbproc: $pb
db prefix: $db_prefix
data dir: $data_dir
EOF
}

run_pipeline() {
  local query="" db_prefix="" out_prefix="" mode="protein" evalue="0.01" post="yes" post_mode="re"
  local rpsblast_bin="" rpstblastn_bin="" rpsbproc_bin=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --query) query="${2:-}"; shift 2 ;;
      --db-prefix) db_prefix="${2:-}"; shift 2 ;;
      --out-prefix) out_prefix="${2:-}"; shift 2 ;;
      --mode) mode="${2:-}"; shift 2 ;;
      --evalue) evalue="${2:-}"; shift 2 ;;
      --post) post="${2:-}"; shift 2 ;;
      --post-mode) post_mode="${2:-}"; shift 2 ;;
      --rpsblast-bin) rpsblast_bin="${2:-}"; shift 2 ;;
      --rpstblastn-bin) rpstblastn_bin="${2:-}"; shift 2 ;;
      --rpsbproc-bin) rpsbproc_bin="${2:-}"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) die "Unknown option for run: $1" ;;
    esac
  done

  [[ -n "$query" ]] || die "--query is required"
  [[ -n "$db_prefix" ]] || die "--db-prefix is required"
  [[ -n "$out_prefix" ]] || die "--out-prefix is required"
  require_file "$query"
  require_any_match "${db_prefix}"'*'

  local blast_bin
  case "$mode" in
    protein) blast_bin="$(find_bin "$rpsblast_bin" "rpsblast")" ;;
    nucleotide) blast_bin="$(find_bin "$rpstblastn_bin" "rpstblastn")" ;;
    *) die "--mode must be 'protein' or 'nucleotide'" ;;
  esac

  local raw_out
  if [[ "$post" == "yes" ]]; then
    raw_out="${out_prefix}.asn"
    local proc_bin
    proc_bin="$(find_bin "$rpsbproc_bin" "rpsbproc")"
    echo "Running: $blast_bin -query $query -db $db_prefix -evalue $evalue -outfmt 11 -out $raw_out"
    "$blast_bin" -query "$query" -db "$db_prefix" -evalue "$evalue" -outfmt 11 -out "$raw_out"

    local final_out="${out_prefix}.out"
    echo "Running: $proc_bin -i $raw_out -o $final_out -e $evalue -m $post_mode"
    "$proc_bin" -i "$raw_out" -o "$final_out" -e "$evalue" -m "$post_mode"

    cat <<EOF
Pipeline completed.
raw_asn=$raw_out
tabular_output=$final_out
EOF
  elif [[ "$post" == "no" ]]; then
    raw_out="${out_prefix}.asn"
    echo "Running: $blast_bin -query $query -db $db_prefix -evalue $evalue -outfmt 11 -out $raw_out"
    "$blast_bin" -query "$query" -db "$db_prefix" -evalue "$evalue" -outfmt 11 -out "$raw_out"
    cat <<EOF
Pipeline completed.
raw_asn=$raw_out
EOF
  else
    die "--post must be 'yes' or 'no'"
  fi
}

[[ $# -gt 0 ]] || { usage; exit 1; }

subcommand="$1"
shift

case "$subcommand" in
  sources) print_sources ;;
  download) download_cdd_assets "$@" ;;
  check) check_setup "$@" ;;
  run) run_pipeline "$@" ;;
  -h|--help) usage ;;
  *) die "Unknown subcommand: $subcommand" ;;
esac
