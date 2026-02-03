# GCP Weather Data Pipeline

## Overview
This project implements a batch data pipeline that ingests hourly weather forecast data from a public API, stores raw data in Google Cloud Storage, and loads structured data into BigQuery for analytics.

The pipeline is built using:
- Terraform for infrastructure provisioning (IaC)
- Apache Airflow for orchestration
- Google Cloud Platform (GCS, BigQuery)

## Architecture (High-level)
- Weather data is fetched daily from the Open-Meteo API
- Raw JSON responses are stored in GCS (date-partitioned)
- Parsed data is appended to a BigQuery table
- Airflow orchestrates the end-to-end workflow

## Status
Project setup in progress. Infrastructure and pipeline implementation will be added incrementally.
