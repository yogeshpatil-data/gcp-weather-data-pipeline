from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator


def fetch_weather_data(**context):
    """
    Fetch hourly weather forecast data from Open-Meteo API.

    Returns:
        dict: Raw JSON response from the API
    """
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

    # Defensive validation
    if "hourly" not in data or "time" not in data["hourly"]:
        raise ValueError("Unexpected API response structure")

    return data


default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="weather_data_pipeline",
    default_args=default_args,
    description="Ingest weather data from Open-Meteo into GCS and BigQuery",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["assignment", "weather", "gcp"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_weather_data",
        python_callable=fetch_weather_data,
    )
