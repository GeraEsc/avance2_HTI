# Foro y Reseñas — avance2_HTI

> Avance 2 del Reto - LSCA2314 - Periodo AD26
> Alumno: Gerardo Emilio Escamilla Cerda   |   Matricula: AL07001821   |   Tema elegido: 4 - Foro y reseñas

## Que hace esta aplicacion

Es un foro donde los usuarios se registran, inician sesion, crean hilos de discusion,
comentan y califican esos hilos. Cada comentario pasa por un servicio de moderacion
independiente antes de publicarse, que revisa palabras prohibidas y longitud del texto.
Los comentarios rechazados quedan registrados en S3 con el motivo del rechazo.

## Como se levanta

```bash
cp .env.ejemplo .env     # y llena tus valores reales de RDS y S3
docker compose up --build
```

La aplicacion queda en http://localhost:5000 y su endpoint de salud
responde en /salud.

## Arquitectura

La aplicacion se compone de dos servicios en contenedores separados, orquestados
con docker-compose:

- **api**: backend en Flask que expone los endpoints de registro, login, hilos,
  comentarios y calificaciones. Guarda todos los datos en una base RDS PostgreSQL
  real. Cuando llega un comentario nuevo, llama por HTTP interno al servicio
  `moderador` antes de guardarlo como aprobado o rechazado.
- **moderador**: servicio Flask independiente que solo recibe texto y regresa un
  veredicto (aprobado/rechazado) segun reglas de longitud y palabras prohibidas.

Cuando un comentario es rechazado, `api` sube un registro JSON con el motivo a un
bucket S3 privado y cifrado, dejando rastro de la moderacion.

Ver el diagrama en `docs/diagrama_arquitectura.png`.

## Servicios de AWS que usa

| Servicio | Para que lo uso | Como lo asegure |
|---|---|---|
| S3 | Guardar el registro (log) de comentarios rechazados por moderacion | Bloqueo total de acceso publico activado, cifrado SSE-S3 activado |
| RDS | Guardar usuarios, hilos, comentarios y calificaciones | Sin acceso publico (`publicly_accessible=false`), cifrado de almacenamiento activado, conexion via SSL (`sslmode=require`), alcanzable solo desde el security group de mi instancia EC2 |

## Requisitos minimos del tema

| Requisito de mi tema | Donde se cumple |
|---|---|
| Backend en Python | Flask, en `app/api/main.py` |
| Al menos 2 contenedores propios | `api` y `moderador`, definidos en `docker-compose.yml` |
| Pieza distintiva: servicio de moderacion | `app/moderador/main.py`, llamado por `api` via HTTP interno en cada comentario nuevo |
| Bucket S3 real, privado y cifrado, usado de verdad | `avance2-hti-gescamilla`, recibe los logs de comentarios rechazados |
| RDS real, cifrada, sin acceso publico | `avance2-hti-db`, PostgreSQL 17 |
| Registro e inicio de sesion | Endpoints `/registro` y `/login` en `app/api/main.py` |
| Endpoint /salud | Implementado en ambos servicios (`api` y `moderador`) |

## Como se corre el pipeline

```bash
./pipeline/run_pipeline.sh
```

Corre tres etapas (escaneo de secretos, analisis de dependencias, lint de
Dockerfile) y termina en un solo veredicto: BLOQUEADO o PERMITIDO. Los reportes
de las corridas en rojo y verde estan en `reportes/corrida_roja.txt` y
`reportes/corrida_verde.txt`.
