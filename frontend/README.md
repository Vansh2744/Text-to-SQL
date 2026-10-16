# QueryPilot frontend (Next.js App Router)

    npm install
    cp .env.example .env.local
    npm run dev          # http://localhost:3000
    npm run typecheck && npm test && npm run build

Backend must be running (default http://localhost:8000). Without Clerk keys the app runs in **dev mode**
and sends `X-Dev-User`, which the backend accepts only with `AUTH_MODE=dev` and a non-production `APP_ENV`.
Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` to use Clerk; the backend then verifies the Clerk JWT itself.

UI components are small Tailwind components in `src/components/ui.tsx` (shadcn/ui was not used).
Monaco loads its editor files from a CDN at runtime.
