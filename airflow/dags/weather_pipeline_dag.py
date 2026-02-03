with DAG(
    dag_id="weather_data_pipeline",
    default_args=default_args,
    description="Ingest weather data from Open-Meteo into GCS and BigQuery",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["assignment", "weather", "gcp"],
) as dag:
