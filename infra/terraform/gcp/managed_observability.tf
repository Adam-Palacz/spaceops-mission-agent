# PR4.4 — managed Cloud Logging / Cloud Trace baseline.

resource "google_logging_project_bucket_config" "spaceops_pilot" {
  count = var.enable_managed_observability ? 1 : 0

  project        = var.project_id
  location       = var.region
  bucket_id      = var.managed_log_bucket_id
  retention_days = var.managed_log_retention_days
  description    = "Sanitized SpaceOps production-pilot and signed-audit records."

  depends_on = [google_project_service.apis]
}

resource "google_logging_project_sink" "spaceops_pilot" {
  count = var.enable_managed_observability ? 1 : 0

  name                   = "spaceops-pilot-${var.environment}"
  project                = var.project_id
  destination            = "logging.googleapis.com/projects/${var.project_id}/locations/${var.region}/buckets/${google_logging_project_bucket_config.spaceops_pilot[0].bucket_id}"
  unique_writer_identity = true

  filter = <<-EOT
    jsonPayload.spaceops_managed_canary=true OR
    jsonPayload.spaceops_audit=true OR
    textPayload:"spaceops_managed_canary" OR
    textPayload:"spaceops_audit"
  EOT
}

resource "google_service_account" "observability" {
  count = var.enable_managed_observability ? 1 : 0

  account_id   = "spaceops-otel-${var.environment}"
  display_name = "SpaceOps OTel collector (${var.environment})"
  description  = "Workload Identity principal for Cloud Trace and managed telemetry."

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "observability_trace_agent" {
  count = var.enable_managed_observability ? 1 : 0

  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.observability[0].email}"
}

resource "google_project_iam_member" "observability_log_writer" {
  count = var.enable_managed_observability ? 1 : 0

  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.observability[0].email}"
}

resource "google_service_account_iam_member" "observability_wi_user" {
  count = var.enable_managed_observability && var.enable_observability_workload_identity_binding ? 1 : 0

  service_account_id = google_service_account.observability[0].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.observability_k8s_namespace}/${var.observability_k8s_service_account}]"

  depends_on = [google_container_cluster.primary]
}
