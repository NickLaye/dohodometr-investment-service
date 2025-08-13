# Runbook: Database Down

1. Confirm alert context and timeframe
2. Check Postgres pod/container status and logs
3. Verify disk/CPU/memory pressure on node
4. Attempt restart; if replicaset exists, failover
5. If data loss suspected, restore last backup to staging, validate, then to prod
6. Post-restore integrity checks and application smoke tests
7. Root cause analysis and preventive actions

