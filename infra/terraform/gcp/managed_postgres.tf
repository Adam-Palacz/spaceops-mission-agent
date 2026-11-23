# PR4.5 — temporary Cloud SQL PostgreSQL HA/PITR drill profile.

resource "google_compute_network" "cloud_sql" {
  count = var.enable_managed_postgres_drill ? 1 : 0

  name                    = "spaceops-cloud-sql-${var.environment}"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [google_project_service.apis]
}

resource "google_compute_global_address" "cloud_sql_private_service_range" {
  count = var.enable_managed_postgres_drill ? 1 : 0

  name          = "spaceops-cloud-sql-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.cloud_sql[0].id
}

resource "google_service_networking_connection" "cloud_sql" {
  count = var.enable_managed_postgres_drill ? 1 : 0

  network                 = google_compute_network.cloud_sql[0].id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.cloud_sql_private_service_range[0].name]
}

resource "google_sql_database_instance" "spaceops_pilot" {
  count = var.enable_managed_postgres_drill ? 1 : 0

  name             = var.managed_postgres_instance_name
  database_version = "POSTGRES_15"
  region           = var.region

  deletion_protection = false

  settings {
    tier              = var.managed_postgres_tier
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = false
    edition           = "ENTERPRISE"

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled                                  = true
      private_network                               = google_compute_network.cloud_sql[0].id
      enable_private_path_for_google_cloud_services = true
      ssl_mode                                      = "ENCRYPTED_ONLY"
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    maintenance_window {
      day          = 7
      hour         = 4
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = false
      record_application_tags = false
      record_client_address   = false
    }

    user_labels = merge(local.common_labels, {
      drill = "pr45"
    })
  }

  depends_on = [google_service_networking_connection.cloud_sql]
}

resource "google_sql_database" "spaceops" {
  count = var.enable_managed_postgres_drill ? 1 : 0

  name     = "spaceops"
  instance = google_sql_database_instance.spaceops_pilot[0].name
}

resource "google_project_iam_member" "cloud_sql_client" {
  count = var.enable_managed_postgres_drill && var.managed_postgres_iam_principal != "" ? 1 : 0

  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = var.managed_postgres_iam_principal
}

resource "google_project_iam_member" "cloud_sql_instance_user" {
  count = var.enable_managed_postgres_drill && var.managed_postgres_iam_principal != "" ? 1 : 0

  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = var.managed_postgres_iam_principal
}

resource "google_sql_user" "pilot_iam" {
  count = var.enable_managed_postgres_drill && var.managed_postgres_database_user != "" ? 1 : 0

  name     = var.managed_postgres_database_user
  instance = google_sql_database_instance.spaceops_pilot[0].name
  type     = "CLOUD_IAM_USER"

  depends_on = [
    google_project_iam_member.cloud_sql_client,
    google_project_iam_member.cloud_sql_instance_user,
  ]
}
