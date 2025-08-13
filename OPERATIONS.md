# Operations Guide

## SLO/SLI
- Availability: 99.9%
- API p95 latency: <= 400ms; p99 <= 1200ms
- Error rate: <= 1%

## Alerts (Prometheus/Grafana)
- Availability: up if /health returns 200
- Latency: p95 > 400ms for 5m
- Error rate: > 1% for 5m
- DB connection errors spike

## Runbooks
- See `RUNBOOKS/`

## Routines
- Daily: check error budget, review alerts, rotate temp credentials
- Weekly: dependency updates, vulnerability triage
- Monthly: backup restore drill on staging, secret rotation check

## Access
- Production access via bastion; MFA required
- Changes only via PR and CI/CD

## Backups
- Nightly DB backup to S3/MinIO, 30/90 retention
- Monthly restore verification job on staging

## Incident Comms
- Telegram on-call channel; status page update within 30m

