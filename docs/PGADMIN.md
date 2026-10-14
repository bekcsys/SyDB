# pgAdmin

pgAdmin is an optional SQL browser. It is not started by `make start`.

Full steps: [../pgadmin/README.md](../pgadmin/README.md).

```bash
make start

cd pgadmin
make start
```

- On this machine: http://localhost:5050/
- Login: `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` in `.env`

Django admin (http://localhost:8000/admin/) is the place to edit products and QC records. pgAdmin is for SQL.
