#!/usr/bin/env python3
"""Build and verify private/public SpaceOps engineering-book editions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "docs" / "book" / "book.yml"
PRIVATE_START = "<!-- private:start -->"
PRIVATE_END = "<!-- private:end -->"
PRIVATE_BLOCK = re.compile(
    rf"{re.escape(PRIVATE_START)}.*?{re.escape(PRIVATE_END)}",
    flags=re.DOTALL,
)
MARKDOWN_LINK = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    (
        "credentialed_url",
        re.compile(r"(?i)\b(?:postgres(?:ql)?|https?)://[^/\s:@]+:[^@\s/]+@"),
    ),
    (
        "secret_assignment",
        re.compile(
            r"(?im)^\s*(?:OPENAI_API_KEY|APPROVAL_API_KEY|GITHUB_TOKEN|"
            r"POSTGRES_PASSWORD)\s*=\s*[^\s<]{12,}\s*$"
        ),
    ),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
        "sha256": sha256_bytes(data),
        "bytes": len(data),
    }


def load_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("book config must be a mapping")
    required = {"schema_version", "book_version", "title", "chapters", "evidence"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"book config missing: {', '.join(sorted(missing))}")
    return config


def build_timestamp() -> str:
    epoch = os.getenv("SOURCE_DATE_EPOCH", "").strip()
    instant = datetime.fromtimestamp(int(epoch), tz=UTC) if epoch else datetime.now(UTC)
    return instant.replace(microsecond=0).isoformat()


def git_commit() -> str:
    explicit = os.getenv("BOOK_GIT_COMMIT", "").strip()
    if explicit:
        return explicit
    if not shutil.which("git"):
        return os.getenv("GITHUB_SHA", "unknown").strip() or "unknown"
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or "unknown").strip() or "unknown"


def validate_local_links(source: Path, text: str) -> None:
    for match in MARKDOWN_LINK.finditer(text):
        href = match.group(2).strip().split(maxsplit=1)[0].strip("<>")
        target = href.split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "data:")):
            continue
        resolved = (source.parent / target).resolve()
        if not resolved.exists():
            raise ValueError(f"broken link in {source}: {href}")


def rewrite_links(text: str, source_dir: Path, book_dir: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        href = match.group(2)
        bare = href.strip().split(maxsplit=1)[0].strip("<>")
        if (
            not bare
            or bare.startswith("#")
            or "://" in bare
            or bare.startswith(("mailto:", "data:"))
        ):
            return match.group(0)
        path_part, separator, fragment = bare.partition("#")
        resolved = (source_dir / path_part).resolve()
        relative = Path(os.path.relpath(resolved, book_dir)).as_posix()
        rewritten = relative + (f"#{fragment}" if separator else "")
        return f"{match.group(1)}{rewritten}{match.group(3)}"

    return MARKDOWN_LINK.sub(replace, text)


def remove_private_blocks(text: str) -> tuple[str, int]:
    starts = text.count(PRIVATE_START)
    ends = text.count(PRIVATE_END)
    if starts != ends:
        raise ValueError("unmatched private block marker")
    if starts and PRIVATE_START in PRIVATE_BLOCK.sub("", text):
        raise ValueError("nested or malformed private block")
    cleaned, count = PRIVATE_BLOCK.subn("", text)
    if PRIVATE_START in cleaned or PRIVATE_END in cleaned:
        raise ValueError("unapproved private marker remains")
    return cleaned, count


def scan_secrets(text: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS if pattern.search(text)]


def process_public(
    text: str, redactions: list[dict[str, str]]
) -> tuple[str, dict[str, int]]:
    result, private_count = remove_private_blocks(text)
    counts: dict[str, int] = {"private_blocks": private_count}
    for item in redactions:
        name = item["name"]
        result, count = re.subn(item["pattern"], item["replacement"], result)
        counts[name] = count
    findings = scan_secrets(result)
    if findings:
        raise ValueError(f"public secret scan failed: {', '.join(findings)}")
    return result, counts


def assemble(
    config_path: Path, config: dict[str, Any], edition: str
) -> tuple[str, list[Path], list[Path], dict[str, int]]:
    book_dir = config_path.parent
    chapter_paths = [(book_dir / item).resolve() for item in config["chapters"]]
    evidence_paths = [(book_dir / item).resolve() for item in config["evidence"]]
    for path in [*chapter_paths, *evidence_paths]:
        if not path.is_file():
            raise ValueError(f"missing book source/evidence: {path}")

    sections: list[str] = []
    for path in chapter_paths:
        text = path.read_text(encoding="utf-8")
        validate_local_links(path, text)
        sections.append(rewrite_links(text, path.parent, book_dir))
    combined = '\n\n<div class="page-break"></div>\n\n'.join(sections)
    counts: dict[str, int] = {}
    if edition == "public":
        combined, counts = process_public(
            combined, list(config.get("public_redactions", []))
        )
    return combined, chapter_paths, evidence_paths, counts


def metadata_header(
    config: dict[str, Any],
    *,
    edition: str,
    generated_at: str,
    commit: str,
) -> str:
    label = f"{edition.title()} edition"
    subtitle = f"{config.get('subtitle', '')} - {label}"
    return (
        "---\n"
        f"title: \"{config['title']}\"\n"
        f"subtitle: \"{subtitle}\"\n"
        f"date: \"{generated_at}\"\n"
        f"edition: \"{edition}\"\n"
        f"git_commit: \"{commit}\"\n"
        f"manifest_schema: \"{config['schema_version']}\"\n"
        "---\n\n"
    )


def write_manifest(
    *,
    config: dict[str, Any],
    edition: str,
    generated_at: str,
    commit: str,
    chapter_paths: list[Path],
    evidence_paths: list[Path],
    redactions: dict[str, int],
    output: Path,
) -> dict[str, Any]:
    manifest = {
        "schema_version": config["schema_version"],
        "book_version": str(config["book_version"]),
        "edition": edition,
        "generated_at": generated_at,
        "git_commit": commit,
        "chapters": [file_record(path) for path in chapter_paths],
        "evidence": [file_record(path) for path in evidence_paths],
        "redactions": dict(sorted(redactions.items())),
    }
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def run_pandoc(
    markdown: Path,
    output_dir: Path,
    formats: list[str],
    config: dict[str, Any],
) -> None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError(
            "pandoc is required for artifact builds; use --verify-only otherwise"
        )
    css_source = DEFAULT_CONFIG.parent / "book.css"
    css_target = output_dir / "book.css"
    shutil.copyfile(css_source, css_target)
    base = output_dir / f"spaceops-engineering-book-{output_dir.name}"
    for output_format in formats:
        target = base.with_suffix(f".{output_format}")
        command = [
            pandoc,
            str(markdown),
            "--from=gfm",
            "--standalone",
            "--toc",
            "--toc-depth=3",
            f"--metadata=lang:{config.get('language', 'en')}",
            f"--output={target}",
        ]
        if output_format in {"html", "epub", "pdf"}:
            command.append(f"--css={css_target}")
        if output_format == "html":
            command.extend(["--section-divs"])
        if output_format == "pdf":
            command.append(f"--pdf-engine={os.getenv('BOOK_PDF_ENGINE', 'weasyprint')}")
        proc = subprocess.run(command, cwd=DEFAULT_CONFIG.parent, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"pandoc {output_format} build failed")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--edition", choices=("private", "public"), required=True)
    parser.add_argument(
        "--output-root", type=Path, default=REPO_ROOT / "build" / "book"
    )
    parser.add_argument("--formats", default="html,pdf,epub")
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config_path = args.config.resolve()
    config = load_config(config_path)
    combined, chapters, evidence, redactions = assemble(
        config_path, config, args.edition
    )
    generated_at = build_timestamp()
    commit = git_commit()
    output_dir = args.output_root.resolve() / args.edition
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown = output_dir / "book.md"
    markdown.write_text(
        metadata_header(
            config,
            edition=args.edition,
            generated_at=generated_at,
            commit=commit,
        )
        + combined
        + "\n",
        encoding="utf-8",
    )
    manifest_path = output_dir / "manifest.json"
    write_manifest(
        config=config,
        edition=args.edition,
        generated_at=generated_at,
        commit=commit,
        chapter_paths=chapters,
        evidence_paths=evidence,
        redactions=redactions,
        output=manifest_path,
    )
    if not args.verify_only:
        formats = [item.strip() for item in args.formats.split(",") if item.strip()]
        invalid = set(formats) - {"html", "pdf", "epub"}
        if invalid:
            raise ValueError(f"unsupported formats: {', '.join(sorted(invalid))}")
        run_pandoc(markdown, output_dir, formats, config)
    print(
        json.dumps(
            {
                "edition": args.edition,
                "result": "pass",
                "verify_only": args.verify_only,
                "manifest": str(manifest_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
