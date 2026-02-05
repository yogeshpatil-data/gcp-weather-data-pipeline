from datetime import datetime, timedelta
import json
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator

from google.cloud import storage
from google.cloud import bigquery


# -------------------------------------------------------------------
# TASK 1: Fetch weather data from Open-Meteo API and store raw JSON in GCS
# -------------------------------------------------------------------
def fetch_and_store_weather_data(**context):
    """
    Fetches hourly weather forecast data from Open-Meteo API
    and stores the raw JSON response in GCS.

    """

    logical_date = context["ds"]  # Airflow logical date (YYYY-MM-DD)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "time_zone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Minimal schema validation
    if "hourly" not in data or "time" not in data["hourly"]:
        raise ValueError("Unexpected API response structure")

    bucket_name = "weather-raw-data-sp"
    object_path = f"weather/raw/ingestion_date={logical_date}/weather.json"

    client = storage.Client(project="weather-data-pipeline-sp")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)

    blob.upload_from_string(
        json.dumps(data),
        content_type="application/json"
    )

    # Only return a lightweight reference (XCom)
    return object_path


# -------------------------------------------------------------------
# TASK 2: Read raw JSON from GCS, transform, and load into BigQuery
# -------------------------------------------------------------------
def transform_and_load_to_bigquery(**context):
    """
    Reads raw weather JSON from GCS for the given logical date,
    transforms hourly arrays into row-based records,
    and appends them into BigQuery.

    Design principles:
    - Always read from raw storage (GCS)
    - Append-only load
    - No deduplication at ingestion time
    """

    logical_date = context["ds"]

    # GCS configuration
    bucket_name = "weather-raw-data-sp"
    object_path = f"weather/raw/ingestion_date={logical_date}/weather.json"

    storage_client = storage.Client(project="weather-data-pipeline-sp")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_path)

    if not blob.exists():
        raise FileNotFoundError(
            f"Raw file not found: gs://{bucket_name}/{object_path}"
        )

    raw_data = json.loads(blob.download_as_text())

    # Extract metadata
    latitude = raw_data.get("latitude")
    longitude = raw_data.get("longitude")
    timezone = raw_data.get("timezone")
    hourly = raw_data.get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    wind_speeds = hourly.get("wind_speed_10m", [])

    # Validate array alignment
    if not (
        len(times)
        == len(temperatures)
        == len(humidities)
        == len(wind_speeds)
    ):
        raise ValueError("Hourly arrays are not aligned")

    rows = []

    for i in range(len(times)):
        rows.append(
            {
                "weather_timestamp": times[i],
                "ingestion_date": logical_date,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "temperature_2m": temperatures[i],
                "relative_humidity_2m": humidities[i],
                "wind_speed_10m": wind_speeds[i],
            }
        )

    if not rows:
        # No rows is valid but should be explicit
        print("No hourly records found to load")
        return

    # BigQuery configuration
    project_id = "weather-data-pipeline-sp"
    dataset_id = "weather_analytics"
    table_id = "weather_hourly_forecast"

    bq_client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Insert rows (append-only)
    errors = bq_client.insert_rows_json(table_ref, rows)

    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    print(f"Inserted {len(rows)} rows into {table_ref}")


# -------------------------------------------------------------------
# DAG DEFAULT CONFIGURATION
# -------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


# -------------------------------------------------------------------
# DAG DEFINITION
# -------------------------------------------------------------------
with DAG(
    dag_id="weather_data_pipeline",
    description="ELT pipeline: Open-Meteo → GCS (raw) → BigQuery (structured)",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 6 * * *",  # Daily at 06:00 UTC
    catchup=False,
    tags=["assignment", "weather", "gcp"],
) as dag:

    fetch_and_store_task = PythonOperator(
        task_id="fetch_and_store_weather_data",
        python_callable=fetch_and_store_weather_data,
    )

    transform_and_load_task = PythonOperator(
        task_id="transform_and_load_to_bigquery",
        python_callable=transform_and_load_to_bigquery,
    )

    fetch_and_store_task >> transform_and_load_task
