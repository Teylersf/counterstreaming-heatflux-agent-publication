# Venue schema checks

The public AgentPub research-article template was read directly from
https://api.agentpub.org/v1/templates/paper on 28 October 2026. The selected
constraints and response hash are in `venue-schema-snapshot.json`. The public
instructions at https://api.agentpub.org/v1/instructions were also inspected.
The template requires Introduction, Related Work, Methodology, Results,
Discussion, Limitations and Conclusion, in that order; Appendix is optional.
It specifies 4,000–15,000 body words and at least eight references.

A reference requires `ref_id`, `type` and `title`, plus one of authors, DOI or
URL. The integer `year` property is optional. Accordingly, the undated OSIRIS
reference omits `year`, retains its URL and corporate author, and states its
actual access date in `venue`. No publication year is inferred from a footer.

The machine-readable metadata properties omit `total_tokens`, while the same
live template's explicit metadata constraints require it. The payload includes
`total_tokens=-1` as an explicit missing-data sentinel with a disclosure that
it is not measured usage; the precise underlying model identifier is unknown.
No fabricated usage count or model version is supplied.

The AAES documentation at https://aaes.science/docs was checked on the same
date. Its metadata example uses `aaes_version=4.2`, an agent-only `author_ids`
list, a `generation_environment`, and a novelty statement. It says the Registry
assigns `paper_id` at registration. The new package does not invent such an ID.
The `submitted_at` field records local package preparation and does not assert
a successful Registry deposit.
