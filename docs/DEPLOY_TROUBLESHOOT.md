### Deploy troubleshooting (prod shows stale version)

#### Symptom
- dohodometr.ru serves an old UI version or ignores new deploys

#### Quick checks (curl)
- HTML response headers:
```
curl -I https://dohodometr.ru
```
Expect to see:
- Cache-Control: no-store (for HTML)
- Vary and server headers depending on hosting

- Bypass caches by adding a timestamp:
```
curl -I "https://dohodometr.ru/?v=$(date +%s)"
```

#### See current deployed build
- JSON: `https://dohodometr.ru/version.json`
- Inline/overlay in UI: add `?debug=1` to any page to show a floating build stamp

#### Purge cache / force refresh
- Vercel: Purge project cache and Redeploy Production from dashboard
- Cloudflare: Cache → Purge → Purge Everything, then hard refresh in browser
- Nginx (self-hosted with Traefik): no CDN cache by default; ensure headers below are set

#### Where prod is hosted
- This repo contains `deployment/docker-compose.production.yml` with Traefik routing `dohodometr.ru` to the Next.js container. Confirm this is the active prod host. If you use Vercel/Netlify instead, keep the Next.js headers in `next.config.js` and use provider console to purge.

#### Cache headers policy
- HTML: `Cache-Control: no-store`
- Next static assets: `Cache-Control: public, max-age=31536000, immutable`

##### Next.js config
Defined in `frontend/next.config.js` via `async headers()`.

##### Nginx include (if used)
Create `ops/nginx/cache.conf` and include it in your server block:
```
location ~* \.html$ { add_header Cache-Control "no-store"; }
location /_next/static/ { add_header Cache-Control "public, max-age=31536000, immutable"; }
```

#### Service Worker stuck?
If a service worker exists and is outdated:
- In browser console run:
```
navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>r.unregister()))
```
- Ensure SW calls `self.skipWaiting()` and `self.clients.claim()` on activate

#### CI/CD build passport in logs
During deploy, print build info:
- Using version.json (jq):
```
echo "Deploying $(jq -r .commit frontend/public/version.json) at $(jq -r .date frontend/public/version.json)"
```
- Fallback:
```
echo "Deploying $(git rev-parse --short HEAD) at $(date -u +\"%Y-%m-%dT%H:%M:%SZ\")"
```

