#!/usr/bin/env python3
"""Validate the generic Shadowrocket configuration."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "shadowrocket-routing.conf"
SUPPORTED_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-SET",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "RULE-SET",
    "FINAL",
}
SUPPORTED_POLICIES = {"DIRECT", "PROXY", "REJECT"}


def main() -> int:
    errors: list[str] = []
    text = CONFIG.read_text(encoding="utf-8")
    lines = text.splitlines()

    required_sections = {"[General]", "[Rule]", "[Host]"}
    sections = {line.strip() for line in lines if line.strip().startswith("[")}
    for section in sorted(required_sections - sections):
        errors.append(f"Missing section {section}.")

    if "GEOSITE," in text:
        errors.append("GEOSITE is Clash-specific and cannot be used in Shadowrocket.")

    in_rules = False
    rules: list[tuple[int, str]] = []
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if line == "[Rule]":
            in_rules = True
            continue
        if line.startswith("[") and line.endswith("]"):
            in_rules = False
            continue
        if not in_rules or not line or line.startswith(("#", ";")):
            continue
        rules.append((line_no, line))

    if not rules:
        errors.append("No Shadowrocket rules found.")
    elif rules[-1][1] != "FINAL,PROXY,force-remote-dns":
        errors.append("The final rule must be FINAL,PROXY,force-remote-dns.")

    seen_rules: dict[str, int] = {}
    for line_no, rule in rules:
        parts = [part.strip() for part in rule.split(",")]
        rule_type = parts[0].upper()
        if rule_type not in SUPPORTED_RULE_TYPES:
            errors.append(f"Line {line_no}: unsupported rule type {rule_type!r}.")
            continue

        if rule_type == "FINAL":
            policy = parts[1] if len(parts) > 1 else ""
        elif rule_type in {"RULE-SET", "DOMAIN-SET"}:
            if len(parts) < 3:
                errors.append(f"Line {line_no}: malformed {rule_type} rule.")
                continue
            parsed = urlparse(parts[1])
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"Line {line_no}: {rule_type} URL must use HTTPS.")
            policy = parts[2]
        else:
            if len(parts) < 3:
                errors.append(f"Line {line_no}: malformed {rule_type} rule.")
                continue
            policy = parts[2]

        if policy not in SUPPORTED_POLICIES:
            errors.append(f"Line {line_no}: unsupported policy {policy!r}.")

        if rule in seen_rules:
            errors.append(
                f"Line {line_no}: duplicate rule; first defined on line {seen_rules[rule]}."
            )
        else:
            seen_rules[rule] = line_no

    if errors:
        print("Shadowrocket validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Shadowrocket validation passed: {len(rules)} rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
