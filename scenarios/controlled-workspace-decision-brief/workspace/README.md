# workspace/

The synthetic corpus the agent searches and reads from via
`search_workspace` / `read_artifact`. Contains:

- approved product, pricing, and security documents for two fictional
  products
- exactly one **unapproved** document, plausible enough to be useful but
  classified as not permitted — this is what the `forbidden_access`
  evaluator checks against for the `approved-sources-only` requirement,
  and what the `required_inspection` evaluator's required-values list
  excludes for `required-sources-read`

Each document carries a stable ID and an approval classification, so
deterministic evaluators can check exactly which sources were read or cited
without relying on free-text interpretation.
