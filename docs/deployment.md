# Deployment

Edgebook ships as a small Docker stack (FastAPI app + Postgres + a one-shot
migration) designed to run on a single Always-Free VM. This guide targets
**Oracle Cloud Always Free** (Ampere A1 ARM) for a true $0 deployment, with a
clear paid scale-up path.

The ingestion scheduler is run by **host cron** as a one-shot
(`scripts/cron_ingest.sh`), not as a long-running container.

## Architecture on the VM

```
Internet ──> :80 (app, uvicorn) ──> FastAPI
                   │
                   ├── db (postgres:16) ── pgdata volume
                   └── migrate (one-shot alembic upgrade head on deploy)

host cron ──> docker compose run --rm app python -m edgebook.ingestion.cli sync
host cron ──> scripts/backup_db.sh
```

All base images (`python:3.11-slim`, `postgres:16-alpine`) ship **arm64**
builds, and `psycopg2-binary` provides arm64 wheels, so the stack runs natively
on Ampere A1 with no cross-compilation.

## 1. Provision the Always-Free VM

1. Create an Oracle Cloud account (requires a card on file, but the A1 shapes
   are free within the Always-Free quota).
2. **Compute → Create instance:**
   - **Shape:** `VM.Standard.A1.Flex` (Ampere ARM). 1–2 OCPU and 4–8 GB RAM is
     plenty for this stack and stays within the free quota (4 OCPU / 24 GB).
   - **Image:** Canonical Ubuntu 24.04 (or 22.04).
   - **SSH keys:** generate or paste your public key; save the private key.
3. **Reserve a public IP** and note it (`VM_PUBLIC_IP`).
4. Wait for the instance to be `RUNNING`.

> **Region capacity:** A1 shapes are sometimes capacity-constrained in popular
> regions. If creation fails, retry or pick a less-busy region — the quota
> resets within minutes.

## 2. Open firewall ports

Traffic must be allowed in **two** places:

1. **Oracle VCN → Security List / NSG:** add ingress rules for TCP **22**
   (SSH, restrict to your IP if possible), **80** (HTTP), and optionally
   **443** (for the later HTTPS step).
2. **On the VM (iptables):** Ubuntu images on Oracle ship with restrictive
   iptables rules. Allow 80 (and 443 later):
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo netfilter-persistent save
   ```

## 3. Install Docker on the VM

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER   # then log out/in
```

## 4. Deploy the stack

```bash
sudo mkdir -p /opt/edgebook && sudo chown $USER /opt/edgebook
cd /opt/edgebook
git clone <your-repo-url> .

# Configure production secrets (never commit this file):
cp .env.example .env
# Generate a strong SECRET_KEY:
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into .env
$EDITOR .env   # set SECRET_KEY, POSTGRES_PASSWORD, ODDS_API_KEY, ALERT_WEBHOOK_URL

docker compose -f docker-compose.prod.yml up -d --build
```

`.env` must set at least:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | A strong random key (≥ 32 chars); the app refuses to start otherwise. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | DB credentials. |
| `ODDS_API_KEY` | Provider key (leave empty to defer live ingestion). |
| `ALERT_WEBHOOK_URL` | Optional; failure webhook (see runbook → Ingestion Alerting). |
| `SESSION_COOKIE_SECURE` | `false` for the HTTP interim; set `true` once HTTPS is added. |

## 5. Verify

```bash
curl --fail http://VM_PUBLIC_IP/healthz     # {"status":"alive"}
curl --fail http://VM_PUBLIC_IP/readyz      # {"status":"ok","database":"ok"}
```

The `migrate` one-shot runs `alembic upgrade head` before the app starts, so the
schema is current on first boot. Create your first admin from the VM:

```bash
docker compose -f docker-compose.prod.yml run --rm --no-deps app \
    python -m edgebook.auth.cli create admin 'strong-password' --role ADMIN
```

## 6. Schedule ingestion + backups (cron)

Edit crontab (`crontab -e`) on the VM:

```cron
CRON_TZ=America/New_York

# Daily pregame odds sync at 08:00 ET
0 8 * * *  cd /opt/edgebook && ./scripts/cron_ingest.sh >> logs/ingest.log 2>&1

# Daily backup (see runbook → Backups)
15 8 * * *  cd /opt/edgebook && ./scripts/backup_db.sh >> logs/backup.log 2>&1
```

## 7. CI/CD on push to main

`.github/workflows/deploy.yml` SSHes into the VM on every push to `main`,
pulls, rebuilds, and restarts the stack — building natively on the ARM VM so no
registry or multi-arch build is required. Configure these **repository secrets**
(GitHub → Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|-------|
| `VM_HOST` | The VM public IP or hostname. |
| `VM_USER` | SSH user (usually `ubuntu`). |
| `SSH_PRIVATE_KEY` | The private key matching the VM's authorized key. |
| `DEPLOY_PATH` | `/opt/edgebook`. |

After the first manual deploy (step 4), subsequent pushes to `main` deploy
automatically.

## Add HTTPS later (when you have a domain)

The interim runs plain HTTP; because `SESSION_COOKIE_SECURE=false`, login works
but credentials traverse in cleartext. Before real use, add TLS:

1. Point an **A record** at `VM_PUBLIC_IP` and open port 443 (security list +
   iptables, as in step 2).
2. Add a reverse proxy that auto-provisions Let's Encrypt. Minimal Caddyfile:
   ```caddy
   edgebook.example.com {
       reverse_proxy app:8000
   }
   ```
   and run Caddy as a compose service on the same network (or on the host).
3. Set `SESSION_COOKIE_SECURE=true` in `/opt/edgebook/.env` and
   `docker compose -f docker-compose.prod.yml up -d`.

## Scale-up path

- **Bigger VM:** resize the A1 shape within the Always-Free quota (up to 4
  OCPU / 24 GB), or switch to a paid shape when you outgrow free.
- **Managed Postgres / object-storage backups / multi-region:** split the
  services out when the single-VM model is exhausted. The app is a modular
  monolith, so this is an operations change, not a re-write.
- **Registry-based deploys:** swap the SSH build-on-VM workflow for a GHCR
  image push when build time or rollbacks become a concern.

## ⚠ Always-Free caveats

- "Always free" holds while the account is in good standing; A1 instances left
  **idle** may be reclaimed by Oracle. Keep at least the cron + app active.
- Free shapes cannot exceed the quota without going paid.
- Backups (step 6) are essential — the Always-Free Postgres volume is not
  replicated.
