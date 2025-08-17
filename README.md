# BB

## Development with Docker

Build and start the application and PostgreSQL:

```bash
docker compose -f deploy/local.compose.yml up --build
```

The app is available at the default command `python main.py` and connects to the
`postgres` service via the `DATABASE_URL` environment variable.
