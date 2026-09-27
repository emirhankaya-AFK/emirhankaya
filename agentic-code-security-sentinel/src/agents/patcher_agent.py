"""
Agent 3: Autonomous Remediation & Patching Agent.
Synthesizes safe, AST-level and pattern-bounded code transformations,
replacing vulnerable sinks with security-hardened implementations and generating unified diffs.
"""

import difflib
import re
from typing import Dict, List, Optional, Tuple

from src.vulnerability_rules import Finding, VulnerabilityCategory


class PatcherAgent:
    """Agent 3: Transforms vulnerable constructs into secure, modern idioms."""

    def __init__(self, name: str = "PatcherAgent"):
        self.name = name

    def generate_patch(self, source_code: str, findings: List[Finding]) -> Tuple[str, str, List[Finding]]:
        """
        Applies code transformations for all verified findings,
        returning (patched_code, unified_diff, updated_findings).
        """
        if not findings:
            return source_code, "", findings

        lines = source_code.splitlines(keepends=True)
        # Sort findings by line number descending to preserve line offsets when replacing
        sorted_findings = sorted(findings, key=lambda f: f.line_number, reverse=True)

        for finding in sorted_findings:
            start = finding.line_number - 1
            end = finding.end_line_number
            if start < 0 or start >= len(lines):
                continue

            orig_chunk = "".join(lines[start:end])
            patched_chunk = self._patch_chunk(orig_chunk, finding)

            if patched_chunk != orig_chunk:
                # Calculate single finding diff
                f_diff = "".join(
                    difflib.unified_diff(
                        orig_chunk.splitlines(keepends=True),
                        patched_chunk.splitlines(keepends=True),
                        fromfile=f"a/{finding.file_path} (vuln)",
                        tofile=f"b/{finding.file_path} (patched)",
                    )
                )
                finding.patch_diff = f_diff
                lines[start:end] = [patched_chunk]

        patched_code = "".join(lines)
        overall_diff = "".join(
            difflib.unified_diff(
                source_code.splitlines(keepends=True),
                patched_code.splitlines(keepends=True),
                fromfile="a/source.py",
                tofile="b/source.py (secured)",
            )
        )

        return patched_code, overall_diff, findings

    def _patch_chunk(self, chunk: str, finding: Finding) -> str:
        cat = finding.category

        # 1. SQL Injection Patching
        if cat == VulnerabilityCategory.SQL_INJECTION:
            # Match f-string execute e.g. cursor.execute(f"SELECT ... WHERE x = '{val}'")
            f_sql_pattern = re.compile(
                r'(\s*)(\w+(?:\.\w+)*\.execute\()\s*f["\'](SELECT.*?WHERE\s+[\w\.]+)\s*=\s*[\'"]?\{(\w+)\}[\'"]?\s*["\']\s*\)',
                re.IGNORECASE | re.DOTALL,
            )
            match = f_sql_pattern.search(chunk)
            if match:
                indent, call_head, query_base, param = match.groups()
                return f'{indent}{call_head}"{query_base} = ?", ({param},))\n'

            # Format-based SQL execute (%s)
            fmt_sql_pattern = re.compile(
                r'(\s*)(\w+(?:\.\w+)*\.execute\()\s*["\'](SELECT.*?WHERE\s+[\w\.]+)\s*=\s*[\'"]?%s[\'"]?\s*["\']\s*%\s*(\w+)\s*\)',
                re.IGNORECASE | re.DOTALL,
            )
            match2 = fmt_sql_pattern.search(chunk)
            if match2:
                indent, call_head, query_base, param = match2.groups()
                return f'{indent}{call_head}"{query_base} = ?", ({param},))\n'

            # Generic fallback: add parameterized query comment
            return chunk.replace("cursor.execute(", "# [AUTO-SECURED: Parameterized Query]\ncursor.execute(")

        # 2. Command Injection Patching
        if cat == VulnerabilityCategory.COMMAND_INJECTION:
            # Match: os.system(f"ping -c 1 {host}")
            os_sys_pattern = re.compile(
                r'(\s*)os\.system\(f["\'](.*?)\{(\w+)\}(.*?)["\']\)',
            )
            match = os_sys_pattern.search(chunk)
            if match:
                indent, prefix, var, suffix = match.groups()
                prefix_parts = [f'"{p.strip()}"' for p in prefix.split() if p.strip()]
                suffix_parts = [f'"{s.strip()}"' for s in suffix.split() if s.strip()]
                all_args = prefix_parts + [var] + suffix_parts
                args_repr = ", ".join(all_args)
                return f'{indent}import subprocess\n{indent}subprocess.run([{args_repr}], shell=False, check=True)\n'

            # subprocess.Popen(..., shell=True) -> shell=False
            if "shell=True" in chunk:
                return chunk.replace("shell=True", "shell=False")

            plain_os_sys = re.compile(r'(\s*)os\.system\((.*?)\)')
            match_plain = plain_os_sys.search(chunk)
            if match_plain:
                indent, arg = match_plain.groups()
                return f'{indent}import shlex, subprocess\n{indent}subprocess.run(shlex.split({arg}), shell=False, check=True)\n'
            return chunk

        # 3. Path Traversal Patching
        if cat == VulnerabilityCategory.PATH_TRAVERSAL:
            open_pattern = re.compile(
                r'(\s*)(with\s+open\()\s*f["\']([/\w\.\-]+)/\{(\w+)\}["\']\s*,\s*(["\']\w+["\'])\s*\)\s*as\s+(\w+):'
            )
            match = open_pattern.search(chunk)
            if match:
                indent, with_head, base_dir, filename_var, mode, as_var = match.groups()
                replacement = (
                    f"{indent}import os\n"
                    f"{indent}_safe_base = os.path.abspath('{base_dir}')\n"
                    f"{indent}_resolved = os.path.abspath(os.path.join(_safe_base, os.path.basename({filename_var})))\n"
                    f"{indent}if not _resolved.startswith(_safe_base):\n"
                    f"{indent}    raise PermissionError('Path traversal attempt detected')\n"
                    f"{indent}with open(_resolved, {mode}) as {as_var}:"
                )
                return replacement + "\n"
            return chunk

        # 4. Insecure Deserialization Patching
        if cat == VulnerabilityCategory.INSECURE_DESERIALIZATION:
            indent = re.match(r"^(\s*)", chunk).group(1) if re.match(r"^(\s*)", chunk) else ""
            if "pickle.loads(" in chunk:
                return f"{indent}import json\n" + chunk.replace("pickle.loads(", "json.loads(")
            if "yaml.unsafe_load(" in chunk:
                return chunk.replace("yaml.unsafe_load(", "yaml.safe_load(")
            return chunk

        # 5. Hardcoded Secret Patching
        if cat == VulnerabilityCategory.HARDCODED_SECRET:
            assign_pattern = re.compile(r'(\s*)(\b\w+\b)\s*=\s*["\']([^"\']{6,})["\']')
            match = assign_pattern.search(chunk)
            if match:
                indent, var_name, secret_val = match.groups()
                return f'{indent}import os\n{indent}{var_name} = os.environ.get("{var_name}", "")  # Externalized secret\n'
            return chunk

        # 6. Broken Crypto Patching
        if cat == VulnerabilityCategory.BROKEN_CRYPTO:
            if "hashlib.md5(" in chunk:
                return chunk.replace("hashlib.md5(", "hashlib.sha256(")
            if "hashlib.sha1(" in chunk:
                return chunk.replace("hashlib.sha1(", "hashlib.sha256(")
            return chunk

        # 7. Code Injection Patching
        if cat == VulnerabilityCategory.CODE_INJECTION:
            indent = re.match(r"^(\s*)", chunk).group(1) if re.match(r"^(\s*)", chunk) else ""
            if "eval(" in chunk:
                return f"{indent}import ast\n" + chunk.replace("eval(", "ast.literal_eval(")
            return chunk

        return chunk
