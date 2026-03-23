# AI Model Scanner Web

Public comparison tool and free API for 320+ AI models. Single-page Next.js app with 3 API endpoints, dark mode UI, and pre-computed recommendations.

**Live:** [ai-model-scanner-web.vercel.app](https://ai-model-scanner-web.vercel.app)
**API Docs:** [/api/models?help=true](https://ai-model-scanner-web.vercel.app/api/models?help=true)
**Source:** [github.com/alexbesp18/ai-model-scanner-web](https://github.com/alexbesp18/ai-model-scanner-web)

## Stack

- Next.js 16, shadcn/ui, TanStack Table, Geist
- Supabase (server-side reads from `ai_scanner` schema)
- Vercel (ISR, Firewall rate limiting)

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/models` | All models with filtering (tier, capabilities, price, context) |
| `GET /api/picks` | All 20 pre-computed recommendations |
| `GET /api/picks/:use_case` | Single recommendation by key |

Free, no auth, CORS enabled, 100 req/min per IP.
