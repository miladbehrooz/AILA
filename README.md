# LAIA
Learning AI asistant

## Log Monitoring

The project ships a self-hosted Grafana/Loki/Promtail stack so you can inspect the application logs (streamed via stdout) and the archived `backend/logs/laia.log` file.

1. Start the monitoring stack alongside the rest of the services: `docker compose up -d loki promtail grafana`.
2. Open Grafana at [http://localhost:3000](http://localhost:3000) (default `admin` / `admin` credentials).
3. Use the pre-provisioned Loki data source and run LogQL queries such as `{service="api"} |= "ERROR"` to filter ETL errors and warnings.

Promtail scrapes both:
- The JSON-formatted stdout/stderr output from every Docker container (so application requests, schedulers, etc. show up without extra mounts).
- The historical `backend/logs/laia.log` file for redundancy or offline inspection.

The Python logger writes to stdout and the rotating `backend/logs/laia.log` file simultaneously, which keeps the legacy log file available while following the “logs go to stdout” best practice for containerized deployments.
