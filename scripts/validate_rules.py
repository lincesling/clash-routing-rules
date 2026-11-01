#!/usr/bin/env python3
"""Validate the Subconverter/Clash custom routing template."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "clash-routing.ini"
BUILTIN_TARGETS = {"DIRECT", "REJECT"}
ALLOWED_RULESET_TYPES = {
    "clash-domain:",
    "clash-ipcidr:",
    "clash-classic:",
    "surge:",
    "quanx:",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    text = CONFIG.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "[custom]":
        fail(errors, "File must start with [custom].")

    semantic_text = "\n".join(
        line for line in lines if not line.lstrip().startswith((";", "#"))
    )
    if "\uff0c" in semantic_text or "\uff1a" in semantic_text or ". yaml" in semantic_text:
        fail(errors, "Full-width punctuation or broken URL found.")

    rules: list[tuple[int, str, str]] = []
    groups: dict[str, int] = {}
    url_test_groups: list[tuple[int, str, list[str]]] = []
    group_references: list[tuple[int, str, str]] = []

    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue

        if line.startswith("ruleset="):
            value = line.removeprefix("ruleset=")
            target, separator, rule = value.partition(",")
            if not separator or not target or not rule:
                fail(errors, f"Line {line_no}: malformed ruleset.")
                continue
            rules.append((line_no, target, rule))
            continue

        if not line.startswith("custom_proxy_group="):
            continue

        parts = line.removeprefix("custom_proxy_group=").split("`")
        if len(parts) < 2 or not parts[0]:
            fail(errors, f"Line {line_no}: malformed custom_proxy_group.")
            continue

        name = parts[0]
        if name in groups:
            fail(
                errors,
                f"Line {line_no}: duplicate group {name!r}; first defined on line {groups[name]}.",
            )
        else:
            groups[name] = line_no

        if parts[1] == "select":
            for reference in parts[2:]:
                if reference.startswith("[]"):
                    group_references.append((line_no, name, reference.removeprefix("[]")))

        if parts[1] in {"url-test", "fallback", "load-balance"}:
            if len(parts) < 5:
                fail(errors, f"Line {line_no}: missing URL or health-check settings.")
                continue
            url_test_groups.append((line_no, name, parts))
            if parts[3] != "https://www.gstatic.com/generate_204":
                fail(errors, f"Line {line_no}: unexpected health-check URL.")
            timing = parts[4].split(",")
            if len(timing) not in {1, 2, 3}:
                fail(errors, f"Line {line_no}: invalid health-check timing.")
            for token in timing:
                if token and not token.isdigit():
                    fail(errors, f"Line {line_no}: non-numeric health-check timing.")

    targets = {target for _, target, _ in rules}
    unknown = sorted(targets - BUILTIN_TARGETS - set(groups))
    for target in unknown:
        fail(errors, f"Ruleset references undefined group: {target!r}.")

    for line_no, owner, reference in group_references:
        if reference not in BUILTIN_TARGETS and reference not in groups:
            fail(
                errors,
                f"Line {line_no}: group {owner!r} references undefined group {reference!r}.",
            )

    if not rules:
        fail(errors, "No ruleset entries found.")
    elif not rules[-1][2].startswith("[]FINAL"):
        fail(errors, "The final rule must be []FINAL.")

    ordered_rules = [(line_no, target, rule) for line_no, target, rule in rules]
    private_pos = next(
        (index for index, (_, _, rule) in enumerate(ordered_rules) if "GEOSITE,private" in rule),
        None,
    )
    final_pos = next(
        (index for index, (_, _, rule) in enumerate(ordered_rules) if rule.startswith("[]FINAL")),
        None,
    )
    if private_pos is None or final_pos is None or private_pos >= final_pos:
        fail(errors, "Private-network direct rule must appear before the final rule.")

    steam_index = next(
        (
            index
            for index, (_, _, rule) in enumerate(ordered_rules)
            if rule.lower() == "[]geosite,steam"
        ),
        None,
    )
    broad_game_index = next(
        (
            index
            for index, (_, _, rule) in enumerate(ordered_rules)
            if rule.lower() == "[]geosite,category-games"
        ),
        None,
    )
    if steam_index is not None and broad_game_index is not None and steam_index >= broad_game_index:
        fail(errors, "Steam rule must appear before the broad category-games rule.")

    for line_no, _, rule in rules:
        if rule.startswith("[]"):
            continue
        if any(rule.startswith(prefix) for prefix in ALLOWED_RULESET_TYPES):
            if "https://" not in rule:
                fail(errors, f"Line {line_no}: external ruleset must use HTTPS.")
            continue
        fail(errors, f"Line {line_no}: unsupported ruleset type: {rule!r}.")

    for line_no, name, parts in url_test_groups:
        pattern = parts[2]
        try:
            re.compile(pattern)
        except re.error as exc:
            fail(errors, f"Line {line_no}: invalid regex for {name!r}: {exc}")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed: {len(rules)} rules, {len(groups)} proxy groups.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
