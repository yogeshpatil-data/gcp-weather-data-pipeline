# GCP Weather Data Pipeline

## Overview

This repository contains an end-to-end data engineering pipeline built on **Google Cloud Platform (GCP)** as part of a take-home assignment for a **Data Engineer (3–3.5 YOE)** role.

The pipeline ingests weather forecast data from a public API, stores raw data in Google Cloud Storage (GCS), transforms it, and loads structured data into BigQuery. Orchestration is handled locally using Dockerized Apache Airflow, and all cloud infrastructure is provisioned using Terraform.

The solution is designed to be **append-only**, **reproducible**, and **interview-grade**, with clear separation of concerns across ingestion, storage, and analytics layers.

---

## High-Level Architecture

```
Open-Meteo API
      |
      v
Apache Airflow (Docker, Local)
      |
      v
Google Cloud Storage (Raw Zone)
      |
      v
BigQuery (Analytics / Warehouse)
```

---

## Assignment Requirements Mapping

| Requirement            | Implementation            |
| ---------------------- | ------------------------- |
| Infrastructure as Code | Terraform                 |
| Local orchestration    | Dockerized Apache Airflow |
| Public API ingestion   | Open-Meteo API            |
| Raw data storage       | Google Cloud Storage      |
| Structured analytics   | BigQuery                  |
| Append-only logic      | Enforced                  |
| Manual DAG execution   | Supported via Airflow UI  |
| Clean Git workflow     | Feature branch + PR       |

---

## Data Source

* **API**: Open-Meteo
* **Type**: Public weather forecast API
* **Granularity**: Hourly
* **Characteristics**:

  * Rolling multi-day forecast window
  * Overlapping data across API calls (expected)

---

## Data Storage Design

### Raw Zone (Google Cloud Storage)

* **Bucket**: `weather-raw-data-sp`
* **Path Convention**:

  ```
  gs://weather-raw-data-sp/weather/raw/ingestion_date=YYYY-MM-DD/weather.json
  ```

#### Design Decisions

* Append-only storage
* Hive-style partitioning using `ingestion_date`
* Raw data stored exactly as received from the API
* No transformations or enrichment at this layer

---

### Analytics Zone (BigQuery)

* **Dataset**: `weather_analytics`
* **Table**: `weather_hourly_forecast`

#### Table Schema (High-Level)

* `weather_timestamp` (TIMESTAMP)
* `ingestion_date` (DATE) – partition column
* `latitude` (FLOAT)
* `longitude` (FLOAT)
* `timezone` (STRING)
* `temperature_2m` (FLOAT)
* `relative_humidity_2m` (INTEGER)
* `wind_speed_10m` (FLOAT)

#### Partitioning

* Partitioned by `ingestion_date`
* Enables efficient pruning and time-based queries

---

## Orchestration (Apache Airflow)

* **Airflow Version**: 2.8.1
* **Executor**: SequentialExecutor (local development)
* **Deployment**: Docker Compose

### DAG: `weather_data_pipeline`

#### Tasks

1. **fetch_and_store_weather_data**

   * Calls the Open-Meteo API
   * Stores raw JSON response in GCS
   * Uses Airflow logical date as `ingestion_date`

2. **transform_and_load_to_bigquery**

   * Reads raw JSON from GCS
   * Transforms hourly arrays into row-based format
   * Loads data into BigQuery (append-only)

### Scheduling

* Schedule: `0 6 * * *`
* Catchup: Disabled
* Manual trigger supported via Airflow UI

---

## Infrastructure as Code (Terraform)

Terraform provisions the following resources:

* GCS bucket for raw data
* BigQuery dataset and table
* Service account and required IAM roles

### Key Principles

* No destructive changes to existing data
* Idempotent Terraform applies
* Infrastructure defined declaratively

---

## Append-Only Semantics & Idempotency

* Both raw and analytics layers are **append-only by design**
* No overwrites or updates are performed
* Each DAG run represents a snapshot identified by `ingestion_date`

### Duplicate Data Handling

* The Open-Meteo API returns overlapping forecast windows
* As a result, duplicate forecast records across runs are expected
* Deduplication or snapshot selection is intentionally deferred to downstream analytics or query-time logic

This design preserves historical forecast snapshots and aligns with common data lake / warehouse patterns.

---

## Local Setup & Execution

### Prerequisites

* Docker & Docker Compose
* Google Cloud SDK
* Terraform

### Steps

1. Authenticate using Application Default Credentials:

   ```bash
   gcloud auth application-default login
   ```

2. Provision infrastructure:

   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

3. Start Airflow:

   ```bash
   cd airflow
   docker compose up -d
   ```

4. Access Airflow UI:

   * URL: [http://localhost:8080](http://localhost:8080)
   * Username: `airflow`
   * Password: `airflow`

5. Trigger the `weather_data_pipeline` DAG manually

---

## Validation & Sanity Checks

* Raw data verified in GCS by ingestion date
* BigQuery table schema validated against Terraform
* Partitioning confirmed on `ingestion_date`
* Row counts validated per DAG run
* Sample data spot-checked for correctness

---

## Future Improvements

* Add downstream deduplicated views or models (e.g., latest forecast per hour)
* Parameterize locations for multi-city ingestion
* Introduce data quality checks
* Migrate orchestration to managed Airflow / Kubernetes for production

---

## Conclusion

This project demonstrates a complete, production-oriented data engineering pipeline with clear design rationale, strong separation of concerns, and adherence to modern best practices. The solution is intentionally simple where appropriate and extensible where needed.
