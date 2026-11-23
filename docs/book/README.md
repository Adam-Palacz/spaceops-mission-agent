# SpaceOps Engineering Book

This directory is the canonical source for the English engineering book. It is a narrative index
over the repository, not a replacement for ADRs, runbooks, tests, sprint reviews, or JSON evidence.

## Editions

- **Private engineering edition:** complete repository-facing links, implementation details, and
  operational lessons.
- **Public edition:** removes `private` blocks, applies configured redactions, and fails if common
  secret patterns remain.

Both editions are generated from the same chapter files and `book.yml`.

## Toolchain

- Python 3.12 + PyYAML: source assembly, public redaction, link checks, evidence hashing, and
  deterministic manifest.
- Pandoc: standalone navigable HTML and EPUB.
- WeasyPrint through Pandoc: PDF.
- Optional Playwright: live screenshots. The default CI-safe screenshot command only writes a
  deterministic capture plan when services are unavailable.

Generated files go to `build/book/` and are not committed.

```bash
make book             # private + public HTML/PDF/EPUB
make book-private
make book-public
make book-verify      # source/link/redaction/manifest checks; no Pandoc required
make book-screenshots-dry-run
```

Direct examples:

```bash
python scripts/book_build.py --edition private
python scripts/book_build.py --edition public
python scripts/book_build.py --edition public --verify-only
python scripts/book_screenshots.py --mode dry-run
```

Set `SOURCE_DATE_EPOCH` for byte-stable build metadata in CI. The manifest records schema, book
version, edition, UTC build date, Git commit SHA, ordered source hashes, and evidence hashes.

## Private blocks

Content that is useful internally but must not enter the public edition is wrapped exactly once:

```markdown
<!-- private:start -->
Internal-only material.
<!-- private:end -->
```

Nested or unmatched markers fail the build. Redaction is not permission to place secrets in source:
secret-like values fail public verification even after configured field replacement.

## Screenshot workflow

The collector targets the SpaceOps UI, Grafana, Prometheus, and Jaeger. Live mode requires
Playwright and explicit URLs. It stores PNG files plus `screenshots.json` captions; it does not
automate authenticated cloud consoles. Screenshots must be reviewed before public publication.

## Maintenance policy

At every sprint or phase closure:

1. update affected chapters and canonical links;
2. add new ADR/review/evidence entries to `book.yml` or the appendix;
3. run `make book-verify`;
4. build both editions and review the public artifact;
5. attach generated artifacts to CI/release output, never edit generated HTML/PDF/EPUB directly.

Publication always requires a human editorial/security review.
