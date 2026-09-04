OpenAI insurance extraction output

- One structured JSON file mirrors each source Markdown document.
- documents.jsonl contains one record per source document.
- policies.jsonl contains one flattened record per extracted policy.
- manifest.csv includes each policy and its quick summary.
- plans and plan-specific benefit amounts preserve tiered claim tables.
- extraction_report.json includes token usage, estimated cost, quality, and review counts.
- Every extracted policy, benefit, rider, and exclusion carries line-numbered evidence.
- Null means the brochure did not state the field reliably.
