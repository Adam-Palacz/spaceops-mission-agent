# ESA-AD slice manifest (RD3.3)

The lookalike slice has an import manifest and a replay manifest. CI uses this slice only. The Zenodo archives stay unread.

## Import manifest

`commit_slice_import` records `rd3.slice-manifest.v1`:

- `code_revision` supplied by the caller
- `mission_id` and lookalike `dataset_ids`
- each CSV `relative_path`, `md5`, `row_count`, and `byte_count`
- `byte_budget` and `bytes_planned`

The budget is an argument. If the CSV bytes exceed it, the function raises and does not create the output file. The manifest stores checksums and counts, not sample values.

## Replay manifest

`rd3.slice-replay.v1` names the same `code_revision`, the MD5 of the canonical import manifest, the mission, the dataset ids, and a time range. Repeating `replay_slice_event_ids` returns the same event ids. A changed file checksum fails before those ids are returned.
