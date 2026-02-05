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

#------------------------
#Biquery table creation
#------------------------

resource "google_bigquery_table" "weather_hourly_forecast" {
  dataset_id = var.bq_dataset_id
  table_id   = var.bq_table_id

  # Partition table by ingestion date (Airflow logical date)
  time_partitioning {
    type  = "DAY"
    field = "ingestion_date"
  }

  # Append-only table (no clustering required for assignment,
  # but can be added later if needed)
  deletion_protection = false

  schema = <<EOF
[
  {
    "name": "weather_timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Forecasted hour timestamp from Open-Meteo API"
  },
  {
    "name": "ingestion_date",
    "type": "DATE",
    "mode": "REQUIRED",
    "description": "Airflow logical date when this forecast snapshot was ingested"
  },
  {
    "name": "latitude",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Latitude of the forecast location"
  },
  {
    "name": "longitude",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Longitude of the forecast location"
  },
  {
    "name": "timezone",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Timezone used by the API for hourly timestamps"
  },
  {
    "name": "temperature_2m",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Temperature at 2 meters above ground (°C)"
  },
  {
    "name": "relative_humidity_2m",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Relative humidity at 2 meters (%)"
  },
  {
    "name": "wind_speed_10m",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Wind speed at 10 meters (m/s)"
  }
]
EOF
}
