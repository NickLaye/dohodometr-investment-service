# 🤝 Contributing to Investment Service

First off, thank you for considering contributing to Investment Service! It's people like you that make this project great. 🙌

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Security Guidelines](#security-guidelines)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose**
- **Git**

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/investment-service.git
   cd investment-service
   ```

2. **Set up the environment**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Start development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. **Run database migrations**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   alembic upgrade head
   ```

6. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

## 🛠 How to Contribute

### 🐛 Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Provide detailed information** including steps to reproduce
4. **Include environment details** (OS, browser, versions)

### ✨ Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Provide clear use cases** and rationale
4. **Consider implementation complexity**

### 💻 Code Contributions

1. **Create a feature branch** from `main` (Git Workflow)
   ```bash
   git checkout main
   git pull --ff-only origin main
   git checkout -b feat/your-scope-short
   # examples: feat/auth-2fa, fix/api-400-status, docs/rules-v3
   ```

2. **Make your changes** following our coding standards
3. **Write tests** for new functionality
4. **Run tests locally** to ensure everything passes
5. **Commit with Conventional Commits**
   ```bash
   git commit -m "feat(auth): add 2FA TOTP flow"
   git commit -m "fix(api): return 400 for invalid 2FA code"
   ```

6. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** using our PR template (Squash & Merge only)

## 🔄 Pull Request Process

### Before Submitting (Required Checks)

- [ ] **Tests pass** locally (`make test`)
- [ ] **Linting passes** (`make lint`)
- [ ] **Documentation** is updated if needed
- [ ] **Commit messages** follow conventional commits
- [ ] **Branch is up-to-date** with main (rebase if needed)

CI jobs required to merge into `main`:

- Backend Tests
- Frontend Tests
- Security Scan
- Docker Build Test
- Quality Gate

### PR Requirements

1. **Fill out the PR template** completely
2. **Link related issues** using keywords (fixes #123)
3. **Add meaningful description** of changes
4. **Include tests** for new functionality
5. **Update documentation** if needed

### Review Process (Branch Protection)

1. **Automated checks** must pass (see required checks above)
2. **Code review** by at least one maintainer (2 for security/infra/high‑risk)
3. **Security review** for sensitive changes
4. **Manual testing** for UI/UX changes

### Git Workflow Summary

- Base branch: `main` (protected, linear history, squash merge)
- Branch naming: `feat|fix|docs|chore|perf|refactor|ci/<scope>-<short>`
- Conventional Commits for all commits and PR titles: `type(scope): subject`
- Rebase your branch onto latest `main` before requesting review
- Small PRs are preferred (≤400 LOC diff)
- Delete the feature branch after merge

## 📝 Issue Guidelines

### 🏷 Labels

- **Type**: `bug`, `feature`, `documentation`, `maintenance`
- **Priority**: `low`, `medium`, `high`, `critical`
- **Status**: `needs-triage`, `in-progress`, `blocked`
- **Component**: `backend`, `frontend`, `infrastructure`, `security`

### 📋 Issue Templates

Use the appropriate template:
- 🐛 [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- 🚀 [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- 🔒 [Security Issue](.github/ISSUE_TEMPLATE/security.md)

## 🎨 Coding Standards

### Python (Backend)

- **Follow PEP 8** with line length of 88 characters
- **Use type hints** for all function parameters and returns
- **Write docstrings** for all public functions and classes
- **Use Ruff** for linting and formatting
- **Follow FastAPI best practices**

```python
from typing import List, Optional
from pydantic import BaseModel

class PortfolioResponse(BaseModel):
    """Response model for portfolio data."""
    
    id: int
    name: str
    total_value: float
    currency: str
    
    class Config:
        from_attributes = True

async def get_portfolio(
    portfolio_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> PortfolioResponse:
    """
    Retrieve a portfolio by ID for a specific user.
    
    Args:
        portfolio_id: The ID of the portfolio to retrieve
        user_id: The ID of the user requesting the portfolio
        db: Database session dependency
        
    Returns:
        Portfolio data
        
    Raises:
        HTTPException: If portfolio not found or access denied
    """
    # Implementation here
```

### TypeScript/React (Frontend)

- **Use TypeScript strict mode**
- **Follow React best practices**
- **Use functional components** with hooks
- **Implement proper error boundaries**
- **Use ESLint and Prettier**

```tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PortfolioCardProps {
  portfolio: Portfolio;
  onUpdate?: (portfolio: Portfolio) => void;
}

export const PortfolioCard: React.FC<PortfolioCardProps> = ({
  portfolio,
  onUpdate,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleUpdate = async (): Promise<void> => {
    setIsLoading(true);
    try {
      // Update logic here
      onUpdate?.(portfolio);
    } catch (error) {
      console.error('Failed to update portfolio:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{portfolio.name}</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content here */}
      </CardContent>
    </Card>
  );
};
```

### Database

- **Use Alembic migrations** for all schema changes
- **Include up and down migrations**
- **Add database indexes** for performance
- **Use descriptive migration messages**

```python
"""Add portfolio performance tracking

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add performance tracking tables."""
    op.create_table(
        'portfolio_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_value', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'])
    )
    
    # Add index for performance queries
    op.create_index('ix_portfolio_performance_date', 'portfolio_performance', ['portfolio_id', 'date'])

def downgrade() -> None:
    """Remove performance tracking tables."""
    op.drop_index('ix_portfolio_performance_date')
    op.drop_table('portfolio_performance')
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── fixtures/      # Test data
└── conftest.py    # Test configuration
```

### Writing Tests

- **Test all new functionality**
- **Maintain >80% code coverage**
- **Use descriptive test names**
- **Follow AAA pattern** (Arrange, Act, Assert)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_portfolio():
    return {
        "name": "Test Portfolio",
        "currency": "USD",
        "description": "A test portfolio"
    }

def test_create_portfolio_success(client, sample_portfolio, auth_headers):
    """Test successful portfolio creation."""
    # Arrange
    payload = sample_portfolio
    
    # Act
    response = client.post("/api/v1/portfolios/", json=payload, headers=auth_headers)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["currency"] == payload["currency"]
    assert "id" in data
```

### Running Tests

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:e2e

# All tests
make test
```

## 🔒 Security Guidelines

### Security Requirements

- **Never commit secrets** to the repository
- **Use environment variables** for configuration
- **Validate all inputs** on both client and server
- **Follow OWASP guidelines**
- **Implement proper authentication** and authorization

### Security Checklist

- [ ] **Input validation** implemented
- [ ] **SQL injection** prevention in place
- [ ] **XSS protection** implemented
- [ ] **CSRF protection** enabled
- [ ] **Secure headers** configured
- [ ] **Secrets** properly managed
- [ ] **Dependencies** regularly updated

### Reporting Security Issues

**Never report security vulnerabilities in public issues!**

Email us at: **security@investment-service.ru**

See our [Security Policy](SECURITY.md) for details.

## 🎯 Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Adding tests

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(auth): add two-factor authentication
fix(portfolio): resolve calculation error
docs(api): update endpoint documentation
test(auth): add login flow tests
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 📚 Documentation

### Code Documentation

- **Comment complex logic**
- **Document public APIs**
- **Keep README up-to-date**
- **Update CHANGELOG.md**

### API Documentation

- **Use OpenAPI/Swagger** for backend APIs
- **Include request/response examples**
- **Document error responses**
- **Provide integration examples**

## 🎉 Recognition

Contributors will be recognized in:
- **README.md** - Contributors section
- **CHANGELOG.md** - Release notes
- **GitHub Releases** - Release notes

## 💬 Getting Help

- **GitHub Discussions** - For questions and ideas
- **GitHub Issues** - For bugs and feature requests
- **Email** - dev@investment-service.ru for private matters

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) as the project.

---

**Thank you for contributing! 🙏**

Your efforts help make this project better for everyone.
