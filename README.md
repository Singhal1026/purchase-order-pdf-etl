# 📦 PDF → ERP Pipeline

An automated pipeline that reads purchase-order PDFs from a shared drive, extracts item data with a local LLM, maps it against a reference sheet, and uploads it directly into an Infor BW ERP session.

---

## How It Works

```
Shared Drive (PDFs)
      │
      ▼
[1] Copy PDFs to local input/
      │
      ▼
[2] pdfplumber  →  extract DC code, PO number, items table text
      │
      ▼
[3] Ollama LLM  →  parse items into structured JSON
      │            { Article Code, Qty, Price }
      ▼
[4] Preprocessor  →  merge with reference Excel (SKU, BP CODE, W/H Code…)
      │
      ▼
[5] Write output.csv
      │
      ▼
[6] Infor BW ERP (bw.exe)  →  upload CSV, generate Excel report
      │
      ▼
[7] Optional cleanup of local input & shared drive files
```

---

## Project Structure

```
project/
├── main.py              # Orchestrator — runs all pipeline stages
├── pdf_extractor.py     # pdfplumber: extracts DC code, PO number, items text
├── llm_processor.py     # Ollama: converts raw text → structured JSON
├── preprocessor.py      # pandas: merges LLM output with reference Excel
├── validator.py         # Pydantic: schema validation (currently commented out)
├── erp_runner.py        # subprocess: drives bw.exe ERP upload session
├── logger.py            # Root logger: rotating file + console handler
├── config.ini           # All environment-specific settings (gitignored)
├── requirements.txt
└── .gitignore
```

---

## Prerequisites

| Dependency | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| [Ollama](https://ollama.com) | Local LLM server |
| `llama3.1:latest` | Default model (pull with `ollama pull llama3.1`) |
| Infor BW (`bw.exe`) | ERP upload client |
| Reference Excel | Article code → SKU / facility mapping |

---

## Setup

**1. Clone and create a virtual environment**
```bash
git clone <repo-url>
cd <project-folder>
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure `config.ini`**

Copy the template below, fill in your paths, and save as `config.ini` in the project root. This file is gitignored and should **never** be committed.

```ini
[paths]
shared_drive_path = \\server\share\purchase_orders
input_dir         = data\input
output_csv        = output\output.csv
reference_xlsx    = data\reference.xlsx
log_file          = logs\pipeline.log
excel_output_path = output\output.xlsx

[llm]
model       = llama3.1:latest
temperature = 0
max_retries = 1
retry_delay = 2

[erp]
bw_exe   = C:\Infor\bw.exe
bwc_file = C:\Infor\Test.bwc
session  = YOUR_SESSION_CODE

[pipeline]
delete_from_shared_drive_after_copy = no
delete_local_input_after_processing = no
```

**4. Start the Ollama server**
```bash
ollama serve
ollama pull llama3.1
```

**5. Run the pipeline**
```bash
python main.py
```

---

## Reference Excel Format

The pipeline expects a file at `data/reference.xlsx` (Sheet1) with at least these columns:

| Column | Description |
|---|---|
| `Article code` | Matches the Article Code extracted from the PO PDF |
| `SKU` | Internal SKU passed to the ERP |
| `facility_name 2` | Matches the DC code (e.g. `D001`) from the PDF |
| `BP CODE` | Business partner code |
| `Address Code` | Delivery address code |
| `Emp Code` | Employee / rep code |
| `W/H Code` | Warehouse code |

---

## Output CSV Columns

The CSV written to `output/output.csv` (and uploaded to ERP) has these columns in order:

```
Portal | po_num | BP CODE | Address Code | SKU_x | Qty | Price | Emp Code | Customer Name | W/H Code
```

---

## Logging

Logs are written to the path set in `config.ini → log_file`.

- **Rotating file handler**: max 5 MB per file, keeps last 3 files
- **Console**: INFO level and above
- **File**: DEBUG level and above (full LLM responses, subprocess commands, row-level detail)

```
2025-01-15 10:23:01 | INFO     | main            | Pipeline started at 2025-01-15 10:23:01
2025-01-15 10:23:02 | INFO     | pdf_extractor   | ./data/input/PO_123.pdf — Extracted PO: 4500012345 | DC: D001
2025-01-15 10:23:04 | INFO     | llm_processor   | LLM extracted 8 item(s)
2025-01-15 10:23:04 | INFO     | main            | PO_123.pdf — ready for upload (8 row(s))
2025-01-15 10:23:09 | INFO     | erp_runner      | Success: Excel report generated.
2025-01-15 10:23:09 | INFO     | main            | Pipeline finished — Uploaded: 1 | Skipped: 0 | Failed: 0
```

---

## Configuration Reference

| Section | Key | Default | Description |
|---|---|---|---|
| `paths` | `shared_drive_path` | — | UNC or local path where PDFs arrive |
| `paths` | `input_dir` | `data\input` | Local staging folder |
| `paths` | `output_csv` | `output\output.csv` | Merged CSV sent to ERP |
| `paths` | `reference_xlsx` | `data\reference.xlsx` | Article/facility mapping |
| `paths` | `excel_output_path` | `output\output.xlsx` | ERP-generated report |
| `paths` | `log_file` | `logs\pipeline.log` | Rolling log path |
| `llm` | `model` | `llama3.1:latest` | Any Ollama-served model |
| `llm` | `temperature` | `0` | 0 = deterministic |
| `llm` | `max_retries` | `1` | Retry attempts on LLM failure |
| `llm` | `retry_delay` | `2` | Seconds between retries |
| `erp` | `bw_exe` | — | Absolute path to `bw.exe` |
| `erp` | `bwc_file` | — | Absolute path to `.bwc` session file |
| `erp` | `session` | — | ERP session identifier |
| `pipeline` | `delete_from_shared_drive_after_copy` | `no` | Delete source PDFs after copy |
| `pipeline` | `delete_local_input_after_processing` | `no` | Delete local input after upload |

---

## Building a Standalone Executable (Windows)

The pipeline supports PyInstaller. Use `sys.frozen` detection already in `main.py`:

```bash
pyinstaller --onefile --name PO_Pipeline main.py
```

The `.exe` will look for `config.ini` in the same directory as itself.

---
