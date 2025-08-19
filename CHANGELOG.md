# 📝 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2025-08-19)


### Features

* add comprehensive deployment automation and security tools ([4b361a7](https://github.com/NickLaye/dohodometr-investment-service/commit/4b361a7bd3b0b30cbab3c9124efebec04acb0ff9))
* add comprehensive health monitoring and fix Docker issues ([7acf6c3](https://github.com/NickLaye/dohodometr-investment-service/commit/7acf6c39d0c312a4a524bbe2b351df32c5797e1d))
* add comprehensive security tooling and monitoring stack ([f4b8d62](https://github.com/NickLaye/dohodometr-investment-service/commit/f4b8d624c8000b14b81a537c40f76169a6409a96))
* Implement new Dohodometr design system ([5802b0e](https://github.com/NickLaye/dohodometr-investment-service/commit/5802b0ed181c89b008c96e8021f97950f42d6f14))
* Migrate entire backend to synchronous architecture ([bd70e72](https://github.com/NickLaye/dohodometr-investment-service/commit/bd70e7253e5adebfd9636e68bfc07165a6fd3b48))


### Bug Fixes

* Repair GitHub Actions workflow YAML syntax and deployment paths ([bacbb5a](https://github.com/NickLaye/dohodometr-investment-service/commit/bacbb5ad2d11eaf499c0e4cfad41e653828fec4c))
* update GitHub Actions to latest stable versions ([07a2fd1](https://github.com/NickLaye/dohodometr-investment-service/commit/07a2fd10a566668a4a11999dd8fed23dd11aa522))
* добавить поле name в Docker Compose файлы ([49a82b8](https://github.com/NickLaye/dohodometr-investment-service/commit/49a82b8ab57fccda0af3341b5539fe0a0a397a58))
* исправить критические проблемы CI/CD pipeline ([f1a6665](https://github.com/NickLaye/dohodometr-investment-service/commit/f1a666579f462acaf310dd6c63bd52f05ebe2b54))
* исправить критические проблемы Docker build в CI/CD\n\nДВА УРОВНЯ ИСПРАВЛЕНИЙ:\n\n🐳 DOCKER BUILD ISSUES:\n- Исправлен устаревший npm синтаксис: --only=production → --omit=dev \n- Создана отсутствующая папка frontend/public/ с базовыми ресурсами\n- Исправлен .dockerignore: убрано исключение папки public\n- Docker build теперь проходит успешно (100.2s, все 24/24 этапа)\n\n⚛️ NEXT.JS SSR PRERENDER FIXES:\n- Сделали useAuth SSR-безопасным с fallback для server-side\n- Добавили export const dynamic = 'force-dynamic' для динамических страниц\n- Исправлена ошибка 'useAuth must be used within AuthProvider' при prerender\n- Все страницы (/, /auth/*, /app, /tax-demo) теперь собираются корректно\n\n📁 СОЗДАННЫЕ ФАЙЛЫ:\n- frontend/public/favicon.svg - базовая иконка\n- frontend/public/favicon.ico - для браузерной совместимости  \n- frontend/public/robots.txt - для SEO\n\n�� РЕЗУЛЬТАТ:\n- 'Build and Push Images' job больше не падает\n- CI/CD pipeline готов к успешному прохождению\n- Все red commits должны стать green ✅\n\nТестировано локально: Docker build успешен ([606688a](https://github.com/NickLaye/dohodometr-investment-service/commit/606688a3784971aa2b4243664e8a0b8f445a4659))
* обновить docker-compose команды до Docker Compose v2 ([1a919ee](https://github.com/NickLaye/dohodometr-investment-service/commit/1a919ee1f831faa892d41b397e824bf019938b3b))

## [Unreleased]

### 🚀 Added
- Comprehensive development standards and tooling setup
- Pre-commit hooks with security scanning
- GitHub Actions CI/CD pipeline
- Code quality tools (ESLint, Prettier, Ruff, MyPy)
- Security scanning (Bandit, Trivy, CodeQL)
- Issue and PR templates
- Contributing guidelines and code of conduct
- Automated dependency updates with Renovate (weekly)

### 🔧 Changed
- Migrated from async database calls to synchronous for stability
- Updated domain configuration for dohodometr.ru
- Improved Docker configurations for production deployment

### 🐛 Fixed
- Docker build issues for ARM64 architecture compatibility
- YAML syntax errors in Docker Compose configurations
- Frontend dependency conflicts with Radix UI components

### 🔒 Security
- Added secrets detection in pre-commit hooks
- Implemented comprehensive security scanning pipeline
- Enhanced container security with non-root users
- Added security headers and HTTPS enforcement
- Updated security dependencies and CI scanning jobs as part of repo hardening

## [1.0.0] - 2025-01-08

### 🎉 Initial Release

#### 🚀 Added

**Backend Features:**
- FastAPI-based REST API with OpenAPI documentation
- JWT authentication with refresh tokens
- Two-factor authentication (TOTP) support
- User registration and profile management
- Portfolio creation and management
- Account management (brokerage, IIS, pension accounts)
- Transaction import from CSV files
- Financial analytics and calculations
- Database encryption for sensitive data
- Comprehensive logging and monitoring

**Frontend Features:**
- Next.js 14 with App Router
- TypeScript and TailwindCSS
- Responsive design with shadcn/ui components
- User authentication flows
- Portfolio dashboard
- Transaction import interface
- Analytics and reporting views
- Real-time data updates

**Infrastructure:**
- Docker containerization
- PostgreSQL 16 database with pgcrypto
- Redis for caching and job queues
- MinIO for file storage
- Traefik reverse proxy with Let's Encrypt
- Prometheus and Grafana monitoring
- Production-ready deployment scripts

**Security Features:**
- OWASP ASVS L2 compliance
- AES-256-GCM encryption
- Argon2id password hashing
- Rate limiting and CORS protection
- Security headers implementation
- Audit logging for all user actions

#### 🏗️ Technical Architecture

**Backend Stack:**
- Python 3.12 + FastAPI
- SQLAlchemy with Alembic migrations
- Pydantic for data validation
- Celery for background tasks
- Redis for caching
- PostgreSQL for data storage

**Frontend Stack:**
- Next.js 14 with TypeScript
- React 18 with hooks
- TailwindCSS for styling
- Recharts for data visualization
- React Query for state management
- Zod for validation

**DevOps:**
- Docker multi-stage builds
- docker-compose for orchestration
- Health checks and monitoring
- Automated backups
- SSL/TLS encryption
- Production deployment automation

#### 📊 Supported Features

**Portfolio Management:**
- Multiple portfolio support
- Account categorization (brokerage, IIS, pension)
- Asset type support (stocks, bonds, ETFs, currencies)
- FIFO position tracking
- Currency conversion and revaluation

**Transaction Processing:**
- CSV import from major Russian brokers:
  - Tinkoff Investments
  - Sberbank Investor
  - VTB Capital
  - BCS Broker
  - Finam
  - Otkritie Broker
- Manual transaction entry
- Transaction categorization and validation
- Duplicate detection and handling

**Analytics & Reporting:**
- Portfolio performance metrics (TWR, XIRR)
- Asset allocation analysis
- P&L calculations with FIFO accounting
- Currency impact analysis
- Benchmark comparisons (IMOEX, S&P 500)
- Export capabilities

**User Experience:**
- Intuitive dashboard design
- Mobile-responsive interface
- Real-time data updates
- Comprehensive error handling
- Loading states and feedback
- Accessibility compliance

#### 🌍 Deployment Options

**VPS Deployment (Recommended):**
- Full-stack deployment on Ubuntu server
- Automatic SSL certificate management
- Production monitoring and alerting
- Automated backup solutions
- Domain: https://dohodometr.ru

**Development Setup:**
- Docker-based local development
- Hot reloading for both frontend and backend
- Database seeding and test data
- Development tools integration

#### 🔧 Configuration

**Environment Variables:**
- Comprehensive configuration through .env files
- Production vs development settings
- Database and Redis connection strings
- External API keys and secrets
- Security and encryption settings

**Database Setup:**
- Automated migration system
- Data encryption at rest
- Connection pooling
- Performance optimization
- Backup and recovery procedures

#### 📋 Installation Requirements

**System Requirements:**
- Ubuntu 20.04 LTS or later
- Docker 20.x+ and Docker Compose 2.x+
- 2+ GB RAM (4+ GB recommended)
- 20+ GB storage space
- SSL certificate (automated via Let's Encrypt)

**Development Requirements:**
- Python 3.12+
- Node.js 18+
- PostgreSQL 16
- Redis 7
- Git

#### 🧪 Testing Coverage

**Backend Testing:**
- Unit tests for business logic
- Integration tests for API endpoints
- Database testing with fixtures
- Security testing for vulnerabilities
- Performance testing for bottlenecks

**Frontend Testing:**
- Component unit tests
- Integration tests for user flows
- E2E tests with Playwright
- Accessibility testing
- Cross-browser compatibility

#### 📚 Documentation

**User Documentation:**
- Getting started guide
- Feature documentation
- API reference
- Troubleshooting guide
- FAQ and best practices

**Developer Documentation:**
- Setup and installation guide
- Architecture overview
- API documentation
- Contributing guidelines
- Security guidelines

#### 🔒 Security Measures

**Data Protection:**
- End-to-end encryption
- Secure password storage
- Session management
- CSRF protection
- XSS prevention

**Infrastructure Security:**
- Container hardening
- Network isolation
- Firewall configuration
- Intrusion detection
- Regular security updates

**Compliance:**
- GDPR considerations
- Financial data protection
- Audit trail maintenance
- User consent management
- Data retention policies

---

## 📋 Version History Format

### Types of Changes
- 🚀 **Added** for new features
- 🔧 **Changed** for changes in existing functionality  
- 🔄 **Deprecated** for soon-to-be removed features
- 🗑️ **Removed** for now removed features
- 🐛 **Fixed** for any bug fixes
- 🔒 **Security** for vulnerability fixes

### Versioning Scheme
- **Major.Minor.Patch** (e.g., 1.0.0)
- **Major**: Breaking changes
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, backwards compatible

### Release Notes Format
Each release includes:
- Version number and date
- Summary of changes
- Migration notes (if applicable)
- Known issues
- Contributors acknowledgment

---

## 🤝 Contributing to Changelog

When contributing changes:
1. Add entries to `[Unreleased]` section
2. Use appropriate emoji and category
3. Include PR/issue numbers where applicable
4. Follow the established format
5. Update on each significant change

## 📞 Support

For questions about releases or changes:
- 📧 Email: support@investment-service.ru
- 💬 GitHub Discussions
- 🐛 GitHub Issues

---

**Note**: This changelog is automatically updated as part of our release process. For the most current information, check the [GitHub Releases](https://github.com/yourusername/investment-service/releases) page.
