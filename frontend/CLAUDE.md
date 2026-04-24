# Frontend CLAUDE.md

## Setup
- Bun for package management and scripts
- `bun install` to install dependencies
- `bun run dev` for Vite dev server

## Architecture
- React 19 with TanStack Router file-based routing
- TanStack Query for server state
- Radix UI + Tailwind CSS for components and styling
- Auto-generated API client from backend OpenAPI spec

## Runtime Configuration
- Config is loaded from `/env.js` at runtime
- Access API config through `getApiBaseUrl()` in `src/config.ts`
- For local dev, Vite proxy forwards `/api` to the backend
- Do not use `import.meta.env.VITE_*` for deployment-varying config

## Code Generation
- `just generate-client` regenerates `frontend/openapi.json` and `src/client/` from backend OpenAPI
- Do not manually edit files in `src/client/` or `src/routeTree.gen.ts`

## Key Files
- `src/main.tsx` - App entrypoint, router setup, API client config
- `src/config.ts` - Runtime config accessor
- `src/routes/` - TanStack Router file-based routes
- `src/hooks/` - Custom React hooks
- `src/components/ui/` - UI primitives
- `openapi-ts.config.ts` - Generated API client configuration

## Linting
- `bun run lint` - auto-fix mode for development
- `bun run lint:ci` - read-only check for CI and quality gates
