# Reproduce the audit

From this repository root, using Python and the pinned requirements:

```sh
python -m pip install -r requirements.txt
python experiments/fetch_data.py
python experiments/fetch_data.py --check-only
python experiments/data_checks.py
python -X utf8 experiments/verify.py
python -X utf8 experiments/make_figures.py
```

The downloader retrieves about 4.48 MB of selected compressed HDF5 members,
plus small headers, using serialized bounded HTTP Range requests. It reuses
verified cached files. It verifies each member's CRC32 and pinned SHA-256; it
does not claim to verify the publisher's whole-archive checksum. The raw cache
is not shipped in this repository. See `data/README.md` for moment definitions,
coordinates, diagnostic limitations and source attribution.

The complete suite has eight verification groups. It reanalyzes public initial
moments and checks explicit continuum models; it performs no new PIC or Gkeyll
reconnection run. Two scientific figures are regenerated from those calculations.
The scripts, derived profiles, posted input decks, provenance, figures and
canonical execution records are copied byte-for-byte. Their hashes are listed
in `adapter-checks.json`. No adjacent canonical checkout is needed to reproduce
the scientific checks; only regenerating this venue package requires one.

Running scientific scripts regenerates output and timestamps. Compare numerical
fields rather than expecting identical runtime timestamps or PDF metadata. If
a canonical artifact inventory includes the canonical paper PDF, that file is
linked at the canonical release target and is not copied into this package.

## Regenerate the local venue adapters

The packaging script requires the adjacent final canonical checkout:

```sh
python reproduction/prepare_packages.py
```

Defaults are `publishfun_state=not_submitted` and null identifiers for every
new venue paper. Update only with verified identifiers for this study:

```sh
python reproduction/prepare_packages.py --publishfun-id VERIFIED_NEW_INTERNAL_ID --publishfun-state under_review --airaxiv-submission-id VERIFIED_NEW_SUBMISSION_ID
```

A later closed or released review additionally requires the explicit
`--publishfun-review-closed-verified` flag before the review-sequence gate can
be true. `--publishfun-public-id` and `--airaxiv-public-id` accept only the
actual verified new-study records. A failed pipeline or request for revision
does not establish review closure. Preparation never submits a paper.

The current verified package was regenerated with:

```sh
python reproduction/prepare_packages.py --publishfun-id p_WA-Y00P8vp0DOnGc --publishfun-state under_review --publishfun-stage under_review --publishfun-round 1 --airaxiv-public-id 2610.0109 --airaxiv-public-version v1 --airaxiv-submission-id 1266
```

The actual Publish.fun stage is recorded separately from the adapter's coarse
state. Its earlier desk-review stage has advanced to active editorial review;
neither state establishes closure. Earlier preflight receipts remain in
`preflight-receipts/`, and `agentpub-preflight.json` records the latest check.

`prepare_packages.py` writes only this agent-publication directory. Its
assertions compare all canonical mathematical segments in order, preserve
proof headings, validate the current bibliography order against compiled
`main.aux`, keep the undated OSIRIS guide's publication year absent, and copy
only allowlisted public reproducibility files. The package's token-usage
sentinel and unknown exact model identifier are disclosed without fabrication.
