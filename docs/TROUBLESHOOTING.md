# Troubleshooting

## Connection refused on http://localhost:8000/

Nothing is listening on port 8000 on the computer where the browser is running.

### Browser on another computer, app on this machine

`localhost` on the other computer is that computer, not this one.

```bash
make start
make urls
```

Open the LAN address `make urls` prints, for example `http://192.168.0.198:8000/`.

### Browser on this machine

```bash
make start
make status
```

`sauna-django` must be **Up**. Then open http://localhost:8000/.

### Checks

```bash
make status
curl -sI http://127.0.0.1:8000/
docker logs sauna-django --tail 30
```

| Result | What to do |
|--------|------------|
| `sauna-django` is missing or not Up | `make start` |
| `curl` returns 200 | Use the URL from `make urls` |
| `curl` fails | Read `docker logs sauna-django` |

## Admin login fails

Username and password are `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` in `.env`.

```bash
make reset_admin
```

Then open http://localhost:8000/admin/. Details: [DJANGO_ADMIN.md](DJANGO_ADMIN.md).

If the login page is unstyled or returns **403 Forbidden**, rebuild:

```bash
make stop
make start
```

Use one hostname for the whole session. Mixing `localhost` and the LAN IP can trip Django's CSRF check.

## HTTP 400 Disallowed Host

With `DJANGO_DEBUG=1`, any host is allowed after a rebuild. For a locked-down host, set `DJANGO_DEBUG=0` and put the hostname in `DJANGO_ALLOWED_HOSTS`, then rebuild.

## pgAdmin

pgAdmin is optional and slow to start. Wait until `cd pgadmin && make start` prints that it is ready. See [PGADMIN.md](PGADMIN.md).
