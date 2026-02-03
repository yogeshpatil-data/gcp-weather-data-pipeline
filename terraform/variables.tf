variable "project_id" {
  description = "GCP project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "asia-south1"
}

variable "gcs_bucket_name" {
  description = "GCS bucket name for raw weather data"
  type        = string
}

variable "bq_dataset_id" {
  description = "BigQuery dataset ID for weather analytics"
  type        = string
}
