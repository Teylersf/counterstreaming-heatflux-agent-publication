# Later publication checklist

Prepared on 28 October 2026. This file is a plan, not an execution record.
It does not change the current IDs or review-sequence gate.

1. Once the final canonical venue context is known, regenerate the adapter
   with this study's verified identifiers. During active review use
   `--publishfun-state under_review` or `revision_requested`, without
   `--publishfun-review-closed-verified`. The gate remains false. Do not
   substitute an earlier study's identifiers.
2. Review the allowlisted tree and `adapter-checks.json`; ensure `data/raw/`,
   credentials, original PDFs and full source archives are excluded. Commit
   this directory on `main`, then create/push the **public** repository
   `Teylersf/counterstreaming-heatflux-agent-publication` using the prepared
   directory as its source. No review is initiated by this checklist.

   After the local commit exists and the target is confirmed not to exist:

   ```sh
   gh repo create Teylersf/counterstreaming-heatflux-agent-publication --public --source E:/ALIVE/research/counterstreaming-heatflux-agent-publication --remote origin --push
   ```
3. Enable Discussions:

   ```sh
   gh repo edit Teylersf/counterstreaming-heatflux-agent-publication --enable-discussions
   ```

4. In the repository's Discussions tab, edit Categories, choose New category,
   name it exactly **AAES-Review**, choose **Open-ended discussion**, and
   create it. An announcement category would restrict who can start reviews.
   Creating the category does not require creating a discussion or review.
5. Verify public visibility, `has_discussions=true`, the exact category name,
   and raw access to `paper.md`, `metadata.json` and `reproduction/README.md`.
   Confirm the existing public identity Gist still contains exactly one valid
   AAES identity file for operator `Teylersf`; keep Registry-assigned paper IDs
   absent until registration actually succeeds.
6. While Publish.fun review is active, only local checks, public GET requests
   and AgentPub's **non-storing** `POST /v1/papers/check` may be used here.
   Do not call AgentPub `POST /v1/papers`, any draft-submit endpoint, or AAES
   `POST /api/v1/papers`. AAES registration immediately opens its review record.
7. When this study's Publish.fun review is verified closed or released, record
   that actual state and identifier and use
   `--publishfun-review-closed-verified`. Recheck the regenerated payload before
   any separately authorized venue submission.

The CLI accepts `--publishfun-id`, `--publishfun-state`,
`--publishfun-public-id`, `--publishfun-review-closed-verified`,
`--airaxiv-submission-id`, and `--airaxiv-public-id`. Its defaults are
`not_submitted`, null new-paper identifiers and gate false. Preparing a file
does not establish submission or successful repository publication.

Optional `--publishfun-stage` / `--publishfun-round` retain the actual platform
stage and round, and `--airaxiv-public-version` records the verified public
version separately from its identifier. The current package contains the
verified new-study identifiers in `publication-context.json` and remains gated
because Publish.fun round 1 is active. No repository has been created by the
adapter.

The AAES structure includes `reproduction/code/` and `reproduction/data/`
pointers to the actual top-level code and attributed data, plus
`reproduction/environment.yml`. The environment file describes recorded
dependency versions; no new conda-resolution test is asserted.

Sources: [AAES submission preflight](https://aaes.science/docs),
[AAES charter](https://aaes.science/charter),
[GitHub category instructions](https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-categories-for-discussions),
[AgentPub instructions and non-storing check](https://api.agentpub.org/v1/instructions).
