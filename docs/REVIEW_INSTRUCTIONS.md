# Task: Fresh-Eyes Review of Project Proposal

## What to do

Read and critically evaluate `proposal.md` in this directory. This is a resubmission for a Big Data course (CS-GY 6513) final project proposal. The TA rejected the first version for two reasons:

1. **Unrealistic data source/size** — original claimed 50-100GB from a broken API link
2. **Bloated tech stack** — original had 12 tools, many redundant

The proposal has been rewritten to address both. Your job is to evaluate whether the current version is solid or needs further changes.

## Context

- **Course:** CS-GY 6513, Big Data, Spring 2026, NYU
- **Infrastructure:** Google Cloud Dataproc cluster, HDFS, MapReduce (Python streaming)
- **TA feedback is in:** `proposal_rework_instructions.txt`
- **Original assignment instructions:** `project_proposal_instructions.txt`
- **Sample project report:** `Sample_Project_Report.pdf` (reference for expected complexity level)
- **Course CLAUDE.md:** `../CLAUDE.md` (has course conventions)

## What the project does

Detects insider trading on Polymarket geopolitical prediction markets. Pipeline: fetch trades via Polymarket CLOB API (1-month rolling window, ~20-50 geopolitics markets) → detect price spikes → trace large directional bets preceding spikes → score wallets against GDELT news timeline → classify insiders with Spark MLlib.

## Key decisions already made (don't re-litigate these)

- Scope narrowed to insider trading only (cut wash trading, collusion)
- Data from Polymarket CLOB API, not Polygonscan (which had a dead link)
- 1-month rolling window (CLOB API limitation), geopolitics markets only
- Dataset size: 2-4 GB (realistic for scope)
- Tech stack: HDFS/MapReduce, Hive/Tez, Spark SQL, BigQuery (for GDELT), Spark MLlib, Matplotlib
- MapReduce does raw aggregation, Spark SQL does spike detection + prescience scoring
- Manual market selection to start, automation later

## What to look for

1. **Does the proposal fully address the TA's two concerns?** (data feasibility + tool bloat)
2. **Is anything still overclaimed or unrealistic?** (e.g., can you actually get wallet-level trade data from the CLOB API? Is the prescience scoring methodology hand-wavy?)
3. **Is the tech stack justified?** Each tool should have a clear, non-redundant role.
4. **Does the writing match course expectations?** Check against `project_proposal_instructions.txt` for required sections.
5. **Are there gaps?** Missing sections, unclear methodology, unsupported claims?
6. **Is the size estimate defensible?** 2-4 GB for ~20-50 markets over 1 month.

## Output

Give a clear verdict: **ready to submit**, **minor tweaks needed** (list them), or **needs more work** (explain what). Be direct.
