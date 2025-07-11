# Enable APIs
resource "google_project_service" "api" {
    for_each = toset(var.apis)

    service = each.value
}

resource "time_sleep" "wait_for_api" {
  create_duration = "60s"

  depends_on = [google_project_service.api]
}