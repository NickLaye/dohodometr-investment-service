# Release Process

1. Versioning: SemVer; conventional commits generate changelog
2. CI: lint -> tests -> security -> sbom -> build -> scan -> deploy
3. Staging deploy: run smoke, contract tests, and k6 smoke
4. Blue-Green/Canary: migrate DB (expand), deploy new, switch traffic, monitor, contract, clean old
5. Rollback: automatic on SLO breach; revert image tag; run smoke
6. Artifacts: SBOM attached to release; license report
