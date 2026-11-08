# WellowNet portfolio

## Requirements

- Node.js 18 or newer
- npm
- Writable persistent storage for `data/` and `uploads/`

## Run locally

```powershell
Copy-Item .env.example .env
```

Set `ADMIN_PASSWORD` in `.env` to a unique password with at least 12 characters, then run:

```powershell
npm ci
npm start
```

Open `http://localhost:3000`. The password is saved to `data/admin-password.txt` on first startup and can be changed through the gallery admin controls. Keep `.env` and `data/admin-password.txt` private.

## Deployment notes

Set `ADMIN_PASSWORD` in the hosting provider's environment settings for the first deployment. Keep `data/` and `uploads/` on persistent storage: the gallery index, admin password, and uploaded images are stored there. Copy the existing `data/gallery.json` and referenced upload images when migrating the current gallery.

This app stores sessions and gallery data locally, so deploy it as a single application instance with persistent disk. Use HTTPS at the hosting provider or reverse proxy. The `/health` endpoint can be used for a health check.
