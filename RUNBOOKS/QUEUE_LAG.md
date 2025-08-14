# Runbook: Queue Lag

1. Identify affected queues and consumers
2. Check consumer error logs and retry policies
3. Scale worker replicas; ensure idempotency
4. Drain DLQ; requeue after fix
5. Validate throughput and backlog drain
