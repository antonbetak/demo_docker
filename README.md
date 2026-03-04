# demo_dockers
Trabajo demo de Docker Compose para clase de sistemas distribuidos.
Anton Betak Licea

## Levantar el proyecto

```bash
docker compose up --build
```




### `GET /`
endpoint de bienvenida. Muestra mensaje y lista de rutas disponibles

### `GET /health`
valida que la app pueda conectarse a PostgreSQL y Redis,
regresa estado si si se pudo conectar o marca error

### `GET /visits`
muestra el contador de visitas al darle refresh a la página

### `POST /users`
crea un usuario en PostgreSQL


### `GET /users`
muestra los usuarios guardados en PostgreSQL y devuelve el total en count
