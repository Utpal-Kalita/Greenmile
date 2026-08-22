# Greenmile Frontend

A dark-first operational interface for Greenmile’s bidirectional last-mile optimizer. The frontend is a **Next.js 16 App Router** application using TypeScript and Tailwind CSS 4. It consumes persisted scenarios, computed routes, events, metrics, benchmarks, and Azure OpenAI intelligence from the FastAPI backend.

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

The frontend owns no logistics results. It loads the persisted demo scenario from FastAPI, follows optimization progress over SSE, and renders the canonical run response. Configure `NEXT_PUBLIC_API_URL` when the API is not available at `http://localhost:8000`.

## Structure

```text
src/
├── app/            # App Router pages, metadata, and route states
├── components/     # Interactive product experiences and shared shell
├── data/           # Static navigation content only
├── lib/            # Small shared utilities
└── types/          # Greenmile domain types
```

The visual system follows `../docs/branding.md` and the experience follows `../docs/ui_ux.md`.
