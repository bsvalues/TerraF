# Contributing to TerraFusion

Thank you for your interest in contributing to TerraFusion! This document provides guidelines and instructions for contributing to the project.

## Development Process

### Branch Organization

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature branches

### Development Workflow

1. Fork the repository
2. Create a feature branch (`feature/your-feature-name`)
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request to the `develop` branch

## Code Standards

### TypeScript

- Use TypeScript for all new code
- Maintain strict type safety
- Follow the existing code style

### React

- Use functional components with hooks
- Implement proper error boundaries
- Ensure accessibility compliance

### Testing

- Write unit tests for all new features
- Maintain or improve code coverage
- Include integration tests for API endpoints

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) for our commit messages:

- `feat:` - A new feature
- `fix:` - A bug fix
- `docs:` - Documentation changes
- `style:` - Changes that do not affect the meaning of the code (formatting, etc.)
- `refactor:` - Code changes that neither fix a bug nor add a feature
- `perf:` - Performance improvements
- `test:` - Adding or correcting tests
- `chore:` - Changes to the build process or auxiliary tools

## Pull Request Process

1. Update documentation if necessary
2. Update the README.md with details of changes if applicable
3. The PR should pass all CI checks
4. A maintainer will review and merge your Pull Request

## Setting Up Development Environment

### Prerequisites

- Node.js 16 or higher
- PNPM 8.6.0 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/terrafusion.git

# Navigate to the repository
cd terrafusion

# Install dependencies
pnpm install

# Start the development environment
pnpm dev
```

## Getting Help

If you have questions or need help with the contribution process, please:

- Comment on the relevant issue
- Reach out to the maintainers
- Check the documentation

Thank you for contributing to TerraFusion!