# Historical cases (RD4.3)

Visible packets live in `visible/`. Hidden references live in `hidden/` and are for the scorer only.

`hidden/` is listed in the root `.dockerignore` and is not a Compose volume. KB indexing reads `kb/` only. Telemetry reads `data/telemetry/` only. Real public reconstructions are not in git. A blinded packet is not a claim that a model has never seen a public report.
