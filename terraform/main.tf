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
