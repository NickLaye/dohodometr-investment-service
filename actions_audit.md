# GitHub Actions Audit

Ниже — сводка по workflow в `.github/workflows`.

| workflow | job.id | on | needs | continue-on-error | note |
|---|---|---|---|---|---|
| auto-labeler.yml | triage | pull_request_target [opened, synchronize, reopened] | — | — | — |
| cd-production-fixed.yml | build-and-push | push [main, tags v*], workflow_dispatch | — | — | — |
| cd-production-fixed.yml | security-scan | push [main, tags v*], workflow_dispatch | build-and-push | — | — |
| cd-production-fixed.yml | deploy-production | push [main] | build-and-push, security-scan | — | — |
| cd-production-fixed.yml | create-release | tags v* | deploy-production | — | — |
| cd-production-fixed.yml | docker-build (alias) | push [main, tags v*], workflow_dispatch | build-and-push | — | aligns to docker-build |
| cd-production-fixed.yml | security (alias) | push [main, tags v*], workflow_dispatch | security-scan | — | aligns to security |
| cd-production-fixed.yml | quality-gate (alias) | push [main], workflow_dispatch | docker-build, security | — | aligns to quality-gate |
| cd-production.yml | noop | workflow_dispatch | — | — | deprecated |
| ci.yml | lint-backend | push [main, develop], pull_request [main, develop] | — | true (partial steps) | опасно (не блокирует) |
| ci.yml | backend-tests | push, pull_request | — | — | target required |
| ci.yml | frontend-tests | push, pull_request | — | — | target required |
| ci.yml | security | push, pull_request | — | — | target required |
| ci.yml | docker-build | push, pull_request | — | — | target required |
| ci.yml | e2e-tests | pull_request | backend-tests, frontend-tests | — | — |
| ci.yml | quality-gate | push, pull_request | backend-tests, frontend-tests, security, docker-build | — | target required |
| ci.yml | backend-tests-alias | push, pull_request | backend-tests | — | aligns to backend-tests |
| ci.yml | frontend-tests-alias | push, pull_request | frontend-tests | — | aligns to frontend-tests |
| ci.yml | security-alias | push, pull_request | security | — | aligns to security |
| ci.yml | docker-build-alias | push, pull_request | docker-build | — | aligns to docker-build |
| ci.yml | quality-gate-alias | push, pull_request | quality-gate | — | aligns to quality-gate |
| codeql.yml | analyze | push [main], pull_request [main], schedule | — | — | security supplemental |
| comprehensive-security.yml | security-preflight | push [main, develop], PR [main], schedule, dispatch | — | true | опасно |
| comprehensive-security.yml | backend-security | push/PR/schedule/dispatch | security-preflight | true | опасно |
| comprehensive-security.yml | frontend-security | push/PR/schedule/dispatch | security-preflight | true | опасно |
| comprehensive-security.yml | container-security | push/PR/schedule/dispatch | backend-security, frontend-security | true | опасно |
| comprehensive-security.yml | sbom-generation | push/PR/schedule/dispatch | container-security | true | опасно |
| comprehensive-security.yml | penetration-testing | schedule/dispatch | container-security | true | опасно |
| comprehensive-security.yml | security-summary | push/PR/schedule/dispatch | backend-security, frontend-security, container-security, sbom-generation | true | опасно |
| docker-ci.yml | build | pull_request [main, develop] | — | — | — |
| docker-ci.yml | docker-build | pull_request [main, develop] | build | — | aligns to docker-build |
| release-please.yml | release | push [main], dispatch | — | — | — |
| security-baseline.yml | secret-scanning | dispatch, PR [main, develop] | — | true | опасно |
| security-baseline.yml | sbom | dispatch, PR [main, develop] | — | true | опасно |
| security-hardened.yml | secret-detection | schedule, push [main, develop], PR [main] | — | true | опасно |
| security-hardened.yml | codeql-analysis | schedule, push, PR | — | true | опасно |
| security-hardened.yml | sbom-generation | schedule, push, PR | — | true | опасно |
| security-hardened.yml | dependency-audit | schedule, push, PR | — | true | опасно |
| security-hardened.yml | docker-security-scan | schedule-excluded, push, PR | — | true | опасно |
| security-hardened.yml | infrastructure-security | push | — | true | опасно |
| security-hardened.yml | security-summary | push/PR | secret-detection, codeql-analysis, sbom-generation, dependency-audit, docker-security-scan | — | — |
| security-scanning.yml | codeql | schedule, push [main, develop], PR [main], dispatch | — | true | опасно |
| security-scanning.yml | dependency-scan | schedule, push [main, develop], PR [main], dispatch | — | true | опасно |
| security-scanning.yml | secret-scan | schedule, push [main, develop], PR [main], dispatch | — | — | — |
| security-scanning.yml | docker-security | schedule-excluded, push [main, develop], PR [main], dispatch | — | true | опасно |
| security-scanning.yml | infrastructure-scan | push [main, develop], PR [main], dispatch | — | true | опасно |
| security-scanning.yml | security-report | push/PR/dispatch | codeql, dependency-scan, secret-scan, docker-security, infrastructure-scan | — | — |

Примечания:
- «опасно» — у джобы установлен `continue-on-error: true`, что делает её неблокирующей.
- В `ci.yml` основные статусы уже соответствуют: backend-tests, frontend-tests, security, docker-build, quality-gate. Для меж‑workflow статусов добавлены alias‑джобы в текущем изменении.


