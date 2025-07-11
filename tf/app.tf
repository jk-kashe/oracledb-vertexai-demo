# Repository
resource "google_artifact_registry_repository" "container_images" {
  location      = var.region
  repository_id = "container-images"
  description   = "Artifact Registry repository for container images"
  format        = "DOCKER"
  cleanup_policy_dry_run = false
  
  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state    = "UNTAGGED"
    }
  }
}

# API key
resource "google_apikeys_key" "coffee" {
  name = "coffee"
  display_name = "coffee"

  restrictions {
    api_targets {
      service = "aiplatform.googleapis.com"
    }
  }
}

# Service account
resource "google_service_account" "coffee" {
  account_id = "coffee"
  display_name = "Coffee"
}

resource "google_project_iam_member" "coffee" {
  project = var.project_id
  role = "roles/aiplatform.user"
  member = google_service_account.coffee.email
}

resource "google_cloud_run_v2_service" "coffee" {
  depends_on = [] # timeout for DB config

  name = "coffee"
  location = var.region
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.container_images.repository_id}/coffee:latest"

      env {
        name = "DATABASE_URL"
        value = local.oracle_database_url
      }

      env {
        name = "ORACLE_TNS_NAMES"
        value = "${google_oracle_database_autonomous_database.oracle.autonomous_database_id} = ${local.oracle_profiles.high.value}"
      }

      env {
        name = "TNS_ADMIN"
        value = "/app"
      }
    }

    service_account = google_service_account.coffee.email

    vpc_access {
      network_interfaces {
        network = google_compute_network.oracle.id
      }
    }
  }
}