# Deploying CrimeSense on Catalyst by Zoho (AppSail)

> Deployment **must** be on Catalyst to qualify for Datathon 2026 evaluation.
> Two routes below. Try **Route A** (managed Python runtime) first; if Streamlit's
> WebSocket doesn't load behind the gateway, use **Route B** (Docker custom runtime),
> which is the most reliable for Streamlit.

---

## 0. One-time setup

1. Create a free account at https://catalyst.zoho.com and create a **project**
   (e.g. `CrimeSense`). Note the project from the console.
2. Install Node.js (18+), then the Catalyst CLI:
   ```bash
   npm install -g zcatalyst-cli
   catalyst --version
   ```
3. Log in (opens a browser):
   ```bash
   catalyst login
   ```

---

## Route A — Catalyst-Managed Python Runtime (try first)

From the repo root (`E:/Datathon-2026-by-the-Karnataka-State-Police`):

```bash
catalyst init
```
Answer the prompts:
- Associate with the **CrimeSense** project you created.
- Component to initialise: **AppSail**.
- Runtime type: **Catalyst-Managed Runtime**.
- Start from a sample app? **N** (use your own).
- Is this the source directory? **Y**.
- App name: `crimesense-web`.
- Build path: the repo root (the folder containing `app/`, `requirements.txt`).
- Stack: **Python** (choose 3.11 if offered).

This creates / updates `app-config.json`. Make sure its `command` is the Streamlit
start command (already set in this repo):

```json
{
  "command": "streamlit run app/app.py --server.port $X_ZOHO_CATALYST_LISTEN_PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --browser.gatherUsageStats false",
  "stack": "python3.11",
  "name": "crimesense-web",
  "memory": 512
}
```

> Catalyst injects the port to bind to via the env var **`X_ZOHO_CATALYST_LISTEN_PORT`** —
> the app must listen on `0.0.0.0` and that port (the command above already does).

Generate the database once locally so it ships with the build, then deploy:
```bash
python data/generate_data.py
catalyst deploy
```
The CLI prints the live endpoint URL when done — that is your **Deployed Link**.

If the page loads but the app body stays blank / "Please wait…", it's the Streamlit
WebSocket being blocked — switch to Route B.

---

## Route B — Docker custom runtime (most reliable for Streamlit)

A `Dockerfile` is already included in this repo. It installs deps, builds the DB, and
runs Streamlit on the injected port.

```bash
# from the repo root
catalyst login                # if not already
catalyst deploy appsail
```
When prompted, choose **Docker Image / Custom Runtime** as the runtime type and point
it at the `Dockerfile` in this directory. Catalyst builds the image and deploys it;
the CLI prints the endpoint URL.

(You can also build/push the image yourself to Catalyst's container registry and
deploy from the **Console → AppSail → Deployments**; see the Catalyst docs link below.)

---

## 3. After deploying

- Open the printed URL in an **incognito** window to confirm it's public and working.
- Paste that URL into **slide 13** of the submission deck (Deployed Link) and into the
  Hack2skill submission form.
- Optional production hardening: move the crime data from bundled SQLite into
  **Catalyst Data Store**, add **Catalyst Authentication** for the role-based access,
  and build the forecasting model in **QuickML**.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `catalyst: command not found` | Re-run `npm install -g zcatalyst-cli`; ensure npm global bin is on PATH. |
| Build fails on a package | Pin/trim `requirements.txt`; ensure `reportlab`, `matplotlib` install on the chosen stack. Route B avoids this. |
| Page blank / websocket error | Use Route B (Docker). Keep `--server.enableCORS false --server.enableXsrfProtection false`. |
| App can't find DB | Ensure `python data/generate_data.py` ran before deploy (Route A) or is in the Dockerfile (Route B, already included). |
| Port error | Don't hard-code a port — always use `$X_ZOHO_CATALYST_LISTEN_PORT`. |

## Docs
- AppSail — deploy from CLI: https://docs.catalyst.zoho.com/en/serverless/help/appsail/catalyst-managed-runtimes/deploy-from-cli/
- AppSail Python guide: https://docs.catalyst.zoho.com/en/serverless/help/appsail/help-guides/python/overview/
- Custom runtime (Docker) from CLI: https://docs.catalyst.zoho.com/en/serverless/help/appsail/custom-runtimes/deploy-from-cli/
- CLI reference: https://docs.catalyst.zoho.com/en/cli/v1/cli-command-reference/
