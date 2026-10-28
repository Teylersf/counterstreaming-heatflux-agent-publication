"""Prepare this study's agent-only editions, without any publication operation.

Requires the adjacent canonical checkout after its final Markdown conversion.
Writes only this agent-publication directory. No credentials or API mutations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT.parent / "counterstreaming-heatflux-audit"
CANONICAL_REPOSITORY = "https://github.com/Teylersf/counterstreaming-heatflux-audit"
AGENT_REPOSITORY = "https://github.com/Teylersf/counterstreaming-heatflux-agent-publication"
TARGET_VERSION = "1.1.0"
EXPECTED_CODE_COMMIT = "0d07de76f3d0b56e49e9ef2b9de931b8567ad0c8"
GIST_ID = "gist:7c74312cf47dcc31c789a8b1c3dedd25"
AGENT_ID = "agent_29b9bf7a"
REQUIRED_SECTIONS = ["Introduction", "Related Work", "Methodology", "Results",
                     "Discussion", "Limitations", "Conclusion"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w-]+\b", text))


def math_segments(text: str) -> list[str]:
    return re.findall(r"\$\$.*?\$\$|(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)", text, re.S)


def markdown_headings(text: str) -> list[tuple[int, int, int, str]]:
    """ATX headings outside fenced code, including shell comments inside fences."""
    found, position, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if marker:
            token = marker[1]
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1] and not marker[2].strip():
                fence = None
        elif fence is None:
            m = re.match(r"^(#{1,6}) (.+?)(?: +#+)?\s*$", line.rstrip("\r\n"))
            if m:
                found.append((position, position + len(line), len(m[1]), m[2]))
        position += len(line)
    assert fence is None, "Unclosed code fence in canonical Markdown"
    return found


def markdown_sections(text: str) -> dict[str, str]:
    headings = [h for h in markdown_headings(text) if h[2] == 1]
    result = {h[3]: text[h[1]:headings[i + 1][0] if i + 1 < len(headings) else len(text)].strip()
              for i, h in enumerate(headings)}
    assert len(result) == len(headings), "Duplicate canonical section headings"
    return result


def title_only(heading: str) -> str:
    return re.sub(r"^(?:\d+|[A-Z])\.?\s+", "", heading)


def nested(text: str, heading: str) -> str:
    # Only headings and relative image links change; equations remain verbatim.
    text = text.strip()
    for start, _, level, _ in reversed(markdown_headings(text)):
        if 2 <= level <= 4:
            text = text[:start] + "##" + text[start:]
    text = text.replace("../figures/", "figures/")
    return "### " + heading + "\n\n" + text


def plain_tex(text: str) -> str:
    text = re.sub(r"\\(?:texttt|textbf|emph|url)\{([^{}]*)\}", r"\1", text)
    return text.replace("{", "").replace("}", "").replace("~", " ").replace("--", "–")


def references() -> tuple[list[dict], dict[str, str]]:
    """Read this study's actual BibTeX and its compiled citation numbering."""
    bib = (CANONICAL / "paper/references.bib").read_text(encoding="utf-8")
    entries = {}
    for chunk in re.split(r"(?m)^@", bib)[1:]:
        key = re.match(r"\w+\{([^,]+),", chunk)[1]
        fields = {}
        for line in chunk.splitlines()[1:]:
            match = re.fullmatch(r"\s*(\w+)\s*=\s*\{(.*)\},?\s*", line)
            if match:
                fields[match[1].lower()] = match[2]
            elif line.strip() and line.strip() != "}" and not re.fullmatch(r"\s*month\s*=\s*\w+,?\s*", line):
                raise AssertionError("Unsupported BibTeX field, inspect instead of guessing: " + line)
        entries[key] = fields
    aux = (CANONICAL / "paper/main.aux").read_text(encoding="utf-8")
    numbering = dict(re.findall(r"\\bibcite\{([^}]+)\}\{([^}]+)\}", aux))
    assert len(numbering) >= 8, "Canonical compilation has fewer than eight references"
    assert set(numbering) <= set(entries), "Compiled bibliography key missing from BibTeX"
    result = []
    for key in sorted(numbering, key=lambda item: int(numbering[item])):
        f = entries[key]
        authors = []
        for author in re.split(r"\s+and\s+", f["author"]):
            author = plain_tex(author)
            if "," in author:
                last, first = author.split(",", 1)
                author = first.strip() + " " + last.strip()
            authors.append(author)
        ref = {"ref_id": numbering[key], "type": "external",
               "source": "doi" if "doi" in f else "arxiv" if key == "original" else "url",
               "title": plain_tex(f["title"]), "authors": authors, "url": f["url"]}
        if "year" in f:
            ref["year"] = int(f["year"])
        if "doi" in f:
            ref["doi"] = f["doi"]
        if key in {"osirisudist", "osirisloader"}:
            assert "year" not in f, "Do not invent a year for the undated OSIRIS guide"
            ref["venue"] = ("OSIRIS Reference Guide" if key == "osirisudist" else plain_tex(f["howpublished"])) + "; undated; accessed 28 October 2026; conditional public documentation/source, not identification of the original simulation build"
        elif "journal" in f:
            ref["venue"] = plain_tex(f["journal"]) + " " + f.get("volume", "") + ", " + plain_tex(f.get("pages", ""))
        elif key == "original":
            ref["venue"] = "arXiv:2607.07106v1; submitted 8 July 2026"
        else:
            ref["venue"] = plain_tex(f.get("howpublished", ""))
        result.append(ref)
    assert [r["ref_id"] for r in result] == [str(i) for i in range(1, len(result) + 1)]
    return result, numbering


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publishfun-id", help="Verified new-study internal paper identifier")
    parser.add_argument("--publishfun-state", default="not_submitted", choices=["not_submitted", "under_review", "revision_requested", "failed", "accepted", "published", "rejected", "withdrawn"])
    parser.add_argument("--publishfun-public-id", help="Verified new-study public identifier")
    parser.add_argument("--publishfun-stage", help="Actual verified platform stage, separately from the adapter's coarse review state")
    parser.add_argument("--publishfun-round", type=int, help="Actual verified review round")
    parser.add_argument("--publishfun-review-closed-verified", action="store_true",
                        help="Use only after verifying this study's editorial review is closed or it is released")
    parser.add_argument("--airaxiv-public-id", help="Verified new-study public preprint identifier")
    parser.add_argument("--airaxiv-public-version", help="Verified public version label, for example v1")
    parser.add_argument("--airaxiv-submission-id", help="Verified new-study submission identifier")
    parser.add_argument("--airaxiv-current-canonical-version-verified", action="store_true",
                        help="Use only after checking that the public preprint contains this canonical revision")
    args = parser.parse_args()
    if args.publishfun_state == "not_submitted" and (args.publishfun_id or args.publishfun_public_id):
        parser.error("A verified Publish.fun identifier needs its verified non-default state")
    if (args.publishfun_stage or args.publishfun_round) and not args.publishfun_id:
        parser.error("An actual Publish.fun stage/round requires this study's verified internal identifier")
    if args.publishfun_round is not None and args.publishfun_round < 1:
        parser.error("Review round must be a positive integer")
    if args.airaxiv_public_version and not (args.airaxiv_public_id and re.fullmatch(r"v[1-9]\d*", args.airaxiv_public_version)):
        parser.error("A public AiraXiv version needs a verified public identifier and a v1-style version label")
    if args.airaxiv_current_canonical_version_verified and not (args.airaxiv_public_id and args.airaxiv_public_version):
        parser.error("Verifying the current canonical preprint requires a public ID and version")
    if args.publishfun_state == "published" and not args.publishfun_public_id:
        parser.error("Published requires a verified new-study public identifier")
    if args.publishfun_review_closed_verified and not (args.publishfun_id or args.publishfun_public_id):
        parser.error("Verified closure requires this study's verified identifier")
    closed = args.publishfun_state in {"accepted", "published", "rejected", "withdrawn"}
    if args.publishfun_review_closed_verified and not closed:
        parser.error("An active, failed or unsubmitted review does not establish closure")
    gate = bool(closed and args.publishfun_review_closed_verified)
    meta = json.loads((CANONICAL / "submissions/metadata.json").read_text(encoding="utf-8"))
    version = meta.get("version", "").lstrip("v")
    assert version == TARGET_VERSION, ("Regenerate the final canonical conversion first", version)
    source_path = CANONICAL / "submissions/manuscript.md"
    source = source_path.read_text(encoding="utf-8")
    sections = markdown_sections(source)
    headings = {title_only(h): h for h in sections}
    expected = ["Introduction and scope", "Initial-state matching in the supplied input decks",
                "An auxiliary homogeneous linear-stability test", "A secondary continuity clarification",
                "Conditioning a relative heat-flux accuracy claim", "Finite isotropization over a comparison interval",
                "Reproducible calculations and evidence limits", "Consequences for controlled validation", "Conclusion"]
    assert all(h in headings for h in expected), sorted(set(expected) - set(headings))
    intro = sections[headings[expected[0]]]
    related_match = re.search(r"^## (?:\d+(?:\.\d+)*\.?\s+)?Relation to established work\s*$", intro, re.M)
    audited_match = re.search(r"^## (?:\d+(?:\.\d+)*\.?\s+)?Audited version and available evidence\s*$", intro, re.M)
    assert related_match and audited_match and related_match.start() < audited_match.start(), "Inspect converted Introduction subsection headings"
    intro_body = intro[:related_match.start()].strip()
    related = intro[related_match.end():audited_match.start()].strip()
    audited = intro[audited_match.end():].strip()
    refs, ref_ids = references()
    release = CANONICAL_REPOSITORY + "/releases/tag/v" + version
    methods = (
        "This is a source-specific initial-state audit and reproducible continuum-closure study of arXiv:2607.07106v1. "
        "The original PDF was matched byte-for-byte with the versioned public PDF, and targeted claims were checked against rendered pages and the exact TeX archive. "
        "The authors' published decks and explicit data dictionary define the PIC ordinary-velocity moments. Five archived t=0 Gkeyll BP snapshots were reloaded through official ADIOS2 and checked against their byte-identical embedded Lua inputs. All fluid components are compared over the full grid, and complete 640-row x-averaged profiles corroborate the initial-state mismatch. "
        "Complete ZIP central-directory inventories identify no native deposited-current diagnostic in the posted PIC archive. Selected HDF5 and BP members are checked by CRC32 and pinned SHA-256; whole-archive MD5 was not independently verified. "
        "The original eight-group verification suite is retained unchanged. Three additional revision programs reload BP output, evaluate profile sensitivity and compute a conditional finite-temperature public-loader prediction. Three figures accompany these calculations. The loader and quadratic-shape calculations are unfitted conditional tests, not certification of the original executable or custom diagnostic kernel. No new OSIRIS or Gkeyll reconnection simulation or current-sheet eigenanalysis was performed. "
        "The reference list retains the canonical compiled citation order. The original identities are preserved as valid; this study does not claim their general derivation as new.\n\n"
        "### Agent authorship, tools and funding\n\n"
        "Lattice Audit Agent is the venue-specific agent author. Taylor Kalin is the human operator and author of the canonical study. "
        "OpenAI Codex assisted with source inspection, derivations, code, data analysis and manuscript preparation under his direction. "
        "The exact underlying model identifier was not recorded. Separate AI-agent checks are not independent human expert review. "
        "Exact total token usage was not recorded: total_tokens=-1 is an explicit missing-data sentinel, not a measurement or negative usage. "
        "Taylor Kalin self-funded this study, including computing resources and AI tools. No external funding was received. No competing interests were reported."
    )
    if args.publishfun_state == "not_submitted":
        pf = "No Publish.fun submission is asserted; its new-study identifiers are unknown."
    else:
        pf = "The recorded Publish.fun state is " + args.publishfun_state + "."
        if args.publishfun_id:
            pf += " Its verified internal identifier is " + args.publishfun_id + "."
        if args.publishfun_stage:
            pf += " Its actual current platform stage is " + args.publishfun_stage
            if args.publishfun_round:
                pf += ", round " + str(args.publishfun_round)
            pf += "; the adapter records state " + args.publishfun_state + ", which does not by itself establish verified review closure."
        if args.publishfun_public_id:
            pf += " Its verified public record is https://publish.fun/papers/" + args.publishfun_public_id + "."
    if args.airaxiv_public_id:
        air = "The verified AiraXiv public record is https://airaxiv.com/papers/view/" + args.airaxiv_public_id + "/."
        if args.airaxiv_public_version:
            air += " Its verified public version is " + args.airaxiv_public_version + "."
        if args.airaxiv_submission_id:
            air += " Its recorded submission identifier is " + args.airaxiv_submission_id + "."
        air += (" The public preprint is verified to contain canonical version " + version + "." if args.airaxiv_current_canonical_version_verified else
                " These retained venue identifiers do not assert that the present canonical revision has already replaced that public preprint.")
    elif args.airaxiv_submission_id:
        air = "AiraXiv submission " + args.airaxiv_submission_id + " is recorded; no public identifier or moderation outcome is asserted."
    else:
        air = "No AiraXiv submission or public identifier is asserted."
    dissemination = (
        "This agent-only edition and the Taylor Kalin canonical manuscript are versions of one study, not independent new findings. "
        "The operator authorized the agent byline for venues that require one. The canonical repository is " + CANONICAL_REPOSITORY + "; the versioned release target is " + release + ". "
        + pf + " " + air + " "
        + ("The operator has supplied verified closure of this study's Publish.fun review. " if gate else "The agent-venue review-sequence gate remains false until this study's Publish.fun review is verified closed or released. ")
        + "Preparing local files does not establish a submission, review, acceptance, release or successful repository publication. Actual outcomes belong in the publication-status record."
    )
    results_titles = expected[1:7]
    appendices = [h for h in sections if re.match(r"^[A-Z]\.?(?:\s)", h)]
    assert {title_only(h) for h in appendices} == {"Source passages and artifact scope", "Pinned execution record"}, appendices
    expected_top = {meta["title"], "Abstract", "References", "Author and methods disclosure", "Prior dissemination and review sequencing", *[headings[h] for h in expected], *appendices}
    assert set(sections) == expected_top, sorted(set(sections).symmetric_difference(expected_top))
    # All scientific canonical prose is retained in its original order.
    body_sections = [
        {"heading": "Introduction", "content": intro_body + "\n\nHuman operator and canonical author: **Taylor Kalin**. Agent-only author of this edition: **Lattice Audit Agent**.", "citations": [ref_ids[k] for k in ("original", "dataset", "penrose1960")]},
        {"heading": "Related Work", "content": related, "citations": [r["ref_id"] for r in refs]},
        {"heading": "Methodology", "content": "### Audited version and available evidence\n\n" + audited + "\n\n" + methods, "citations": [ref_ids[k] for k in ("original", "dataset", "osirisudist", "osirisloader")]},
        {"heading": "Results", "content": "\n\n".join(nested(sections[headings[h]], headings[h]) for h in results_titles), "citations": [r["ref_id"] for r in refs]},
        {"heading": "Discussion", "content": sections[headings["Consequences for controlled validation"]], "citations": [ref_ids[k] for k in ("original", "dataset", "ng2019")]},
        {"heading": "Limitations", "content": "The source scope is arXiv:2607.07106v1 and its checked deposit. Actual fluid BP outputs were reloaded and their embedded inputs match the posted decks, but this does not identify a clean executable build. The PIC comparison remains a physical ordinary-velocity moment current; no native deposited-current file is identifiable in the complete posted inventory, so no direct native-current comparison or initial electric-field-transient measurement is claimed. The finite-temperature loading and quadratic-shape sensitivity are conditional on inspected public code and stated sampling assumptions; the original private build and custom velocity-diagnostic kernel are unverified. Selected-member CRC32/SHA-256 checks do not verify whole-archive MD5. No original author was contacted, private executable accessed or matched-state reconnection rerun performed. The auxiliary homogeneous nonrelativistic electrostatic example is not a sheet eigenanalysis, does not establish electromagnetic or relativistic sheet stability, and does not refute the source's application-specific instability claim. This diagnostic comment leaves the mismatch's nonlinear dynamical significance undetermined. The secondary continuity clarification and conditioned error bound do not disprove the source's empirical scan or valid mixture identities. Prior-art inspection is not exhaustive. Full Penrose article text was unavailable; its primary deposited abstract and metadata were checked and the calculation is explicit in the retained proof. Exact model identifier and token usage were not recorded; no independent human expert review is claimed.", "citations": [ref_ids[k] for k in ("original", "dataset", "penrose1960", "osirisloader")]},
        {"heading": "Conclusion", "content": sections[headings["Conclusion"]] + "\n\n### Dissemination and author credit\n\n" + dissemination, "citations": [ref_ids["original"]]},
        {"heading": "Appendix", "content": "\n\n".join(nested(sections[h], h) for h in appendices), "citations": [ref_ids[k] for k in ("original", "dataset", "osirisudist")]},
    ]
    body = "\n\n".join(s["content"] for s in body_sections)
    abstract = sections["Abstract"]
    assert math_segments(source) == math_segments(abstract + "\n\n" + body), "Canonical equation content/order changed or dropped"
    assert len(math_segments(source)) == 306, "Unexpected canonical v1.1.0 mathematics count"
    code_pattern = r"(?ms)^```[^\n]*\n.*?^```\s*$"
    code_source = re.findall(code_pattern, source)
    code_agent = re.findall(code_pattern, body)
    assert len(code_source) == 3 and code_source == code_agent, "A code fence or its contents changed"
    table_pattern = r"(?m)^\|.*(?:\n\|.*)+"
    tables_source = re.findall(table_pattern, source)
    tables_agent = re.findall(table_pattern, body)
    assert len(tables_source) == 5 and tables_source == tables_agent, "A canonical table changed"
    table_rows = sum(len(t.splitlines()) - 2 for t in tables_source)
    assert table_rows == 31, table_rows
    equation_tags = re.findall(r"\\tag\{(\d+)\}", source)
    assert equation_tags == [str(i) for i in range(1, 22)]
    proof_pattern = r"(?m)^\*\*Proof\.\*\*.*$|^#{2,6} Proof\s*$|^\\begin\{proof\}.*$"
    source_proofs = re.findall(proof_pattern, source)
    agent_proofs = re.findall(proof_pattern, body)
    assert source_proofs == agent_proofs, "Proof marker changed or lost"
    assert len(source_proofs) == 3
    body_words = count_words(body)
    assert 4000 <= body_words <= 15000, body_words
    assert len(meta["title"]) <= 200 and count_words(abstract) <= 500
    payload = {"title": meta["title"], "paper_type": "research_article", "abstract": abstract,
               "authors": [{"agent_id": AGENT_ID, "display_name": "Lattice Audit Agent", "model_type": "OpenAI Codex"}],
               "tags": ["plasma-physics", "magnetic-reconnection", "heat-flux-closure", "linear-stability", "reproducibility"],
               "sections": body_sections, "references": refs,
               "metadata": {"agent_model": "OpenAI Codex; exact underlying model identifier not recorded", "agent_platform": "Codex desktop", "total_tokens": -1,
                            "submission_note": "Taylor Kalin is canonical author and human operator. Lattice Audit Agent is the authorized venue-specific agent author. This is one study. All canonical equations, proofs, data methods and references are retained. Token usage is unknown; -1 is an explicit missing-data sentinel, not measured usage. Prepared review state: " + args.publishfun_state + ".",
                            "generation_params": {"token_usage_status": "not_recorded", "total_tokens_sentinel": -1, "token_usage_is_measurement": False, "exact_model_identifier_status": "not_recorded"}}}
    serialized = json.dumps(payload, ensure_ascii=False)
    assert not re.search(r"teylersf@gmail\.com|509[- ]?919[- ]?0487|mailto:|tel:", serialized)
    assert all(s["heading"] == h for s, h in zip(body_sections, REQUIRED_SECTIONS + ["Appendix"]))
    write_json(ROOT / "agentpub-payload.json", payload)
    header = "# " + meta["title"] + "\n\n**Agent author: Lattice Audit Agent**\n\n**Human operator and canonical author: Taylor Kalin**\n\n[Operator ORCID: 0009-0003-9000-9315](https://orcid.org/0009-0003-9000-9315)\n\n28 October 2026\n\n## Abstract\n\n" + abstract + "\n\n"
    paper = header + "\n\n".join("## " + s["heading"] + "\n\n" + s["content"] for s in body_sections)
    paper += "\n\n## References\n\n" + sections["References"] + "\n"
    assert math_segments(source) == math_segments(paper)
    (ROOT / "paper.md").write_text(paper, encoding="utf-8", newline="\n")
    now = datetime.now(timezone.utc).isoformat()
    verification = json.loads((CANONICAL / "results/verification.json").read_text(encoding="utf-8"))
    assert verification["all_assertions_passed"] is True and len(verification["groups"]) == 8
    environment = verification["environment"]
    for pin in environment["source_files"]:
        assert sha((CANONICAL / pin["path"]).read_bytes()) == pin["sha256"], "Verification result has a stale code pin: " + pin["path"]
    code_pin = json.loads((CANONICAL / "results/code-pin.json").read_text(encoding="utf-8"))
    assert code_pin["commit"] == EXPECTED_CODE_COMMIT
    for pin in code_pin["source_files"] + code_pin["revision_outputs"]:
        assert sha((CANONICAL / pin["path"]).read_bytes()) == pin["sha256"], "Revision code/output pin changed: " + pin["path"]
    metadata = {"aaes_version": "4.2", "title": meta["title"], "abstract": abstract,
                "author_ids": [GIST_ID], "submitted_at": now, "tags": payload["tags"],
                "generation_environment": {"model": payload["metadata"]["agent_model"],
                    "tools": ["Python " + environment["python"].split()[0], "NumPy " + environment["numpy"], "h5py " + environment["h5py"], "ADIOS2 2.13.0.1001 (isolated Linux BP reader)", "Matplotlib", "LaTeX", "Tectonic", "Pandoc"],
                    "prompt_strategy": "Source-specific diagnostic comment, archived PIC and BP-fluid reanalysis, conditional public-loader quadrature and explicit auxiliary continuum calculations",
                    "notes": "Human operator and canonical author: Taylor Kalin. Agent-only edition authorized. Self-funded with no external funding or reported competing interests. Exact model identifier and token usage not recorded. submitted_at is local package preparation, not proof of Registry registration. Review state: " + args.publishfun_state + "."},
                "novelty_statement": "Source-specific archived PIC-versus-reloaded-fluid initial-moment controls for arXiv:2607.07106v1, with complete profile diagnostics and an unfitted conditional public-loader calculation. The auxiliary homogeneous stability example is a calibration, not a current-sheet result or refutation of the source's application-specific instability claim. Valid mixture identities, known closure-dependent spectra, the Penrose criterion and continuity are established ingredients. No matched-state rerun or nonlinear causal consequence is established."}
    write_json(ROOT / "metadata.json", metadata)
    claims = [
        {"text": "The archived initial PIC and fluid velocity moments differ: the full x-averaged moment-current profile has a relative L2 difference of 9.87 percent, and the two lower-sheet central cells differ by about 11.6 percent. Reloaded fluid output corroborates the posted initializers to roundoff.", "kind": "finding", "status": "proposed", "evidence_summary": "Five CRC32/SHA-256 checked t=0 BP snapshots, embedded inputs byte-identical to the posted Lua decks, all 480x640 fluid cells checked, and full 640-row PIC/fluid profile comparisons.", "confidence_note": "Physical moment current and velocity-covariance pressure; no native deposited-current file is identifiable. Whole-archive MD5, a matched-state rerun and nonlinear causal significance remain unestablished."},
        {"text": "The inspected public unweighted thermal-momentum loading rule predicts a mean drift below its cold proper-velocity conversion. An unfitted quadratic-shape sensitivity further accounts for the scale of the archived lower-sheet drift reduction.", "kind": "finding", "status": "proposed", "evidence_summary": "Complete posted PIC deck audit, pinned public loader/deposition source, converged Gaussian quadrature and independent Cartesian moment checks; conditional pointwise and shape predictions remain separate.", "confidence_note": "Conditional on the public loading rule and stated sampling assumptions; the original executable and custom velocity-diagnostic kernel are not identified or certified."},
        {"text": "A specified homogeneous two-Maxwellian equilibrium stable to collisionless longitudinal electrostatic perturbations has an overstable mode in the stated finite-isotropization fluid closure.", "kind": "finding", "status": "proposed", "evidence_summary": "Explicit rational Penrose bound, linear system, eigenvalue residual, dielectric residual and Gauss-constraint checks.", "confidence_note": "Separate nonrelativistic continuum benchmark; no claim that this mode occurred in the source reconnection simulation or of general electromagnetic stability."},
    ]
    registration = {"source": "github:Teylersf/counterstreaming-heatflux-agent-publication", "submission": {"kind": "paper", "maturity": "final"},
                    "project": {"title": meta["title"], "summary": "Archived PIC and reloaded fluid initial-state controls with conditional loader calculations and an auxiliary continuum calibration for arXiv:2607.07106v1.", "research_question": "How do the archived initial physical moments differ, what does a conditional public loading rule explain, and which causal or sheet-stability conclusions remain untested?", "status": "active"}, "claims": claims}
    write_json(ROOT / "aaes-registration.json", registration)
    copied = []
    folders = ("experiments", "figures", "source-excerpts", "data/derived", "data/input-decks")
    singles = ("requirements.txt", "requirements-bp.txt", "SOURCE.md", "LICENSE-CODE", "LICENSE-MANUSCRIPT", "data/README.md", "data/provenance.json", "data/revision-README.md", "data/provenance-revision.json", "audit/ledger.md", "audit/prior-art.md",
               "results/artifact-manifest.json", "results/code-pin.json", "results/data-checks.json", "results/execution.log", "results/figure-manifest.json", "results/profile-sensitivity.json", "results/revision-data.json", "results/thermal-loading.json", "results/verification.json")
    paths = [p for folder in folders for p in (CANONICAL / folder).rglob("*") if p.is_file()]
    paths += [CANONICAL / p for p in singles]
    for src in sorted(set(paths)):
        if "__pycache__" in src.parts or src.suffix == ".pyc":
            continue
        relative = src.relative_to(CANONICAL)
        assert "raw" not in relative.parts and ".git" not in relative.parts
        assert src.suffix.lower() not in {".h5", ".hdf5", ".zip", ".tar", ".gz"}
        if src.suffix.lower() == ".pdf":
            assert relative.parts[0] == "figures", "Only the original analysis figure PDFs may be copied"
        dst = ROOT / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        b = src.read_bytes()
        assert b == dst.read_bytes()
        copied.append({"path": relative.as_posix(), "bytes": len(b), "sha256": sha(b)})
    figure_manifest = json.loads((CANONICAL / "results/figure-manifest.json").read_text(encoding="utf-8"))
    for figure in figure_manifest["figures"]:
        assert sha((ROOT / figure["path"]).read_bytes()) == figure["sha256"]
    figure_urls = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", source)
    assert len(figure_urls) == 3
    figure_files = []
    for url in figure_urls:
        png = Path("figures") / Path(urlparse(url).path).name
        for relative in (png, png.with_suffix(".pdf")):
            b = (CANONICAL / relative).read_bytes()
            assert sha((ROOT / relative).read_bytes()) == sha(b)
            figure_files.append({"path": relative.as_posix(), "bytes": len(b), "sha256": sha(b)})
    assert {p.name for p in (ROOT / "audit").iterdir() if p.is_file()} == {"ledger.md", "prior-art.md"}, "Private preparation note present in audit/"
    context = {"prepared_at_utc": now, "canonical_work_version": version, "publishfun_internal_id": args.publishfun_id,
               "publishfun_state": args.publishfun_state, "publishfun_public_id": args.publishfun_public_id,
               "publishfun_actual_stage": args.publishfun_stage, "publishfun_round": args.publishfun_round,
               "publishfun_review_closed_verified": args.publishfun_review_closed_verified,
               "airaxiv_submission_id": args.airaxiv_submission_id, "airaxiv_public_id": args.airaxiv_public_id,
               "airaxiv_public_version": args.airaxiv_public_version,
               "airaxiv_current_canonical_version_verified": args.airaxiv_current_canonical_version_verified,
               "agent_venue_submission_allowed_by_review_sequence": gate,
               "agentpub_paper_id": None, "aaes_paper_id": None, "agentpub_paper_created": False, "aaes_registry_paper_created": False}
    write_json(ROOT / "reproduction/publication-context.json", context)
    checks = {"canonical_manuscript_sha256": sha(source_path.read_bytes()), "agent_paper_sha256": sha((ROOT / "paper.md").read_bytes()),
              "canonical_math_segments": len(math_segments(source)), "agent_math_segments": len(math_segments(paper)),
              "all_math_segments_identical_and_in_same_order": True,
              "canonical_proof_markers": len(source_proofs), "agent_proof_markers": len(agent_proofs), "all_proof_markers_preserved": True,
              "numbered_equations": len(equation_tags), "all_21_equation_tags_preserved": True,
              "code_block_count": len(code_source), "all_code_blocks_identical": True,
              "table_count": len(tables_source), "table_data_rows": table_rows, "all_tables_identical": True,
              "body_word_count_regex": body_words, "body_word_count_whitespace": len(body.split()), "reference_count": len(refs),
              "reference_numbering_matches_compiled_aux": True, "undated_osiris_publication_year_omitted": True,
              "canonical_verification_group_count": len(verification["groups"]), "canonical_verification_groups": list(verification["groups"]),
              "canonical_figure_manifest": figure_manifest, "section_order": [s["heading"] for s in body_sections],
              "canonical_code_commit": code_pin["commit"], "canonical_three_figure_files": figure_files,
              "three_revision_programs_included": ["experiments/revision_data.py", "experiments/profile_sensitivity.py", "experiments/thermal_loading.py"],
              "only_public_audit_ledger_and_prior_art_copied": True,
              "canonical_result_sections_preserved": [headings[h] for h in results_titles], "copied_verbatim": copied,
              "no_owner_email_or_phone_in_agent_payload": True, "human_operator_is_not_agent_schema_coauthor": True,
              "token_usage_sentinel_is_not_measurement": True, "no_raw_data_or_original_or_canonical_paper_pdf_copied": not (ROOT / "data/raw").exists() and not (ROOT / "paper").exists(),
              "canonical_release_target": release, "publication_context": context, "all_adapter_assertions_passed": True}
    write_json(ROOT / "reproduction/adapter-checks.json", checks)
    print(json.dumps({k: checks[k] for k in ("body_word_count_regex", "reference_count", "canonical_math_segments", "canonical_proof_markers", "all_adapter_assertions_passed")}))


if __name__ == "__main__":
    main()
