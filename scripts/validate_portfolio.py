#!/usr/bin/env python3
"""Fail-closed, dependency-light validation for a public portfolio repository."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__"}
FORBIDDEN_ARTIFACTS = {".abf", ".bim", ".pbix", ".pbit"}
TEXT_EXTENSIONS = {
    "", ".dax", ".json", ".md", ".py", ".sql", ".tour", ".txt", ".yaml", ".yml"
}
SENSITIVE_PATTERNS = {
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "GUID": re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
        re.I,
    ),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "Fabric endpoint": re.compile(r"\b(?:datawarehouse\.fabric\.microsoft\.com|database\.windows\.net)\b", re.I),
    "Power BI workspace link": re.compile(r"app\.powerbi\.com/groups/", re.I),
    "local machine path": re.compile(r"\b(?:[A-Z]:\\Users\\|D:\\AI Agent\\)", re.I),
    "employer brand": re.compile(r"\bashley(?: furniture)?\b", re.I),
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def repository_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in IGNORED_DIRECTORIES for part in path.relative_to(ROOT).parts)
    )


def local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    if not target or target.startswith("#"):
        return None
    if re.match(r"^(?:https?|mailto|tel|data):", target, re.I):
        return None
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def validate_machine_contracts() -> list[str]:
    errors: list[str] = []
    model_path = ROOT / "model" / "model-summary.yaml"
    if model_path.is_file():
        model = yaml.safe_load(model_path.read_text(encoding="utf-8"))
        if not isinstance(model, dict):
            return ["model/model-summary.yaml: root must be a mapping"]
        if not re.fullmatch(r"\d+\.\d+", str(model.get("schema_version", ""))):
            errors.append("model/model-summary.yaml: schema_version must be a quoted major.minor value")
        observed_as_of = model.get("observed_as_of")
        try:
            if not isinstance(observed_as_of, str):
                raise ValueError
            date.fromisoformat(observed_as_of)
        except ValueError:
            errors.append("model/model-summary.yaml: observed_as_of must be a quoted ISO date")
        counts = model.get("counts", {})
        for field in ("tables", "relationships", "forecast_measures", "inventory_measures"):
            value = counts.get(field) if isinstance(counts, dict) else None
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"model/model-summary.yaml: counts.{field} must be a positive integer")
        security = model.get("security", {})
        if not isinstance(security, dict) or any(value is not False for value in security.values()):
            errors.append("model/model-summary.yaml: every published security safety flag must be false")
        guardrails = model.get("release_guardrails", [])
        if not isinstance(guardrails, list) or len(set(guardrails)) < 5:
            errors.append("model/model-summary.yaml: at least five unique release_guardrails are required")

    report_path = ROOT / "report" / "page-inventory.yaml"
    if report_path.is_file():
        report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            return errors + ["report/page-inventory.yaml: root must be a mapping"]
        if not re.fullmatch(r"\d+\.\d+", str(report.get("schema_version", ""))):
            errors.append("report/page-inventory.yaml: schema_version must be a quoted major.minor value")
        evidence = report.get("evidence", {})
        observed_as_of = evidence.get("observed_as_of") if isinstance(evidence, dict) else None
        try:
            if not isinstance(observed_as_of, str):
                raise ValueError
            date.fromisoformat(observed_as_of)
        except ValueError:
            errors.append("report/page-inventory.yaml: evidence.observed_as_of must be a quoted ISO date")
        snapshot = report.get("verified_snapshot", {})
        pages = snapshot.get("pages") if isinstance(snapshot, dict) else None
        primary_pages = snapshot.get("primary_pages", []) if isinstance(snapshot, dict) else []
        if not isinstance(pages, int) or isinstance(pages, bool) or pages < len(primary_pages) or pages <= 0:
            errors.append("report/page-inventory.yaml: page count must cover every primary page")
        decisions = report.get("decision_contracts", {})
        if not isinstance(decisions, dict) or not set(primary_pages).issubset(decisions):
            errors.append("report/page-inventory.yaml: every primary page requires a decision contract")
        else:
            required_fields = {"audience", "decision", "action_owner_role", "guardrail"}
            for page in primary_pages:
                if not required_fields.issubset(decisions.get(page, {})):
                    errors.append(f"report/page-inventory.yaml: incomplete decision contract for {page}")
        security = report.get("security", {})
        if not isinstance(security, dict) or any(value is not False for value in security.values()):
            errors.append("report/page-inventory.yaml: every published security safety flag must be false")
        guardrails = report.get("release_guardrails", [])
        if not isinstance(guardrails, list) or len(set(guardrails)) < 5:
            errors.append("report/page-inventory.yaml: at least five unique release_guardrails are required")
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    files = repository_files()
    for required in ("README.md", "SECURITY.md"):
        if not (ROOT / required).is_file():
            errors.append(f"missing required file: {required}")
    errors.extend(validate_machine_contracts())
    for path in files:
        relative = path.relative_to(ROOT)
        if path.suffix.lower() in FORBIDDEN_ARTIFACTS:
            errors.append(f"forbidden BI artifact: {relative}")
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"not valid UTF-8: {relative}")
            continue
        if relative.as_posix() != "scripts/validate_portfolio.py":
            for label, pattern in SENSITIVE_PATTERNS.items():
                if pattern.search(content):
                    errors.append(f"possible {label}: {relative}")
        if path.suffix.lower() in {".json", ".tour"}:
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON: {relative}:{exc.lineno}:{exc.colno}")
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as exc:
                errors.append(f"invalid YAML: {relative}: {exc}")
        if path.suffix.lower() == ".md":
            if content.count("```") % 2:
                errors.append(f"unbalanced fenced code block: {relative}")
            for match in MARKDOWN_LINK.finditer(content):
                target = local_link_target(match.group(1))
                if target is None:
                    continue
                resolved = (ROOT / target.lstrip("/")) if target.startswith("/") else (path.parent / target)
                if not resolved.resolve().exists():
                    errors.append(f"broken local link in {relative}: {target}")
    return sorted(set(errors))


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("Portfolio validation failed:")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("Portfolio validation passed: structure, links, syntax, and public-release checks are clean.")
