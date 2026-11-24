# Ask about Amir: answer API

A Cloudflare Worker that turns the facts the "Ask about Amir" assistant finds into a short, cited answer, using
Cloudflare Workers AI. It runs at `https://amir-zare.com/api/ask`.

How a question flows:

1. The assistant (Hugging Face Space, also embedded on amir-zare.com) searches `kb.json` in the visitor's browser
   and sends the question plus the IDs of the best-matching facts.
2. The Worker reads the facts itself from `https://amir-zare.com/kb.json`, so nobody can send it their own text.
3. Workers AI (Llama 3.3 70B, falling back to GLM-4.7-Flash) writes 1–3 sentences using only those facts, citing them
   as `[1]`, `[2]`, or replies `NO_ANSWER`.
4. The Worker checks the citations in code: citations to facts it didn't provide are removed, and every sentence
   without a valid citation is dropped. If no cited sentence is left, the answer is "no answer".
5. If the AI is unavailable (for example the free daily allowance is used up), the assistant falls back to quoting
   the best-matching facts, as before.

Safety:
- Personal questions (pay, age, family, beliefs, health, residency, private contact details) are refused by rule. The
  `GUARD` list in `src/index.js` must stay identical to the one in the Space's `engine.js`.
- Browsers only accept answers on amir-zare.com and the Space (CORS). This does not stop scripts, which can send any
  `Origin` header, so the rate limits below are what protect the free AI allowance.
- Questions are limited to 300 characters and 10 facts. AI error details are logged (`npx wrangler tail`), not returned.
- There is no API key: Workers AI is attached through the `AI` binding.

Rate limits (none of these is global on its own, so use all three):
1. The Workers rate-limit binding `RATE_LIMITER` in `wrangler.toml`: 6 questions a minute per IP, counted per
   Cloudflare location.
2. A per-instance limit in the code (6 a minute per IP).
3. A Cloudflare WAF rate-limiting rule on the zone, set once in the dashboard (see below).

### WAF rate-limiting rule (dashboard, one time)

1. Cloudflare dashboard → amir-zare.com → Security → WAF → **Rate limiting rules** → Create rule (in the newer
   dashboard: Security → Security rules → Create rule → Rate limiting rule).
2. Name: `api-ask per IP`.
3. If incoming requests match: Field **URI Path**, Operator **equals**, Value `/api/ask`
   (optionally add: **Request Method** equals `POST`).
4. With the same characteristics: **IP**.
5. When rate exceeds: the Free plan only offers a 10-second period, e.g. **3 requests per 10 seconds**. Paid plans
   can use a longer period, e.g. 10 requests per 1 minute.
6. Then take action: **Block** for the duration the plan allows (10 seconds on Free), then Deploy.

The Free plan includes one rate-limiting rule. If the option or these periods differ in your dashboard, use what it
offers; the Worker's own limits still apply.

## Deploy (one time)

Requirements: Node.js 18+ and your Cloudflare account (the one that has amir-zare.com).

```bash
cd ask-worker
npm install             # installs the pinned wrangler
npx wrangler login      # opens the browser to sign in to Cloudflare
npx wrangler deploy     # builds and deploys, and adds the amir-zare.com/api/ask route
```

Test it:

```bash
curl -s https://amir-zare.com/api/ask \
  -H "Origin: https://amir-zare.com" -H "Content-Type: application/json" \
  -d '{"question":"What is his job?","ids":["profile#0","profile#1"]}'
```

Run the unit tests (no Cloudflare account needed): `npm install`, then `npm test`. `wrangler` is pinned in
`package.json`; `npx wrangler deploy --dry-run` checks the config without uploading.

## Settings (wrangler.toml → [vars])

- `MODELS`: models to try in order. Change them if Cloudflare retires one.
- `ALLOWED_ORIGINS`: sites allowed to call the API.
- `KB_URL`: where the facts come from.

Free usage: Workers AI includes 10,000 Neurons a day on the free plan (roughly 100+ answers with Llama 3.3 70B).
When it runs out, requests fail until 00:00 UTC and the assistant quotes facts instead. Usage is visible in the
Cloudflare dashboard under AI → Workers AI.
