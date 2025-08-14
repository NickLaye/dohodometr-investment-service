# Runbook: Latency Regression

1. Confirm scope (p95/p99, endpoints, spike timeframe)
2. Check recent deploys; consider rollback if correlated
3. Inspect DB slow queries; add indexes if needed
4. Check external dependencies (timeouts, retries)
5. Profile hotspots; scale horizontally if saturated
6. Validate fix in staging; rollout gradually (canary)
