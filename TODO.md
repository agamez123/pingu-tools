# TODO

- [ ] **Tests + CI** — Add a pytest suite covering URL creation, redirect, update, and delete. Wire up a GitHub Actions workflow to run tests on every push/PR.
- [ ] **Auth** — Add per-user short links (API keys or JWT-based auth) so URLs are scoped to an owner instead of globally shared.
- [ ] **Deploy** — Write a Dockerfile for the app itself (Postgres is already containerized), then deploy to Render/Fly.io/Railway with a live URL, and document the setup in the README.
