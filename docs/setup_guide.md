# Setup Guide

**CS-GY 6513 Big Data, Spring 2026**  
Rodrigo Arguello (ra2646) | Shwetanshu Raj (sr8250)

---

## Can I view notebook outputs without running anything?

**Yes.** Every notebook (`detect.ipynb`, `trace.ipynb`, `score_v2.ipynb`, `classify.ipynb`) has already been executed and its outputs are saved inside the `.ipynb` file. You can read all charts, tables, and printed results by:

- **VSCode**: open the `.ipynb` file directly — outputs render inline
- **GitHub**: notebooks render automatically in the browser (outputs included)
- **JupyterLab**: `jupyter lab` → open the file, outputs are already there

You do **not** need GCP credentials, Spark, or a Python environment just to read results.

The `analysis/*_insights.md` files are plain markdown summaries of the key findings from each phase — read those first for a quick overview.

---

## Prerequisites (only needed if you want to re-run notebooks)

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12 | Use `pyenv` or download from python.org |
| Java (JDK) | 11 | Required by PySpark. OpenJDK 11 recommended |
| `gcloud` CLI | Any recent | For GCP authentication |
| GCP project access | — | Ask Shwetanshu to add your Google account as Editor on `sr8250-cs6513-polymarket` |

---

## Step 1 — Install Python 3.12

Check your version first:

```bash
python3 --version
```

If it shows anything other than 3.12.x, install it. On macOS the easiest way is via `pyenv`:

```bash
brew install pyenv
pyenv install 3.12.3
pyenv global 3.12.3
```

Or download the installer from [python.org/downloads](https://www.python.org/downloads/).

---

## Step 2 — Install Java 11

PySpark requires Java. Check if you already have it:

```bash
java -version
```

If missing or wrong version, install OpenJDK 11 on macOS:

```bash
brew install openjdk@11
echo 'export JAVA_HOME=$(brew --prefix openjdk@11)' >> ~/.zshrc
source ~/.zshrc
```

On Linux (Ubuntu/Debian):

```bash
sudo apt install openjdk-11-jdk
```

Verify:

```bash
java -version   # should show openjdk version "11.x.x"
```

---

## Step 3 — Clone the Repo

```bash
git clone <repo-url>
cd CS-GY6513-FinalProject
```

---

## Step 4 — Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows
```

Your prompt should now show `(venv)`.

---

## Step 5 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r req.txt
```

This installs everything: PySpark 4.1.1, Jupyter, google-cloud-bigquery, pandas, matplotlib, seaborn, and all transitive dependencies. It takes 2–3 minutes.

---

## Step 6 — Verify the Spark BigQuery JAR

The connector JAR is already in the repo at `jars/spark-bigquery-with-dependencies_2.12-0.36.1.jar`. Verify it is there:

```bash
ls jars/
# should show: spark-bigquery-with-dependencies_2.12-0.36.1.jar
```

If the file is missing (e.g., Git LFS issues), download it manually:

```bash
mkdir -p jars
curl -L -o jars/spark-bigquery-with-dependencies_2.12-0.36.1.jar \
  https://repo1.maven.org/maven2/com/google/cloud/spark/spark-bigquery-with-dependencies_2.12/0.36.1/spark-bigquery-with-dependencies_2.12-0.36.1.jar
```

---

## Step 7 — GCP Authentication

All notebooks read from and write to BigQuery in the project `sr8250-cs6513-polymarket`. You need application default credentials.

**First**, ask Shwetanshu to add your Google account as **Editor** on the GCP project (IAM console → Grant Access).

**Then**, authenticate on your machine:

```bash
gcloud auth application-default login
```

This opens a browser. Sign in with the Google account that has been granted access. A credentials file is stored at `~/.config/gcloud/application_default_credentials.json`.

Verify it works:

```bash
gcloud auth application-default print-access-token
# should print a long token string, not an error
```

---

## Step 8 — Register the Jupyter Kernel

So VSCode and JupyterLab can find the venv's Python:

```bash
source venv/bin/activate
python -m ipykernel install --user --name=polymarket-venv --display-name "Python (polymarket)"
```

In VSCode: open a notebook → click the kernel selector (top right) → choose **Python (polymarket)**.  
In JupyterLab: `jupyter lab` → open a notebook → Kernel menu → Change Kernel → Python (polymarket).

---

## Step 9 — Launch JupyterLab (optional)

```bash
source venv/bin/activate
cd CS-GY6513-FinalProject
jupyter lab
```

Opens at `http://localhost:8888`. Navigate to `analysis/` to open any notebook.

---

## Notebook Execution Order

The notebooks are not independent — each one writes a BigQuery table that the next one reads. Run them in this order if you want to re-execute the full pipeline from scratch:

| Order | Notebook | Reads from BQ | Writes to BQ |
|-------|----------|--------------|-------------|
| 1 | `pipeline/ingest.py` (script) | — | `markets`, `wallet_fills`, `ticks`, `prices` |
| 2 | `analysis/detect.ipynb` | `ticks` | `price_aggregates`, `spike_events` |
| 3 | `analysis/trace.ipynb` | `ticks`, `spike_events` | `suspect_wallets` |
| 4 | `analysis/score_v2.ipynb` | `suspect_wallets` | `wallet_features_v2` |
| 5 | `analysis/classify.ipynb` | `wallet_features_v2` | `ml_results_v2` |

> **Note:** All BigQuery tables are already populated from Shwetanshu's runs. You can open any notebook and run individual cells to explore results without re-running the full pipeline.

### Running ingest.py (Phase 2 — only if needed)

This is a plain Python script, not a notebook:

```bash
source venv/bin/activate
python3 pipeline/ingest.py
```

It reads from `data/` (gitignored — raw JSONL files) and writes to BigQuery. Since `data/` is not in the repo, this step requires Shwetanshu to share the raw data separately if you need it. The BigQuery tables it produces already exist.

---

## Project Structure Quick Reference

```
config/
  markets.json          6 market definitions (token IDs, resolution dates)
  known_suspects.jsonl  Ground truth insider wallets from public reporting

collect/                One-time data download scripts
  fetch_metadata.py       Gamma API → data/metadata/
  fetch_prices.py         CLOB API → data/prices/
  fetch_trades.py         Data API → data/trades/
  fetch_wallets.py        Goldsky subgraph → data/wallets/
  extract_ticks.py        Derives tick prices → data/ticks/

pipeline/
  ingest.py             PySpark: cleans and loads all data/ files → BigQuery

analysis/
  detect.ipynb          Phase 3: spike detection (z-score, rolling window)
  trace.ipynb           Phase 4: bet tracing per spike window
  score_v2.ipynb        Phase 5 v2: prescience scoring, USD-weighted win_rate
  score.ipynb           Phase 5 v1: original (count-based win_rate, kept for reference)
  classify.ipynb        Phase 6: Random Forest + K-Means (reads wallet_features_v2)

  *_insights.md         Key findings and Q&A for each phase
  *_charts/             PNG charts saved by each notebook

jars/                   Spark BigQuery connector JAR (included in repo)
docs/                   This file, proposal, API notes, checklists
req.txt                 Full pip dependency list (pip install -r req.txt)
```

---

## Common Issues

**`JAVA_HOME` not set / Spark fails to start**  
Make sure Java 11 is installed and `java -version` works before starting any notebook.

**`google.auth.exceptions.DefaultCredentialsError`**  
Run `gcloud auth application-default login` and make sure your Google account has been added to the GCP project.

**Kernel not found in VSCode**  
Run the `ipykernel install` command in Step 8, then reload VSCode.

**`ModuleNotFoundError` for any package**  
Make sure `(venv)` is active before launching Jupyter. If you opened JupyterLab without activating the venv first, close it, activate with `source venv/bin/activate`, and relaunch.

**JAR file missing**  
Use the `curl` command in Step 6 to download it directly from Maven Central.
