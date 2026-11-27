# Roadmap Changelog

Tracks significant roadmap-level decisions and direction changes.

## 2026-11-27

- Closed AV1.1 with an experiment registry for the published OPSSAT-AD train flag. The split is stratified random. Leaky features are rejected. No model is trained. No-go is unchanged.
- Closed RD4.4 as a waiver. Telemanom v2.0 does not record a sample license for SMAP/MSL, so no files were downloaded and none entered CI. No-go is unchanged.
- Closed RD4.3 with two synthetic hidden-reference cases. The hidden files are outside the agent image and the KB index. Real public reconstructions are not in git. No-go is unchanged.
- Closed RD4.2 with one cited battery mode for NASA LLIS 2046. No procedure text is stored. Conflicting records stay separate. No-go is unchanged.
- Closed RD4.1 with two public citation records: NASA LLIS 2046 without a stored lesson text, and the ESA anomaly dataset record under CC BY 3.0 IGO. An empty license is refused. No-go is unchanged.
- Closed RD3.3 on the ESA-AD lookalike. The slice manifest records checksums, code revision, and row counts. An over-budget import writes nothing. The archives stay unread. No-go is unchanged.
- Closed RD3.2 on the ESA-AD lookalike. Anomalies, rare nominal events, and telecommands are counted separately. Mission3 has zero telecommands. The archives stay unread. No-go is unchanged.
- Closed RD2.3 with one loopback model report on checksum-verified OPSSAT-AD (`llama3.2:3b`, policy `2026-11-26.v1`, citation check passed, zero write-tool calls). The re-entry campaign stays unread. No-go is unchanged.
- Closed RD2.4 from the RD2.3 lookalike evidence. The active path stays cited historical data in the lab. The later deferral condition is now met; RD3.2, RD3.3, RD4, and phase 04 stay Todo until started.
- Deferred RD3.2, RD3.3, RD4, and phase 04 until RD2.3 has a model-backed report on licensed data, or a later written waiver. The RD3.1 lookalike stays.
- Deferred the API router split (BL-008) and the agent-graph unification (BL-009). Left `docs/project-overview.md` untracked.
- Did not change the 2026-11-23 No-go decision.

## 2026-03-04

- Updated `02-production-scale.md` Phase 7 from Cloud Run-first wording to **K8s-first on GCP** with a vendor-portable baseline.
- Clarified that Cloud Run remains **optional** (showcase/fallback), not the default production path.
- Added explicit direction for future multi-cloud compatible GPU burst patterns (while keeping current scope focused on K8s portability, not autonomous resource scheduling).

