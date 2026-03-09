# Codex Agent Monitor

Codex-only fleet monitor MVP for endpoint, server, and cloud discovery. It keeps three trust levels in the data model:

- `confirmed`: strong local evidence such as known Codex CLI or app signatures
- `observed`: workspace-side evidence without local confirmation
- `suspected`: heuristic detections that still need review

## Run

```powershell
npm run seed
npm start
```

Open [http://localhost:3000](http://localhost:3000).

## Test

```powershell
npm test
```

## Endpoints

- `/api/health`
- `/api/dashboard`
- `/api/sample-db`

## Sample data

The seed script writes `data/monitor.db` and includes:

- 3 hosts
- 4 agent instances
- 4 discovery events
- 4 heartbeat snapshots
- 4 jobs
- 3 workspace observations
