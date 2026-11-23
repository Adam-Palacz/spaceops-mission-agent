output "project_id" {
  description = "GCP project ID."
  value       = var.project_id
}

output "region" {
  description = "Primary region."
  value       = var.region
}

output "cluster_name" {
  description = "GKE cluster name."
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE control plane endpoint (sensitive)."
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "artifact_registry_repository" {
  description = "Full Artifact Registry repository path for docker push."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.spaceops.repository_id}"
}

output "deploy_service_account_email" {
  description = "Email of the CI/deploy service account."
  value       = google_service_account.deploy.email
}

output "eso_service_account_email" {
  description = "GSA for External Secrets Operator (annotate K8s SA per PS6.6 runbook)."
  value       = google_service_account.eso.email
}

output "get_credentials_command" {
  description = "gcloud command to configure kubectl."
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}

output "docker_push_example_api" {
  description = "Example docker tag/push for the API image."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.spaceops.repository_id}/api:stage"
}

output "budget_enabled" {
  description = "Whether PS6.9 billing budget alert is managed by Terraform."
  value       = var.enable_budget_alert
}

output "managed_observability_enabled" {
  description = "Whether PR4.4 managed logging/tracing resources are enabled."
  value       = var.enable_managed_observability
}

output "managed_log_bucket_name" {
  description = "Managed SpaceOps logging bucket resource name."
  value = (
    var.enable_managed_observability
    ? google_logging_project_bucket_config.spaceops_pilot[0].name
    : null
  )
}

output "observability_service_account_email" {
  description = "GSA used by the OTel collector through Workload Identity."
  value = (
    var.enable_managed_observability
    ? google_service_account.observability[0].email
    : null
  )
}

output "managed_postgres_connection_name" {
  description = "Cloud SQL connection name for the temporary PR4.5 source instance."
  value = (
    var.enable_managed_postgres_drill
    ? google_sql_database_instance.spaceops_pilot[0].connection_name
    : null
  )
}

output "managed_postgres_private_ip" {
  description = "Private address of the temporary PR4.5 source instance."
  value = (
    var.enable_managed_postgres_drill
    ? google_sql_database_instance.spaceops_pilot[0].private_ip_address
    : null
  )
}
