# Synthetic policy extraction fixtures

These one-page SVG documents are project-created test artifacts. They contain
no customer information, insurer branding, or copied policy wording. Names,
references, terms, and prices are fictional and exist only to evaluate the
CoverCheck extraction contract.

`manifest.json` is the frozen ground truth for fixture version `1.0.0`. Regions
use the SVG `1200 x 1600` view box and are expressed as `x`, `y`, `width`, and
`height`. Evaluation compares normalized typed values, not model prose:

- text is Unicode-normalized, trimmed, whitespace-collapsed, and case-folded;
- SGD amounts must match the exact integer dollar value;
- durations must match both integer value and unit;
- enumerations must match a declared contract value; and
- missing values must remain explicitly `unknown` and cannot match an invented
  value.

The exact OpenRouter model slug is not recorded here. It must be supplied through
`OPENROUTER_MODEL` only after DEC-002 is resolved, and every measured run must
record the configured slug, prompt version, date, latency, tokens, and cost.