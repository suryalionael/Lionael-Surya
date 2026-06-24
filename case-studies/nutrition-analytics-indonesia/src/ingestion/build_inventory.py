"""Generates docs/data_inventory.md from the real manifest + config metadata + data
contracts. The inventory is a derived artifact -- never hand-edit it; re-run this
after any ingestion change.

Usage: python -m src.ingestion.build_inventory
"""

import logging

import yaml

from src.utils.config import CONFIG_DIR, DOCS_DIR
from src.utils.provenance import latest_entries
from src.validation.contracts import Contract

log = logging.getLogger(__name__)

INVENTORY_PATH = DOCS_DIR / "data_inventory.md"


def load_metadata() -> dict:
    with open(CONFIG_DIR / "metadata.yml") as f:
        return yaml.safe_load(f)


def render(entries: dict[str, dict], metadata: dict) -> str:
    lines = [
        "# Data Inventory",
        "",
        "Generated automatically from `data/raw/_manifest.jsonl`, `config/metadata.yml`, "
        "and `docs/data_contracts/`. Do not hand-edit this file -- run "
        "`python -m src.ingestion.build_inventory` (or `make inventory`) after any "
        "ingestion change.",
        "",
        "| Dataset | Source | Vintage | Granularity | Rows | Validation | Manifest file |",
        "|---|---|---|---|---|---|---|",
    ]

    for slug in sorted(metadata.keys()):
        meta = metadata[slug]
        entry = entries.get(slug)
        if entry is None:
            lines.append(f"| {meta['display_name']} | {meta['source_name']} | _not yet fetched_ | province | - | - | - |")
            continue
        lines.append(
            f"| {meta['display_name']} | {entry['source_name']} | {entry['dataset_version']} | province | "
            f"{entry['rows']} | {entry['validation_status']} | `{entry['file_path']}` |"
        )

    lines += ["", "## Dataset Detail", ""]

    for slug in sorted(metadata.keys()):
        meta = metadata[slug]
        entry = entries.get(slug)
        lines.append(f"### {meta['display_name']} (`{slug}`)")
        lines.append("")
        if entry is None:
            lines.append("Not yet fetched. Run `make fetch` (BPS-sourced datasets require a real `BPS_API_KEY` in `.env`).")
            lines.append("")
            continue

        try:
            contract = Contract.load(slug)
            required_cols = ", ".join(contract.required_columns)
        except FileNotFoundError:
            required_cols = "(no contract found)"

        lines += [
            f"- **Source organization & URL:** {entry['source_name']} — {entry['source_url']}",
            f"- **Unit:** {meta.get('unit', 'n/a')}",
            f"- **Publication / fetch vintage:** {entry['dataset_version']}",
            f"- **Fetched at (UTC):** {entry['fetched_at_utc']}",
            f"- **Geographic granularity:** Province",
            f"- **Required columns:** {required_cols}",
            f"- **Rows / columns:** {entry['rows']} / {entry['columns']}",
            f"- **File size:** {entry['file_size_bytes']} bytes",
            f"- **SHA-256:** `{entry['sha256']}`",
            f"- **Validation status:** {entry['validation_status']}",
            "",
        ]

    return "\n".join(lines) + "\n"


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    entries = latest_entries()
    metadata = load_metadata()
    content = render(entries, metadata)
    INVENTORY_PATH.write_text(content)
    log.info("Wrote %s (%d datasets with manifest entries, %d total configured)", INVENTORY_PATH, len(entries), len(metadata))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
