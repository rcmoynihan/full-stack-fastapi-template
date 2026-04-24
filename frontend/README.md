# FastAPI Project - Frontend

The frontend is built with [Vite](https://vitejs.dev/), [React](https://reactjs.org/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [TanStack Router](https://tanstack.com/router) and [Tailwind CSS](https://tailwindcss.com/).

## Requirements

- [Bun](https://bun.sh/) (recommended) or [Node.js](https://nodejs.org/)

## Quick Start

```bash
bun install
bun run dev
```

Open http://localhost:5173/. The local dev server uses Vite hot reload and the
`/api` proxy from `vite.config.ts`; deployed containers get their API URL from
runtime config instead.

Check `package.json` for the available scripts.

## Generate Client

### Automatically

* From the top level project directory, run:

```bash
just generate-client
```

* Commit the changes.

### Manually

* Start the local backend stack.

* Download the OpenAPI JSON file from `http://localhost:8000/api/v1/openapi.json` and copy it to a new file `openapi.json` at the root of the `frontend` directory.

* To generate the frontend client, run:

```bash
bun run generate-client
```

* Commit the changes.

Regenerate the client whenever backend API changes alter the OpenAPI schema.

## Using a Remote API

The frontend reads its API base URL from `/env.js` at runtime. For local Vite
development, `frontend/public/env.js` leaves `API_BASE_URL` empty so requests use
the Vite `/api` proxy.

For deployed containers, set `API_BASE_URL` in the container environment:

```env
API_BASE_URL=https://api.my-domain.example.com
```

The frontend Docker entrypoint writes that value to `/env.js` when the container
starts.

## Code Structure

The frontend code is structured as follows:

* `frontend/src` - The main frontend code.
* `frontend/src/client` - The generated OpenAPI client.
* `frontend/src/components` -  The different components of the frontend.
* `frontend/src/hooks` - Custom hooks.
* `frontend/src/routes` - The different routes of the frontend which include the pages.

## End-to-End Testing with Playwright

The frontend includes initial end-to-end tests using Playwright. The reset
password tests read email through mailcatcher, so run them through the Compose
Playwright service when possible:

```bash
just test-e2e
```

That command starts the Playwright container with the Compose backend and
mailcatcher dependencies. To run Playwright from your host instead, start both
backend and mailcatcher first:

```bash
docker compose up -d --wait backend mailcatcher
```

Then run the tests:

```bash
bunx playwright test
```

You can also run your tests in UI mode to see the browser and interact with it running:

```bash
bunx playwright test --ui
```

To stop and remove the Docker Compose stack and clean the data created in tests, use the following command:

```bash
docker compose down -v
```

To update the tests, navigate to the tests directory and modify the existing test files or add new ones as needed.

For more information on writing and running Playwright tests, refer to the official [Playwright documentation](https://playwright.dev/docs/intro).
