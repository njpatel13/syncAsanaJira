# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "source" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "${path.module}/function.zip"
}


# Add source code zip to the Cloud Function's bucket (Cloud_function_bucket)
resource "google_storage_bucket_object" "zip" {
  source       = data.archive_file.source.output_path
  content_type = "application/zip"
  name         = "src-${data.archive_file.source.output_md5}.zip"
  bucket       = google_storage_bucket.Cloud_function_bucket.name
  depends_on = [
    google_storage_bucket.Cloud_function_bucket,
    data.archive_file.source
  ]
}


# Create the Cloud function triggered by a `Finalize` event on the bucket
resource "google_cloudfunctions_function" "Cloud_function" {
  name                  = "helloHTTP"
  description           = "Terraform test-${var.project_id}"
  runtime               = "python311"
  project               = var.project_id
  region                = var.region
  source_archive_bucket = google_storage_bucket.Cloud_function_bucket.name
  source_archive_object = google_storage_bucket_object.zip.name
  available_memory_mb   = 128
  trigger_http          = true
  entry_point           = "hello_http"
  depends_on = [
    google_storage_bucket.Cloud_function_bucket,
    google_storage_bucket_object.zip,
  ]
}


resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = var.project_id
  region         = var.region
  cloud_function = google_cloudfunctions_function.Cloud_function.name


  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}
