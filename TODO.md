# TODO

- [ ] **Tests + CI** — Add a pytest suite covering URL creation, redirect, update, and delete. Wire up a GitHub Actions workflow to run tests on every push/PR.
- [x] **Auth** — Per-user short links via session-cookie auth (signup/login/logout, bcrypt-hashed passwords, URLs scoped and ownership-checked per user).
- [ ] **Deploy** — Write a Dockerfile for the app itself (Postgres is already containerized), then deploy to Render/Fly.io/Railway with a live URL, and document the setup in the README.
