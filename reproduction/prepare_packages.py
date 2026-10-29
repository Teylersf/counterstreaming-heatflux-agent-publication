"""Prepare this study's agent-only editions, without any publication operation.

Requires the adjacent canonical checkout after its final Markdown conversion.
Writes only this agent-publication directory. No credentials or API mutations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT.parent / "counterstreaming-heatflux-audit"
CANONICAL_REPOSITORY = "https://github.com/Teylersf/counterstreaming-heatflux-audit"
AGENT_REPOSITORY = "https://github.com/Teylersf/counterstreaming-heatflux-agent-publication"
GIST_ID = "gist:7c74312cf47dcc31c789a8b1c3dedd25"
AGENT_ID = "agent_29b9bf7a"
PUBLIC_AUTHOR_METADATA = ("results/gkeyll-scan-supersession.json",)
REQUIRED_SECTIONS = ["Introduction", "Related Work", "Methodology", "Results",
                     "Discussion", "Limitations", "Conclusion"]
CONTROL_CASES = {"baseline_one_fluid": ("1-fluid-unmatched", "baseline", 1),
                 "baseline_two_fluid": ("2-fluid-unmatched", "baseline", 2),
                 "matched_one_fluid": ("1-fluid-aggregate-matched", "matched", 1),
                 "matched_two_fluid": ("2-fluid-aggregate-matched", "matched", 2)}


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


def agentpub_section_reorganization(sections: list[dict], abstract: str, refs: list[dict]) -> tuple[list[dict], dict]:
    """Move one intact methods subsection; never shorten scientific prose."""
    original = copy.deepcopy(sections)
    reorganized = copy.deepcopy(sections)
    by_name = {section["heading"]: section for section in reorganized}
    results = by_name["Results"]["content"]
    first = "#### 3.1 Intervention and implementation\n\n"
    following = "#### 3.2 Comparison quantities and scope\n\n"
    assert results.count(first) == results.count(following) == 1, "Inspect changed control-subsection structure before repackaging"
    start, end = results.index(first), results.index(following)
    assert end > start
    moved = results[start:end]
    assert not re.search(r"\\tag\{|\*\*Proof\.\*\*|!\[|(?m:^\|)", moved), "Relocated methods unexpectedly contain a numbered equation, proof, figure or table"
    note = ("### Implementation methods (AgentPub section arrangement)\n\n"
            "**AgentPub section-format note.** Canonical Section 3.1, “Intervention and implementation,” "
            "is placed intact in Methodology to meet AgentPub's per-section character limit. Its text "
            "appears exactly once. The [full agent-edition manuscript](" + AGENT_REPOSITORY +
            "/blob/main/paper.md) retains the original section order.")
    by_name["Results"]["content"] = results[:start] + results[end:]
    by_name["Methodology"]["content"] += "\n\n" + note + "\n\n" + moved
    before = "\n\n".join(section["content"] for section in original)
    after = "\n\n".join(section["content"] for section in reorganized)
    unnoted = after.replace(note, "", 1)
    assert after.count(note) == 1 and after.count(moved) == 1
    paragraphs = lambda text: Counter(part for part in text.split("\n\n") if part)
    assert paragraphs(before) == paragraphs(unnoted), "Scientific paragraphs changed, disappeared or duplicated"
    before_math, after_math = math_segments(abstract + "\n\n" + before), math_segments(abstract + "\n\n" + after)
    assert Counter(before_math) == Counter(after_math), "Payload math content/count changed during section relocation"
    equation_pattern = r"\\tag\{(\d+)\}"
    assert re.findall(equation_pattern, before) == re.findall(equation_pattern, after)
    proof_pattern = r"(?s)\*\*Proof\.\*\*.*?\$\\square\$"
    proofs = re.findall(proof_pattern, before)
    assert len(proofs) == before.count("**Proof.**") and proofs == re.findall(proof_pattern, after), "Complete proof text/order changed"
    tables = re.findall(r"(?m)^\|.*(?:\n\|.*)+", before)
    assert tables == re.findall(r"(?m)^\|.*(?:\n\|.*)+", after)
    captions = lambda text: [part for part in text.split("\n\n") if re.match(r"^\*\*(?:Figure|Table) \d+\.\*\*", part)]
    assert captions(before) == captions(after), "A full figure/table caption changed"
    images = re.findall(r"!\[[^\]]*\]\([^)]+\)", before)
    assert images == re.findall(r"!\[[^\]]*\]\([^)]+\)", after)
    code_pattern = r"(?ms)^```[^\n]*\n.*?^```\s*$"
    assert re.findall(code_pattern, before) == re.findall(code_pattern, after)
    numbers = lambda text: Counter(re.findall(r"(?<!\w)[+-]?\d[\d,.]*(?:[eE][+-]?\d+)?", text))
    assert numbers(before) == numbers(unnoted), "A quantitative literal changed"
    lengths = [{"heading": section["heading"], "unicode_codepoints": len(section["content"]),
                "utf16_code_units": len(section["content"].encode("utf-16-le")) // 2} for section in reorganized]
    assert max(max(row["unicode_codepoints"], row["utf16_code_units"]) for row in lengths) <= 49000, "AgentPub section exceeds the conservative character cap"
    words = count_words(after)
    assert 4000 <= words <= 15000
    required_words = count_words("\n\n".join(section["content"] for section in reorganized if section["heading"] != "Appendix"))
    assert 4000 <= required_words <= 15000
    assert [section["heading"] for section in reorganized] == REQUIRED_SECTIONS + ["Appendix"]
    assert all(section == original[index] for index, section in enumerate(reorganized)
               if section["heading"] not in {"Results", "Methodology"})
    report = {"operation": "AgentPub-only exact methods-subsection relocation; no prose condensation",
        "source_section": "Results", "destination_section": "Methodology", "moved_heading": first.strip(),
        "moved_characters": len(moved), "moved_block_sha256": sha(moved.encode()), "moved_block_exactly_once": True,
        "platform_note": note, "full_manuscript_url": AGENT_REPOSITORY + "/blob/main/paper.md",
        "observed_error_count_matches_original_results": len(results) == 52569,
        "original_results_unicode_codepoints": len(results), "original_results_utf16_code_units": len(results.encode("utf-16-le")) // 2,
        "counting_scope": "Per-section content. The observed 52569 equals original Results.content in both Unicode codepoints and UTF-16 units; the runtime metric cannot be distinguished from that sample.",
        "server_section_limit": 50000, "conservative_per_section_cap": 49000, "section_lengths": lengths,
        "body_word_count_regex": words, "required_seven_section_word_count_regex": required_words,
        "before_math_segments": len(before_math), "after_math_segments": len(after_math),
        "all_math_segments_exact_with_multiplicity": True, "global_inline_math_order_preserved": before_math == after_math,
        "within_relocated_block_math_order_preserved": True, "numbered_equations": len(re.findall(equation_pattern, before)),
        "all_numbered_equations_in_original_order": True, "complete_proofs_preserved_in_order": len(proofs),
        "tables_preserved_in_order": len(tables), "table_data_rows": sum(len(table.splitlines()) - 2 for table in tables),
        "full_figure_and_table_captions_preserved_in_order": len(captions(before)), "figures_preserved_in_order": len(images),
        "references_before": len(refs), "references_after": len(refs), "all_reference_records_unchanged": True,
        "all_scientific_paragraphs_exact_with_multiplicity": True, "all_quantitative_literals_preserved": True,
        "all_other_sections_byte_identical": True, "no_prose_truncation_or_math_whitespace_change": True,
        "all_preservation_and_character_assertions_passed": True}
    return reorganized, report


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
    assert len(numbering) >= 8, "AgentPub requires at least eight compiled references"
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


def full_set_control_evidence() -> tuple[str, dict | None, dict | None]:
    """Describe completed controls only from their final comparison/decoding pair."""
    report_path = CANONICAL / "results/gkeyll-control-comparison.json"
    decoding_path = CANONICAL / "results/gkeyll-control-decoding.json"
    incomplete = ("A complete four-case dynamical control is not established by this package's "
                  "validated final comparison and decoding receipts; preparation or partial outputs "
                  "must not be interpreted as completed controls.")
    if not report_path.is_file() or not decoding_path.is_file():
        return incomplete, None, None
    report = json.loads(report_path.read_text(encoding="utf-8"))
    decoding = json.loads(decoding_path.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in report["cases"]}
    assert len(cases) == len(report["cases"]), "Duplicate final control comparison IDs"
    wanted = [g + "_" + m for g in ("archived", "baseline", "matched")
              for m in ("one_fluid", "two_fluid")]
    if (report.get("all_actual_cases_passed") is not True
            or not all(cases.get(name, {}).get("status") == "compared" for name in wanted)
            or decoding.get("completed_case_count") != 4
            or decoding.get("any_case_failed_validation_or_execution") is not False):
        return incomplete, None, None
    assert set(cases) == set(wanted), "Final control summary must identify exactly the six declared cases"
    assert report["script_sha256"] == sha((CANONICAL / "experiments/analyze_gkeyll_controls.py").read_bytes()), "Final comparison pins a different analyzer"
    for key, relative in (("collector_sha256", "experiments/collect_completed_gkeyll_cases.py"),
                          ("reader_sha256", "experiments/read_gkeyll_bp.py"),
                          ("analysis_helper_sha256", "experiments/analyze_gkeyll_controls.py")):
        assert decoding[key] == sha((CANONICAL / relative).read_bytes()), "Decoded-case helper pin changed: " + key
    assert decoding["case_config_sha256"] == report["config_sha256"], "Final report and decoded-case config differ"
    config_path = CANONICAL / "data/gkeyll-completed-control-cases.json"
    assert sha(config_path.read_bytes()) == report["config_sha256"], "Final control config hash changed"
    csv_path = CANONICAL / "data/derived/gkeyll-control-comparison-profiles.csv"
    assert sha(csv_path.read_bytes()) == report["profile_export_sha256"], "Final control profiles changed"
    provenance = json.loads((CANONICAL / "data/provenance-gkeyll-control-comparison.json").read_text(encoding="utf-8"))
    assert provenance["result_sha256"] == sha(report_path.read_bytes()) and provenance["script_sha256"] == report["script_sha256"]
    assert provenance["config_sha256"] == report["config_sha256"] and provenance["profile_export_sha256"] == report["profile_export_sha256"]
    assert not report["failures"], "Final control comparison retains a failure"
    assert {p["id"] for p in report["paired_effects"] if p["status"] == "computed"} == {
        "one_fluid_initialization_effect", "two_fluid_initialization_effect"}, "Both paired effects are required"
    for pair in report["paired_effects"]:
        assert pair["status"] == "computed"
        model = "one_fluid" if pair["id"] == "one_fluid_initialization_effect" else "two_fluid"
        assert pair["baseline"] == "baseline_" + model and pair["matched"] == "matched_" + model
        assert pair["baseline_actual_time"] == cases[pair["baseline"]]["actual_time"]
        assert pair["matched_actual_time"] == cases[pair["matched"]]["actual_time"]
        assert pair["time_interpolation_performed"] is False
    assert {(p["clean"], p["archived"]) for p in report["clean_unmatched_vs_archived_source"]
            if p["status"] == "computed"} == {
        ("baseline_one_fluid", "archived_one_fluid"), ("baseline_two_fluid", "archived_two_fluid")}, "Both clean/archive baselines are required"
    contexts = []
    decoded = {c["analysis_case_id"]: c for c in decoding["cases"]}
    assert len(decoded) == len(decoding["cases"]) == 4, "Expected four distinct decoded controls"
    for name in wanted:
        case = cases[name]
        group, model = name.split("_", 1)
        assert case["kind"] == ("archived_source" if group == "archived" else "solver_control")
        assert case["role"] == ("source_reference" if group == "archived" else group)
        assert case["population_count"] == (1 if model == "one_fluid" else 2)
        assert case["frame"] == 30 and isinstance(case["actual_time"], (float, int)) and 300 <= case["actual_time"] < float("inf")
        if group != "archived":
            item = decoded[name]
            assert item["status"] == "completed_and_decoded"
            portable = item["receipt"]
            assert portable["status"] == "completed_native_stop" and portable["all_decoding_checks_passed"]
            assert portable["source_comparison_is_regular_frame30"] is True and portable["original_dirty_build_reproduced"] is False
            native = str(case["population_count"]) + "-fluid-" + ("unmatched" if group == "baseline" else "aggregate-matched")
            assert item["case"] == portable["case"] == native
            assert portable["frame"] == 30 and portable["actual_time"] == case["actual_time"]
            assert sha(json.dumps(portable, indent=2, allow_nan=False).encode() + b"\n") == item["portable_receipt_sha256"], "Portable completed receipt hash differs"
            assert portable["source_run_receipt_sha256"] == case["completed_case_receipt"]["source_run_receipt_sha256"]
            assert item["portable_receipt_sha256"] == case["completed_case_receipt"]["sha256"]
            assert portable["runtime_context"] == case["runtime_context"] == decoding["expected_runtime_context"]
            contexts.append(case["runtime_context"])
    assert all(context == contexts[0] for context in contexts), "Controls do not share one runtime context"
    text = ("Four aggregate-initialization controls completed with one tested clean Gkeyll source base and "
            "common runtime context. The final report contains all six archived/clean-baseline/matched "
            "comparisons, both initialization pairs and both clean-versus-archived checks. It retains "
            "actual regular-frame-30 times and complete-grid errors. This is a fixed-grid sensitivity "
            "experiment, not recovery of the original dirty executable, PIC-tag matching or a universal "
            "nonlinear effect bound.")
    return text, report, decoding


def verify_profiles(report: dict) -> None:
    """Recheck projected norms without presenting them as full-grid errors."""
    path = CANONICAL / "data/derived/gkeyll-control-comparison-profiles.csv"
    assert sha(path.read_bytes()) == report["profile_export_sha256"], "Final profile CSV hash differs"
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        headings = list(reader.fieldnames or [])
        rows = list(reader)
    assert len(rows) == 640 and len(headings) == len(set(headings)), "Expected 640 rows and unique profile columns"
    for index, row in enumerate(rows):
        assert math.isclose(float(row["raw_y"]), -32 + (index + .5) * .1, rel_tol=0, abs_tol=1e-12)
        assert all(math.isfinite(float(value)) for value in row.values()), "Nonfinite profile data"
    targets = {"rho": "PIC_rho", "Jz": "PIC_Jz", "Pxx": "PIC_Pxx", "Pzz": "PIC_Pzz",
               "qCSxxx_contribution": "PIC_qxxx_CONDITIONAL_raw_third",
               "qCSxxx_contribution_vs_tagged_PIC": "PIC_qCSxxx"}
    for case in report["cases"]:
        if case["status"] != "compared":
            assert "metrics" not in case, "Rejected/pending endpoint has primary metrics"
            assert not any(name.startswith(case["id"] + "_") for name in headings), "Rejected/pending endpoint has exported profile columns"
            continue
        for quantity, metrics in case["metrics"].items():
            assert quantity in targets, "Inspect new comparison quantity before adapting it: " + quantity
            model, target = case["id"] + "_" + quantity, targets[quantity]
            reference_norm_squared = math.fsum(float(row[target]) ** 2 for row in rows)
            measured = (math.sqrt(math.fsum((float(row[model]) - float(row[target])) ** 2 for row in rows)
                                  / reference_norm_squared) if reference_norm_squared else None)
            expected = metrics["x_averaged_profile"]["relative_L2"]
            assert (expected is None and measured is None) or (expected is not None and measured is not None
                and math.isclose(measured, expected, rel_tol=2e-11, abs_tol=2e-14)), "Profile norm differs: " + model
            grid_error = metrics["full_2D_grid"]["relative_L2"]
            assert grid_error is None or math.isfinite(grid_error) and grid_error >= 0, "Invalid full-grid error"


def control_evidence(scope: str, code_pin: dict, pinned_files: dict) -> tuple[str, dict, dict, dict]:
    """Explicit numerical-subset route; never promote it to the full-set gate."""
    helper_path = CANONICAL / "scripts/make_paper_data.py"
    assert pinned_files.get("scripts/make_paper_data.py") == sha(helper_path.read_bytes()), "Shared evidence validator is not source-pinned"
    spec = importlib.util.spec_from_file_location("heatflux_canonical_evidence_gate", helper_path)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)  # Functions only; never invokes generator main.
    state = helper.validate_numerical_subset_evidence(
        "results/gkeyll-control-comparison.json", ["results/gkeyll-control-decoding.json"],
        "results/gkeyll-admissibility.json", commit=None)
    bindings = state.pop("read_only_evidence_bindings")
    assert all(pinned_files.get(item["path"]) == item["sha256"] for item in bindings), "Numerical evidence is absent from the final source/input/output pin"
    assert state == code_pin["controls_state"], "Recomputed outcome/scan/endpoint state differs from the final code pin"
    assert state["physical_trajectory_validation_claimed"] is False and state["saved_histories_certify_between_output_states"] is False
    report = json.loads((CANONICAL / "results/gkeyll-control-comparison.json").read_text(encoding="utf-8"))
    decoding = json.loads((CANONICAL / "results/gkeyll-control-decoding.json").read_text(encoding="utf-8"))
    provenance = json.loads((CANONICAL / "data/provenance-gkeyll-control-comparison.json").read_text(encoding="utf-8"))
    assert provenance["result_sha256"] == sha((CANONICAL / "results/gkeyll-control-comparison.json").read_bytes())
    assert provenance["script_sha256"] == report["script_sha256"] and provenance["config_sha256"] == report["config_sha256"]
    assert provenance["profile_export_sha256"] == report["profile_export_sha256"]
    assert report.get("all_requested_enabled_endpoint_cases_passed") is True and not report["failures"], "An enabled endpoint comparison failed"
    cases = {case["id"]: case for case in report["cases"]}
    assert len(cases) == len(report["cases"]) and set(cases) == {*CONTROL_CASES, "archived_one_fluid", "archived_two_fluid"}
    rejected = state["endpoint_collector_rejected_case_ids"]
    assert sorted(report["rejected_native_completed_case_ids"]) == sorted(rejected), "Rejected native outcomes disappeared from comparison history"
    for name in rejected:
        case = cases[name]
        assert case["status"] == "rejected_state_conformance" and case["metrics_accepted"] is False and "metrics" not in case
        assert case["native_execution_status"] == "completed_native_stop" and case["native_execution_completed"] is True
        assert case["source_run_receipt_sha256"] == state["native_outcomes"][name]["source_run_receipt_sha256"]
    verify_profiles(report)
    if scope == "full-set":
        text, full_report, full_decoding = full_set_control_evidence()
        assert full_report is not None and state["all_four_completed_and_compared"] is True, "Full-set mode requires all six endpoint comparisons; select the explicit numerical-endpoint-subset mode for qualified partial results"
        assert state["all_four_saved_snapshot_scans_complete"] is True, "Full-set mode needs the separate four saved-history records"
        text += " Saved-state histories remain separately disclosed; positive-definite endpoints do not certify a physically admissible trajectory or physical causality."
        return text, full_report, full_decoding, state
    assert scope == "numerical-endpoint-subset"
    assert state["all_four_native_outcomes_observed"] is True and state["all_terminal_outcomes_and_required_histories_bound"] is True
    assert state["all_four_collector_decisions_resolved"] is True and state["all_four_saved_snapshot_diagnostics_resolved"] is True, "Final numerical subset retains an unresolved endpoint/history decision"
    assert state["numerical_endpoint_subset_evidence_bound"] is True and state["endpoint_admissible_numerical_pairs"], "No receipt-bound numerical endpoint pair is eligible"
    failed_native = []
    for identifier, outcome in state["native_outcomes"].items():
        assert outcome["native_outcome_terminal"] is True, "All four terminal native outcomes must be observed before packaging this final subset"
        history = state["saved_snapshot_histories"][identifier]
        if outcome["native_status"] == "completed_native_stop":
            assert history["status"] == "completed_regular0_through30"
        else:
            assert outcome["native_status"] in {"failed", "failed_controller_guard"}
            assert history["status"] == "not_applicable_native_execution_failed" and outcome["primary_metrics_accepted"] is False
            assert "actual_time" not in outcome and "portable_decoding_receipt_sha256" not in outcome, "Failed native case claims an endpoint receipt/time"
            case = cases[identifier]
            native_name = CONTROL_CASES[identifier][0]
            item = next(row for row in decoding["cases"] if row["case"] == native_name)
            assert item["status"] == case["status"] == "failed_native_execution" and "metrics" not in case
            assert case["native_outcome_terminal"] is True and case["native_execution_successful"] is False
            assert case["native_execution_status"] == outcome["native_status"] and case["native_returncode"] == outcome["native_returncode"] != 0
            assert case["source_run_receipt_sha256"] == item["source_run_receipt_sha256"] == outcome["source_run_receipt_sha256"]
            failure = item["failure_receipt"]
            digest = sha((json.dumps(failure, indent=2, allow_nan=False) + "\n").encode())
            assert digest == item["failure_receipt_sha256"] == case["failure_receipt"]["sha256"]
            assert failure["source_run_receipt_sha256"] == outcome["source_run_receipt_sha256"] and failure["runtime_context"] == state["admissibility_native_runtime_context"]
            assert failure["native_stop_requested"] is False and failure["regular30_endpoint_accepted"] is False and failure["regular30_frame_files_present"] is False and failure["metrics_accepted"] is False
            assert failure["last_closed_regular_frame"] == case["last_closed_regular_frame"] and failure["last_closed_regular_time"] == case["last_closed_regular_time"]
            assert "actual_time" not in case and "frame" not in case, "Failed native case acquired a comparison endpoint"
            failed_native.append(identifier)
        if outcome["primary_metrics_accepted"]:
            case = cases[identifier]
            native_name, role, populations = CONTROL_CASES[identifier]
            assert case["status"] == "compared" and case["kind"] == "solver_control" and case["role"] == role and case["population_count"] == populations
            assert "NUMERICAL" in case["comparison_scope"] and outcome["native_case"] == native_name
    histories = state["saved_snapshot_histories"]
    failed_histories = sorted(name for name, history in histories.items() if history.get("all_scanned_populations_PSD") is False)
    pairs = ", ".join(sorted(state["endpoint_admissible_numerical_pairs"]))
    text = ("This edition reports endpoint-admissible NUMERICAL contrasts for " + pairs + ". "
            "All four terminal native outcomes are retained. Complete regular0-through30 saved histories are bound for every successful native completion. "
            + ("Native execution failures (" + ", ".join(sorted(failed_native)) + ") supply no comparison endpoint, primary metrics or complete saved-history claim. " if failed_native else "")
            + ("Endpoint-rejected cases (" + ", ".join(sorted(rejected)) + ") have no accepted primary comparison metrics. " if rejected else "")
            + ("Non-PSD saved histories (" + ", ".join(failed_histories) + ") remain attached to these results. " if failed_histories else "")
            + "Native completion and positive-definite initial/final states do not establish physically admissible trajectories, physical causality or convergence. "
            "No rejected state is clipped, assigned a zero error or silently omitted from the outcome narrative.")
    return text, report, decoding, state


def public_reproduction_paths(pinned_paths: set[str] | None = None) -> list[Path]:
    """Allowlist portable scientific material, never caches or submission/access files."""
    folders = ("experiments", "scripts", "figures", "source-excerpts", "data/derived", "data/input-decks")
    paths = [p for folder in folders for p in (CANONICAL / folder).rglob("*") if p.is_file()]
    paths += [p for folder in ("data", "results") for p in (CANONICAL / folder).iterdir()
              if p.is_file() and p.suffix.lower() in {".json", ".md", ".log", ".csv", ".tex"}]
    paths += [p for p in (CANONICAL / "results/gkeyll-saved-state-scans").glob("*.json") if p.is_file()]
    # Nested selected records are eligible only when actually bound by the final
    # source/input/grouped output pin. Do not publish unselected interim packets.
    paths += [p for p in (CANONICAL / "results/gkeyll-admissibility-inputs").rglob("*.json")
              if p.is_file() and pinned_paths is not None
              and p.relative_to(CANONICAL).as_posix() in pinned_paths]
    paths += [CANONICAL / p for p in ("requirements.txt", "requirements-bp.txt", "SOURCE.md",
              "LICENSE-CODE", "LICENSE-MANUSCRIPT", "audit/ledger.md", "audit/prior-art.md")]
    # Author-assembled provenance annotations are public release metadata,
    # separate from the numerical readiness gate and its code-pin inputs.
    paths += [CANONICAL / p for p in PUBLIC_AUTHOR_METADATA if (CANONICAL / p).is_file()]
    allowed = {".py", ".lua", ".md", ".txt", ".csv", ".json", ".png", ".pdf", ".tex", ".bib", ".log"}
    selected = []
    for path in sorted(set(paths)):
        relative = path.relative_to(CANONICAL)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        assert path.resolve().is_relative_to(CANONICAL.resolve()), "Reproduction file escapes canonical tree"
        assert not {"raw", ".git", ".publishing-access", "submissions"}.intersection(relative.parts)
        if relative.parts[:2] == ("results", "gkeyll-admissibility-inputs"):
            content = path.read_text(encoding="utf-8-sig")
            assert not re.search(r"\b[A-Za-z]:[\\/]", content) and not any(token in content for token in ("/mnt/", "/root/")), "Selected admissibility evidence contains a private absolute path"
        assert (path.suffix.lower() in allowed or path.name.startswith("LICENSE-")
                or relative.as_posix() == "data/input-decks/input_PIC.2d"), "Unallowlisted reproduction file: " + str(relative)
        if path.suffix.lower() == ".pdf":
            assert relative.parts[0] == "figures", "Only analysis figure PDFs may be copied"
        if relative.parts[0] == "audit":
            assert relative.as_posix() in {"audit/ledger.md", "audit/prior-art.md"}
        selected.append(path)
    return selected


def main() -> None:
    if sys.flags.optimize:
        raise RuntimeError("Run without Python -O: preservation assertions must remain enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-version", required=True, help="Actual final canonical version, for example 1.2.0")
    parser.add_argument("--expected-code-commit", required=True, help="Actual final 40-hex code pin; never a guessed future commit")
    parser.add_argument("--controls-scope", choices=("full-set", "numerical-endpoint-subset"), default="full-set",
                        help="Strict full endpoint set by default; explicitly select numerical subset with rejected outcomes and saved-history evidence retained")
    parser.add_argument("--agentpub-only", action="store_true",
                        help="Update only AgentPub payload and its adapter checks; preserve full manuscript, AAES files, context and copied science bytes")
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
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.canonical_version):
        parser.error("--canonical-version must be an explicit x.y.z version")
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_code_commit):
        parser.error("--expected-code-commit must be the actual final lowercase 40-hex commit")
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
    assert version == args.canonical_version, ("Regenerate the requested final canonical conversion first", version)
    source_path = CANONICAL / "submissions/manuscript.md"
    source = source_path.read_text(encoding="utf-8")
    sections = markdown_sections(source)
    headings = {title_only(h): h for h in sections}
    expected = ["Introduction and scope", "Initial-state matching in the supplied input decks",
                "Matched-initial-state fluid comparisons",
                "An auxiliary homogeneous linear-stability test", "A secondary continuity clarification",
                "Conditioning a relative heat-flux accuracy claim", "Finite isotropization over a comparison interval",
                "Reproducible calculations and evidence limits", "Consequences for controlled validation", "Conclusion"]
    assert all(h in headings for h in expected), sorted(set(expected) - set(headings))
    assert [title_only(h) for h in sections if title_only(h) in expected] == expected, "Canonical scientific section order differs"
    intro = sections[headings[expected[0]]]
    related_match = re.search(r"^## (?:\d+(?:\.\d+)*\.?\s+)?Relation to established work\s*$", intro, re.M)
    audited_match = re.search(r"^## (?:\d+(?:\.\d+)*\.?\s+)?Audited version and available evidence\s*$", intro, re.M)
    assert related_match and audited_match and related_match.start() < audited_match.start(), "Inspect converted Introduction subsection headings"
    intro_body = intro[:related_match.start()].strip()
    related = intro[related_match.end():audited_match.start()].strip()
    audited = intro[audited_match.end():].strip()
    refs, ref_ids = references()
    release = CANONICAL_REPOSITORY + "/releases/tag/v" + version
    verification = json.loads((CANONICAL / "results/verification.json").read_text(encoding="utf-8"))
    assert verification["all_assertions_passed"] is True and len(verification["groups"]) == 8
    environment = verification["environment"]
    for pin in environment["source_files"]:
        assert sha((CANONICAL / pin["path"]).read_bytes()) == pin["sha256"], "Verification result has a stale code pin: " + pin["path"]
    code_pin = json.loads((CANONICAL / "results/code-pin.json").read_text(encoding="utf-8"))
    assert code_pin["commit"] == args.expected_code_commit, "The final code pin differs from the explicitly requested commit"
    pinned_files = {}
    for pin in code_pin["source_files"] + code_pin["revision_outputs"] + code_pin.get("input_files", []):
        assert sha((CANONICAL / pin["path"]).read_bytes()) == pin["sha256"], "Revision code/output pin changed: " + pin["path"]
        assert pin["path"] not in pinned_files or pinned_files[pin["path"]] == pin["sha256"], "Conflicting final file pins"
        pinned_files[pin["path"]] = pin["sha256"]
    pinned_output_paths = set()
    if "output_manifest" in code_pin:
        manifest_pin = code_pin["output_manifest"]
        manifest_path = CANONICAL / manifest_pin["path"]
        assert sha(manifest_path.read_bytes()) == manifest_pin["sha256"], "Grouped output inventory changed"
        pinned_files[manifest_pin["path"]] = manifest_pin["sha256"]
        output_inventory = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert output_inventory["commit"] == args.expected_code_commit
        for entries in output_inventory["groups"].values():
            for pin in entries:
                assert sha((CANONICAL / pin["path"]).read_bytes()) == pin["sha256"], "Grouped evidence pin changed: " + pin["path"]
                pinned_output_paths.add(pin["path"])
                assert pin["path"] not in pinned_files or pinned_files[pin["path"]] == pin["sha256"], "Conflicting grouped file pins"
                pinned_files[pin["path"]] = pin["sha256"]
    integrity = json.loads((CANONICAL / "data/full-archive-verification.json").read_text(encoding="utf-8"))
    assert integrity["all_three_archives_and_18_selected_inputs_verified"] is True
    assert len(integrity["archives"]) == 3
    assert all(a["size_and_publisher_MD5_match"] is True and a["full_archive_checksum_verified"] is True
               and a["computed_md5"] == a["publisher_md5"] for a in integrity["archives"])
    controls_text, controls_report, controls_decoding, controls_state = control_evidence(
        args.controls_scope, code_pin, pinned_files)
    assert {"results/gkeyll-control-comparison.json", "results/gkeyll-control-decoding.json",
            "results/gkeyll-admissibility.json", "data/gkeyll-completed-control-cases.json",
            "data/provenance-gkeyll-control-comparison.json",
            "data/derived/gkeyll-control-comparison-profiles.csv"} <= pinned_output_paths, "The singular control/outcome/scan report is absent from the final grouped pin"
    public_sources = public_reproduction_paths(set(pinned_files))
    public_paths = {p.relative_to(CANONICAL).as_posix() for p in public_sources}
    assert set(pinned_files) <= public_paths, "A pinned source/input/grouped output is outside the public-copy allowlist: " + str(sorted(set(pinned_files) - public_paths))
    methods = (
        "This is a source-specific initial-state audit and reproducible continuum-closure study of arXiv:2607.07106v1. "
        "The original PDF was matched byte-for-byte with the versioned public PDF, and targeted claims were checked against rendered pages and the exact TeX archive. "
        "The authors' published decks and explicit data dictionary define the PIC ordinary-velocity moments. Five archived t=0 Gkeyll BP snapshots were reloaded through official ADIOS2 and checked against their byte-identical embedded Lua inputs. All fluid components are compared over the full grid, and complete 640-row x-averaged profiles corroborate the initial-state mismatch. "
        "Complete ZIP central-directory inventories identify no native deposited-current diagnostic in the posted PIC archive. The final provenance additionally verifies the full byte count and publisher MD5 of all three complete simulation ZIPs, computes their full SHA-256s and binds the original selected inputs to those archives. "
        "The original eight-group verification suite is retained unchanged. Separate programs reload archived fluid output, evaluate profile sensitivity, compute a conditional finite-temperature public-loader consistency check and analyze actual archived or completed control outputs. The loader and quadratic-shape calculations are unfitted conditional tests, not certification of the original executable or custom diagnostic kernel. No new PIC simulation or current-sheet eigenanalysis is claimed. "
        + controls_text + " "
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
        + ("The closed-or-released sequencing condition has been explicitly verified for this study's Publish.fun record. " if gate else "The agent-venue review-sequence gate remains false until this study's Publish.fun review is verified closed or released. ")
        + "Preparing local files does not establish a submission, review, acceptance, release or successful repository publication. Actual outcomes belong in the publication-status record."
    )
    results_titles = expected[1:-2]
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
        {"heading": "Limitations", "content": "The source scope is arXiv:2607.07106v1 and its checked deposit. Clean-source tests do not recover the original dirty 9663ea594e80+ executable. " + controls_text + " The aggregate-matching intervention retains the original smooth fluid population weights, not the actual PIC tags, and imports the full finite-particle spatial variation while replacing the conserved moment vector through second order. It does not isolate a current-only correction, match intrinsic third moments or provide an ensemble or grid-convergence result. Actual output times are retained without interpolation. The PIC current is a physical ordinary-velocity moment; no native deposited-current file is identifiable in the complete posted inventory. Tagged qCS is a decomposition-dependent population-recentering contribution, not unique full fluid heat flux. Any total PIC central-qxxx comparison remains conditional on unverified raw-third diagnostic normalization. The finite-temperature loader and quadratic-shape model are conditional consistency checks, not identification of the original executable or diagnostic kernel. Full-archive verification supplements the preserved historical selected-member receipts. No original author was contacted or private executable accessed. The auxiliary homogeneous nonrelativistic electrostatic example is not a sheet eigenanalysis, does not establish electromagnetic or relativistic sheet stability, and does not refute the source's application-specific instability claim. The secondary continuity clarification and conditioned error bound do not disprove the source's empirical scan or valid mixture identities. Prior-art inspection is not exhaustive. Full Penrose article text was unavailable; its primary deposited abstract and metadata were checked and the retained calculation is explicit. Exact model identifier and token usage were not recorded; no independent human expert review is claimed.", "citations": [ref_ids[k] for k in ("original", "dataset", "penrose1960", "osirisloader")]},
        {"heading": "Conclusion", "content": sections[headings["Conclusion"]] + "\n\n### Dissemination and author credit\n\n" + dissemination, "citations": [ref_ids["original"]]},
        {"heading": "Appendix", "content": "\n\n".join(nested(sections[h], h) for h in appendices), "citations": [ref_ids[k] for k in ("original", "dataset", "osirisudist")]},
    ]
    body = "\n\n".join(s["content"] for s in body_sections)
    abstract = sections["Abstract"]
    assert math_segments(source) == math_segments(abstract + "\n\n" + body), "Canonical equation content/order changed or dropped"
    code_pattern = r"(?ms)^```[^\n]*\n.*?^```\s*$"
    code_source = re.findall(code_pattern, source)
    code_agent = re.findall(code_pattern, body)
    assert code_source == code_agent, "A code fence or its contents changed"
    table_pattern = r"(?m)^\|.*(?:\n\|.*)+"
    tables_source = re.findall(table_pattern, source)
    tables_agent = re.findall(table_pattern, body)
    assert tables_source == tables_agent, "A canonical table changed"
    table_rows = sum(len(t.splitlines()) - 2 for t in tables_source)
    equation_tags = re.findall(r"\\tag\{(\d+)\}", source)
    assert equation_tags == re.findall(r"\\tag\{(\d+)\}", body), "Numbered equation tags changed"
    assert equation_tags == [str(i) for i in range(1, len(equation_tags) + 1)], "Canonical numbered equations are not consecutive"
    proof_pattern = r"(?m)^\*\*Proof\.\*\*.*$|^#{2,6} Proof\s*$|^\\begin\{proof\}.*$"
    source_proofs = re.findall(proof_pattern, source)
    agent_proofs = re.findall(proof_pattern, body)
    assert source_proofs == agent_proofs, "Proof marker changed or lost"
    body_words = count_words(body)
    assert 4000 <= body_words <= 15000, body_words
    assert len(meta["title"]) <= 200 and count_words(abstract) <= 500
    agentpub_sections, agentpub_reorganization = agentpub_section_reorganization(body_sections, abstract, refs)
    payload = {"title": meta["title"], "paper_type": "research_article", "abstract": abstract,
               "authors": [{"agent_id": AGENT_ID, "display_name": "Lattice Audit Agent", "model_type": "OpenAI Codex"}],
               "tags": ["plasma-physics", "magnetic-reconnection", "heat-flux-closure", "linear-stability", "reproducibility"],
               "sections": agentpub_sections, "references": refs,
               "metadata": {"agent_model": "OpenAI Codex; exact underlying model identifier not recorded", "agent_platform": "Codex desktop", "total_tokens": -1,
                            "submission_note": "Taylor Kalin is canonical author and human operator. Lattice Audit Agent is the authorized venue-specific agent author. This is one study. All canonical equations, proofs, data methods and references are retained. Token usage is unknown; -1 is an explicit missing-data sentinel, not measured usage. Prepared review state: " + args.publishfun_state + ". AgentPub-only formatting moves canonical Section 3.1 intact into Methodology; full manuscript and AAES edition keep their original order. Full manuscript: " + AGENT_REPOSITORY + "/blob/main/paper.md.",
                            "generation_params": {"token_usage_status": "not_recorded", "total_tokens_sentinel": -1, "token_usage_is_measurement": False, "exact_model_identifier_status": "not_recorded", "agentpub_section_reorganization": "Canonical Section 3.1 moved intact from Results to Methodology; no scientific prose shortened"}}}
    serialized = json.dumps(payload, ensure_ascii=False)
    assert not re.search(r"teylersf@gmail\.com|509[- ]?919[- ]?0487|mailto:|tel:", serialized)
    assert all(s["heading"] == h for s, h in zip(body_sections, REQUIRED_SECTIONS + ["Appendix"]))
    if args.agentpub_only:
        existing = json.loads((ROOT / "reproduction/adapter-checks.json").read_text(encoding="utf-8"))
        context = json.loads((ROOT / "reproduction/publication-context.json").read_text(encoding="utf-8"))
        assert existing["canonical_code_commit"] == args.expected_code_commit and existing["canonical_manuscript_sha256"] == sha(source_path.read_bytes())
        for key, expected_value in {"canonical_work_version": version, "publishfun_internal_id": args.publishfun_id,
                "publishfun_state": args.publishfun_state, "publishfun_public_id": args.publishfun_public_id,
                "publishfun_actual_stage": args.publishfun_stage, "publishfun_round": args.publishfun_round,
                "publishfun_review_closed_verified": args.publishfun_review_closed_verified,
                "airaxiv_public_id": args.airaxiv_public_id, "airaxiv_public_version": args.airaxiv_public_version,
                "airaxiv_submission_id": args.airaxiv_submission_id,
                "airaxiv_current_canonical_version_verified": args.airaxiv_current_canonical_version_verified,
                "agent_venue_submission_allowed_by_review_sequence": gate}.items():
            assert context.get(key) == expected_value, "AgentPub-only mode requires the existing verified package context: " + key
        frozen = {relative: sha((ROOT / relative).read_bytes()) for relative in
                  ("paper.md", "metadata.json", "aaes-registration.json", "reproduction/publication-context.json")}
        assert frozen["paper.md"] == existing["agent_paper_sha256"]
        for item in existing["copied_verbatim"]:
            assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"] == sha((CANONICAL / item["path"]).read_bytes())
            frozen[item["path"]] = item["sha256"]
        write_json(ROOT / "agentpub-payload.json", payload)
        assert all(sha((ROOT / relative).read_bytes()) == digest for relative, digest in frozen.items()), "AgentPub-only update changed a frozen full-edition/scientific file"
        agentpub_reorganization["frozen_full_edition_files_sha256"] = {key: frozen[key] for key in ("paper.md", "metadata.json", "aaes-registration.json", "reproduction/publication-context.json")}
        agentpub_reorganization["copied_science_files_unchanged"] = len(existing["copied_verbatim"])
        agentpub_reorganization["payload_sha256"] = sha((ROOT / "agentpub-payload.json").read_bytes())
        existing["agentpub_section_reorganization"] = agentpub_reorganization
        write_json(ROOT / "reproduction/adapter-checks.json", existing)
        print(json.dumps({"agentpub_only": True, "all_preservation_assertions_passed": True,
                          "Results_characters": len(next(section["content"] for section in agentpub_sections if section["heading"] == "Results")),
                          "maximum_section_characters": max(row["unicode_codepoints"] for row in agentpub_reorganization["section_lengths"]),
                          "payload_sha256": agentpub_reorganization["payload_sha256"]}))
        return
    write_json(ROOT / "agentpub-payload.json", payload)
    displayed_date = datetime.fromisoformat(meta["date"]).strftime("%d %B %Y").lstrip("0")
    header = "# " + meta["title"] + "\n\n**Agent author: Lattice Audit Agent**\n\n**Human operator and canonical author: Taylor Kalin**\n\n[Operator ORCID: 0009-0003-9000-9315](https://orcid.org/0009-0003-9000-9315)\n\n" + displayed_date + " · Version " + version + "\n\n## Abstract\n\n" + abstract + "\n\n"
    paper = header + "\n\n".join("## " + s["heading"] + "\n\n" + s["content"] for s in body_sections)
    paper += "\n\n## References\n\n" + sections["References"] + "\n"
    assert math_segments(source) == math_segments(paper)
    (ROOT / "paper.md").write_text(paper, encoding="utf-8", newline="\n")
    now = datetime.now(timezone.utc).isoformat()
    metadata = {"aaes_version": "4.2", "title": meta["title"], "abstract": abstract,
                "author_ids": [GIST_ID], "submitted_at": now, "tags": payload["tags"],
                "generation_environment": {"model": payload["metadata"]["agent_model"],
                    "tools": ["Python " + environment["python"].split()[0], "NumPy " + environment["numpy"], "h5py " + environment["h5py"], "ADIOS2 2.13.0.1001 (isolated Linux BP reader)", "Matplotlib", "LaTeX", "Tectonic", "Pandoc"],
                    "prompt_strategy": "Source-specific archived PIC and BP-fluid audit, conditional public-loader consistency checks, receipt-bound aggregate-initialization comparisons and auxiliary continuum calculations",
                    "notes": "Human operator and canonical author: Taylor Kalin. Agent-only edition authorized. Self-funded with no external funding or reported competing interests. Exact model identifier and token usage not recorded. submitted_at is local package preparation, not proof of Registry registration. Review state: " + args.publishfun_state + "."},
                "novelty_statement": "Source-specific archived PIC-versus-reloaded-fluid initial-moment controls for arXiv:2607.07106v1, with complete profile diagnostics and an unfitted conditional public-loader consistency check. " + controls_text + " The auxiliary homogeneous stability example is a calibration, not a current-sheet result or refutation of the source's application-specific instability claim. Valid mixture identities, known closure-dependent spectra, the Penrose criterion and continuity are established ingredients."}
    write_json(ROOT / "metadata.json", metadata)
    claims = [
        {"text": "The archived initial PIC and fluid velocity moments differ: the full x-averaged moment-current profile has a relative L2 difference of 9.87 percent, and the two lower-sheet central cells differ by about 11.6 percent. Reloaded fluid output corroborates the posted initializers to roundoff.", "kind": "finding", "status": "proposed", "evidence_summary": "Five CRC32/SHA-256 checked t=0 BP snapshots, embedded inputs byte-identical to the posted Lua decks, all 480x640 fluid cells checked, and full 640-row PIC/fluid profile comparisons; full source ZIP byte counts/MD5/SHA-256 verified separately.", "confidence_note": "Physical moment current and velocity-covariance pressure; no native deposited-current file is identifiable. Initial mismatch percentages alone do not give a nonlinear effect or reconnection-rate bound."},
        {"text": "The inspected public unweighted thermal-momentum loading rule predicts a mean drift below its cold proper-velocity conversion. An unfitted quadratic-shape model provides a conditional consistency check against selected archived lower-sheet moments.", "kind": "finding", "status": "proposed", "evidence_summary": "Complete posted PIC deck audit, pinned public loader/deposition source, converged Gaussian quadrature and independent Cartesian moment checks; conditional pointwise and shape calculations remain separate.", "confidence_note": "Conditional on the public loading rule and stated sampling assumptions; the original executable and custom velocity-diagnostic kernel are not identified or certified."},
        {"text": "A specified homogeneous two-Maxwellian equilibrium stable to collisionless longitudinal electrostatic perturbations has an overstable mode in the stated finite-isotropization fluid closure.", "kind": "finding", "status": "proposed", "evidence_summary": "Explicit rational Penrose bound, linear system, eigenvalue residual, dielectric residual and Gauss-constraint checks.", "confidence_note": "Separate nonrelativistic continuum benchmark; no claim that this mode occurred in the source reconnection simulation or of general electromagnetic stability."},
    ]
    if controls_report is not None:
        clean_cases = [c for c in controls_report["cases"]
                       if c.get("kind") == "solver_control" and c["status"] == "compared"]
        measurements = [{"id": c["id"], "actual_time": c["actual_time"],
                         "full_grid_relative_L2": {q: c["metrics"][q]["full_2D_grid"]["relative_L2"]
                                                    for q in ("rho", "Jz", "Pxx", "Pzz")}}
                        for c in clean_cases]
        claims.append({"text": controls_text, "kind": "finding", "status": "proposed",
                       "evidence_summary": "Accepted numerical regular-frame30 comparisons only: " + json.dumps(measurements, allow_nan=False),
                       "confidence_note": "One grid and one sampled aggregate target; actual times are retained. All four native outcomes, rejected endpoint decisions and saved-history failures remain explicit; no rejected endpoint has a primary metric. Endpoint PD does not validate the saved or continuous physical trajectory. Smooth fluid labels are retained, not PIC tags. Tagged qCS is only a population-recentering contribution; central-qxxx comparisons require an unverified raw-third normalization. Only eligible endpoint pairs and eligible clean-versus-archived differences are compared."})
    registration = {"source": "github:Teylersf/counterstreaming-heatflux-agent-publication", "submission": {"kind": "paper", "maturity": "final"},
                    "project": {"title": meta["title"], "summary": "Archived PIC/fluid initial-state audit, conditional loader consistency checks, receipt-bound aggregate-matching comparisons and an auxiliary continuum calibration for arXiv:2607.07106v1.", "research_question": "How do the archived physical moments differ, how sensitive are the tested fluid results to aggregate-moment matching, and which implementation, label, time and third-moment limitations remain?", "status": "active"}, "claims": claims}
    write_json(ROOT / "aaes-registration.json", registration)
    copied = []
    for src in public_sources:
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
    copied_pins = {entry["path"]: entry["sha256"] for entry in copied}
    assert all(copied_pins.get(path) == digest for path, digest in pinned_files.items()), "A pinned scientific source/input/grouped output was not copied byte-for-byte"
    author_metadata_pins = {relative: sha((CANONICAL / relative).read_bytes()) for relative in PUBLIC_AUTHOR_METADATA}
    assert all(copied_pins.get(path) == digest for path, digest in author_metadata_pins.items()), "Public author provenance annotation was not copied byte-for-byte"
    figure_manifest = json.loads((CANONICAL / "results/figure-manifest.json").read_text(encoding="utf-8"))
    for figure in figure_manifest["figures"]:
        assert sha((ROOT / figure["path"]).read_bytes()) == figure["sha256"]
    figure_urls = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", source)
    assert figure_urls, "Canonical manuscript has no scientific figures"
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
              "numbered_equations": len(equation_tags), "all_numbered_equation_tags_preserved": True,
              "code_block_count": len(code_source), "all_code_blocks_identical": True,
              "table_count": len(tables_source), "table_data_rows": table_rows, "all_tables_identical": True,
              "body_word_count_regex": body_words, "body_word_count_whitespace": len(body.split()), "reference_count": len(refs),
              "reference_numbering_matches_compiled_aux": True, "undated_osiris_publication_year_omitted": True,
              "canonical_verification_group_count": len(verification["groups"]), "canonical_verification_groups": list(verification["groups"]),
              "canonical_figure_manifest": figure_manifest, "section_order": [s["heading"] for s in body_sections],
              "canonical_code_commit": code_pin["commit"], "canonical_figure_count": len(figure_urls), "canonical_figure_files": figure_files,
              "scientific_source_files_included": [p["path"] for p in code_pin["source_files"]],
              "completed_control_comparison_verified": controls_state["all_four_completed_and_compared"],
              "controls_scope": args.controls_scope,
              "numerical_endpoint_subset_evidence_bound": controls_state["numerical_endpoint_subset_evidence_bound"],
              "canonical_controls_state": controls_state,
              "public_author_metadata_sha256": author_metadata_pins,
              "all_four_successful_native_outcomes_and_full_saved_histories": controls_state["all_four_native_outcomes_completed"] and controls_state["all_four_saved_snapshot_scans_complete"],
              "all_terminal_outcomes_and_required_histories_bound": controls_state["all_terminal_outcomes_and_required_histories_bound"],
              "physical_trajectory_validation_claimed": False,
              "control_evidence_scope": controls_text,
              "whole_archive_receipt_sha256": sha((CANONICAL / "data/full-archive-verification.json").read_bytes()),
              "only_public_audit_ledger_and_prior_art_copied": True,
              "canonical_result_sections_preserved": [headings[h] for h in results_titles], "copied_verbatim": copied,
              "agentpub_section_reorganization": agentpub_reorganization,
              "no_owner_email_or_phone_in_agent_payload": True, "human_operator_is_not_agent_schema_coauthor": True,
              "token_usage_sentinel_is_not_measurement": True, "no_raw_data_or_original_or_canonical_paper_pdf_copied": not (ROOT / "data/raw").exists() and not (ROOT / "paper").exists(),
              "canonical_release_target": release, "publication_context": context, "all_adapter_assertions_passed": True}
    write_json(ROOT / "reproduction/adapter-checks.json", checks)
    print(json.dumps({k: checks[k] for k in ("body_word_count_regex", "reference_count", "canonical_math_segments", "canonical_proof_markers", "all_adapter_assertions_passed")}))


if __name__ == "__main__":
    main()
