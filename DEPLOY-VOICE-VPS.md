# Deploy for smooth live voice (VPS, Path A)

The choppy/slow "Talk to Mary live" on localhost is caused by the dev machine's
slow network path to OpenAI (measured 12–76s per call). Deploying the backend to
a cloud host with fast OpenAI connectivity makes per-turn latency sub-second.

**Pick a US region** (e.g. US-East) — closest to OpenAI's API and to Neon — this
is the single biggest latency win.

## 1. Provision the VPS
- Ubuntu 22.04+, 2 vCPU / 2–4 GB RAM is plenty. US-East region.
- Install Docker + compose plugin:
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```
- Open the firewall for HTTP/HTTPS:
  ```bash
  ufw allow 80,443/tcp && ufw allow 443/udp && ufw enable
  ```

## 2. DNS (do this first so Caddy can issue certs)
Point two **non-proxied** A records at the VPS public IP:
- `api.workflowauth.com`  → VPS IP   (Caddy → backend; Vapi calls this)
- `app.workflowauth.com`  → VPS IP   (Caddy → frontend)

On Cloudflare DNS use the **grey cloud** (DNS only) — proxied breaks Let's Encrypt's TLS-ALPN challenge.

## 3. Clone + configure
```bash
git clone <your-repo-url> dropline && cd dropline
cp .env.example .env
```
Fill in `.env` (these all matter for voice + the live widget):

| Var | Value |
|---|---|
| `DJANGO_SECRET_KEY` | long random string |
| `DATABASE_URL` | your Neon URL (already used in dev) |
| `OPENAI_API_KEY` | your key |
| `OPENAI_MODEL` | `gpt-4o-mini` (low latency) |
| `VAPI_API_KEY` | Vapi **private** key |
| `VAPI_WEBHOOK_SECRET` | the shared secret |
| `NEXT_PUBLIC_VAPI_PUBLIC_KEY` | Vapi **public** key (baked into frontend build) |
| `NEXT_PUBLIC_VAPI_ASSISTANT_ID` | Mary's assistant id |
| `NEXT_PUBLIC_BOOKING_URL` | your Google Calendar / Calendly link |
| `API_DOMAIN` | `api.workflowauth.com` |
| `APP_DOMAIN` | `app.workflowauth.com` |
| `FRONTEND_ORIGIN` | `https://workflowauth.com,https://app.workflowauth.com` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | same as FRONTEND_ORIGIN |

> Prod overrides `DJANGO_ALLOWED_HOSTS` to `${API_DOMAIN},backend,localhost,127.0.0.1`,
> so the dev `.trycloudflare.com` entry isn't needed in production.

## 4. Build + run
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
This runs migrations + collectstatic + gunicorn (gthread), the Next.js frontend
(with the Vapi keys baked in), and Caddy (auto-HTTPS).

## 5. Verify
```bash
curl https://api.workflowauth.com/api/health/            # -> 200
# Business already on OpenAI (shared Neon DB). Confirm:
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py shell -c "from apps.core.models import Business; print([(b.name,b.llm_provider) for b in Business.objects.all()])"
```
If any business isn't `openai`:
```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py shell -c "from apps.core.models import Business; Business.objects.update(llm_provider='openai')"
```

## 6. Point Vapi at production (and drop the dev tunnel)
```bash
scripts/repoint-vapi.sh https://api.workflowauth.com
```
This sets the assistant's `model.url` to `…/api/calls/vapi/k/<secret>` and the
`server.url` webhook. Then stop the local dev tunnel: `docker rm -f wf-tunnel`.

## 7. Test
Open `https://app.workflowauth.com` (or your marketing domain) → "Hear Mary pick
up" → "Talk to Mary live" → allow mic. Turns should now be sub-second and smooth.

---

### Tuning already applied (in the repo)
- `OPENAI_MODEL=gpt-4o-mini` (env-overridable in `openai_loop.py`)
- Vapi assistant: Deepgram `nova-2` STT, 11Labs `eleven_turbo_v2_5` voice, tightened endpointing
- Caddy streams the custom-LLM SSE (`flush_interval -1`); gunicorn uses gthread workers

### Optional post-deploy polish
True token-by-token streaming from OpenAI (today the endpoint streams an
already-complete response). Worth doing once deployed, where it's testable and
not buffered by the dev tunnel — say the word and I'll implement it.
