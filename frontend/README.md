# Greenmile Frontend

A dark-first operational interface for Greenmile’s bidirectional last-mile optimizer. The frontend is a **Next.js 16 App Router** application using TypeScript, Tailwind CSS 4, and seeded mock data.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Routes

- `/` — Trip demo: load Delhi NCR data, run the visible optimization pipeline, and explore impact, intelligence, packing, and driver mode.
- `/performance` — Performance Lab with workload benchmarks and optimization profiles.
- `/system` — System architecture and engine event timeline.
- `/how-it-works` — Four-step product explanation and technical methods.

## Commands

```bash
npm run dev        # start the development server
npm run lint       # lint the source
npm run typecheck  # run TypeScript without emitting files
npm run build      # create a production build
npm run start      # serve the production build
```

## Data

The current experience intentionally uses typed mock data from `src/data/mock-data.ts`. No backend or environment variable is required for the redesign demo.

## Structure

```text
src/
├── app/            # App Router pages, metadata, and route states
├── components/     # Interactive product experiences and shared shell
├── data/           # Typed Delhi NCR demo fixtures
├── lib/            # Small shared utilities
└── types/          # Greenmile domain types
```

The visual system follows `../docs/branding.md` and the experience follows `../docs/ui_ux.md`.
