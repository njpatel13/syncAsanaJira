resource "google_storage_bucket" "Cloud_function_bucket" {
  name     = "syncAsanaJira-${var.project_id}"
  location = var.region
  project  = var.project_id
}
