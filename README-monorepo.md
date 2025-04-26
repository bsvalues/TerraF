# TerraFusion Monorepo

This repository contains the code for the TerraFusion platform, which includes various applications and services for intelligent code analysis and workflow optimization.

## Repository Structure

The monorepo is organized as follows:

```
terrafusion/
├── apps/               # Frontend applications
│   └── marketplace-ui/ # Plugin marketplace UI
├── packages/           # Shared libraries and modules
│   └── marketplace-backend/ # Plugin marketplace backend
├── server/             # Main API server
├── shared/             # Shared types and configuration
└── streamlit/          # Legacy Streamlit application (during migration)
```

## Development

### Requirements

- Node.js 16 or higher
- PNPM 8.6.0 or higher

### Installation

```bash
# Install dependencies
pnpm install
```

### Development Workflow

To start the development environment:

```bash
# Start all applications in development mode
pnpm dev

# Start a specific application
pnpm --filter <app-name> dev
```

### Building for Production

```bash
# Build all applications
pnpm build

# Build a specific application
pnpm --filter <app-name> build
```

## Migration Plan

The project is currently undergoing a migration from a monolithic Streamlit application to a modern monorepo architecture. The migration is being executed in phases:

1. **Phase 1: Scaffolding and Setup**
   - Set up monorepo structure with pnpm workspaces
   - Create shared configuration and schema files
   - Establish server skeleton with Express

2. **Phase 2: Domain Migration**
   - Migrate domain-specific components to separate packages
   - Create shared services for common functionality
   - Implement cross-cutting concerns (auth, logging, etc.)

3. **Phase 3: UI Migration**
   - Implement modern React-based UIs for each domain
   - Create shared component library with consistent styling
   - Develop marketplace UI for plugins

4. **Phase 4: Integration**
   - Connect all components through API interfaces
   - Implement comprehensive testing
   - Deploy in production environment

## Contributing

Please refer to the [CONTRIBUTING.md](./CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

This project is proprietary and confidential. All rights reserved.