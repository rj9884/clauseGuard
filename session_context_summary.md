# ClauseGuard Evaluation Session Context Summary

## 1. Objective
Establish and execute a robust legal risk-clause extraction evaluation harness for ClauseGuard, benchmarking it against the expert-annotated Atticus CUAD v1 dataset (15-document test split) to measure Precision, Recall, F1-Score, and Latency under two scopes (Model Quality vs. Overall Pipeline Utility).

## 2. Completed Work
- **Strict Validation & Quota Exhaustion Failsafe:** Added a `--sample N` flag in [evaluate.py](file:///home/rajan/Coding/clauseGuard/backend/evaluate.py). When specified, it limits the run to `N` documents and disables local fallback entirely, causing any rate limits or daily API quota exhaustions to hard-fail immediately (raising `RuntimeError`).
- **Separate Metric Tables:** Refactored metric aggregation so classification results are tagged with their source (`"live_llm"` or `"fallback_simulation"`). The script now displays and logs two completely separate tables (Model Quality and Pipeline Utility) for Live LLM and Fallback simulations, preventing hybrid results from skews or padding.
- **Persistent Live History Log:** Implemented a log file [live_evaluation_history.json](file:///home/rajan/Coding/clauseGuard/backend/live_evaluation_history.json) that appends and tracks metrics for documents completed fully live in strict validation mode, preventing duplicate counts on reruns.
- **Evaluation Loop Skipping Mechanism:** Added a lookup check in [evaluate.py](file:///home/rajan/Coding/clauseGuard/backend/evaluate.py) that reads from [live_evaluation_history.json](file:///home/rajan/Coding/clauseGuard/backend/live_evaluation_history.json) to automatically skip already-evaluated contracts on subsequent reruns, preventing redundant API calls and conserving precious quota.
- **Robust Transient Error Retries:** Refactored error handling in [evaluate.py](file:///home/rajan/Coding/clauseGuard/backend/evaluate.py) to ensure transient network/HTTP errors (like 502 Bad Gateway or Timeout) are retried up to `max_retries` before aborting in strict validation mode, rather than failing fast on the first attempt.
- **OpenRouter API Integration:** Added `OPENROUTER_API_KEY` and `OPENROUTER_MODEL=openrouter/free` to [.env](file:///home/rajan/Coding/clauseGuard/.env), [.env.example](file:///home/rajan/Coding/clauseGuard/.env.example), and [SETUP.md](file:///home/rajan/Coding/clauseGuard/SETUP.md) to enable an independent, cost-effective evaluation path.
- **Budget Relevance Pre-filtering (Option B):** Addressed the 20-clause recall truncation limit on long agreements by introducing a cheap, local keyword relevance scoring heuristic (`score_clause_relevance` and `select_top_clauses`) in both [evaluate.py](file:///home/rajan/Coding/clauseGuard/backend/evaluate.py) and [analyzer.py](file:///home/rajan/Coding/clauseGuard/backend/analyzer.py). It pre-filters all clauses, selecting and order-preserving the top 20 most critical risk-bearing clauses (IP, liability, termination, non-compete) to route to the LLM.
  - *Impact:* Within-Scope Overlap Recall rose from **11.1%** to **76.3%**, and Full-Document Overlap Recall rose from **6.1%** to **72.5%** on the CUAD test set.
- **Documentation Updated:** Saved local results to [evaluation_results.md](file:///home/rajan/Coding/clauseGuard/backend/evaluation_results.md) and updated the Evaluation section of [README.md](file:///home/rajan/Coding/clauseGuard/README.md).


## 3. Key Decisions & Rationale
- **Heuristic Pre-Filtering over Capping Expansion:** Keeping the 20-clause processing budget but pre-filtering clauses based on risk keywords ensures zero additional API costs or latencies while capturing deep-document clauses (IP/non-compete) previously missed by simple truncation.
- **Strict Table Separation:** Keeping Live LLM metrics and Fallback Keyword Simulation metrics completely separate guarantees that the reported benchmarks accurately represent actual model classification performance rather than local regex keyword fallback.
- **Cumulative Live Logging:** Logging completed strict mode runs persistently allows accumulating a 100%-real sample of live model performance across multiple days, bypassing free-tier rate limits.

## 4. Current State & Constraints
- **Gemini API Quota:** The user's Gemini API key is free-tier and daily quota-exhausted (returning HTTP 429).
- **Standard Mode Results:** Full 15-document hybrid benchmarks are logged in [evaluation_results.md](file:///home/rajan/Coding/clauseGuard/backend/evaluation_results.md) and [README.md](file:///home/rajan/Coding/clauseGuard/README.md).
- **Strict Mode Results:** A cumulative run history log has been established at [live_evaluation_history.json](file:///home/rajan/Coding/clauseGuard/backend/live_evaluation_history.json) (currently initialized with 0 completed documents due to immediate 429 quota failures).

## 5. Relevant Code/Files/Data
- **Evaluation Script:** [evaluate.py](file:///home/rajan/Coding/clauseGuard/backend/evaluate.py)
- **Legal Risk Analyzer:** [analyzer.py](file:///home/rajan/Coding/clauseGuard/backend/analyzer.py)
- **Cumulative Live Log:** [live_evaluation_history.json](file:///home/rajan/Coding/clauseGuard/backend/live_evaluation_history.json)
- **Current Run Results:** [evaluation_results.md](file:///home/rajan/Coding/clauseGuard/backend/evaluation_results.md)
- **Project Readme:** [README.md](file:///home/rajan/Coding/clauseGuard/README.md)

## 6. Exact Next Step
Once daily Gemini API quotas reset or a paid key is available, run the evaluation in strict sample validation mode to accumulate live evaluations (each completed document logs 20 live classification calls):
```bash
docker run --rm -e GEMINI_API_KEY="YOUR_WORKING_KEY" -e USE_GEMINI=true -v $(pwd)/backend:/app -w /app clauseguard-backend:eval python3 -u evaluate.py --sample 2
```
Verify that the run completes successfully, adds the documents to the running log, and reports cumulative live precision/recall/F1 metrics. Repeat over several days until you have at least 30–50 live classification calls logged.
