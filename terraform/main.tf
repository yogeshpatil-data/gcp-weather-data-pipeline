resource "google_storage_bucket" "raw_weather_bucket" {
  name     = var.gcs_bucket_name
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

resource "google_bigquery_dataset" "weather_dataset" {
  dataset_id = var.bq_dataset_id
  location   = var.region

  delete_contents_on_destroy = false
}


# -----------------------------
# Service Account for Pipeline
# -----------------------------
resource "google_service_account" "weather_pipeline_sa" {
  account_id   = "weather-pipeline-sa"
  display_name = "Weather Data Pipeline Service Account"
  description  = "Service account used by Airflow weather data pipeline"
}

# -----------------------------
# GCS Bucket IAM
# -----------------------------
resource "google_storage_bucket_iam_member" "gcs_object_admin" {
  bucket = google_storage_bucket.raw_weather_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.weather_pipeline_sa.email}"
}

# -----------------------------
# BigQuery Dataset IAM
# -----------------------------
resource "google_bigquery_dataset_iam_member" "bq_data_editor" {
  dataset_id = google_bigquery_dataset.weather_dataset.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.weather_pipeline_sa.email}"
}

resource "google_bigquery_dataset_iam_member" "bq_job_user" {
  dataset_id = google_bigquery_dataset.weather_dataset.dataset_id
  role       = "roles/bigquery.jobUser"
  member     = "serviceAccount:${google_service_account.weather_pipeline_sa.email}"
}
