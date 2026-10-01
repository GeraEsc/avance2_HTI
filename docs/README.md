# Foro y Reseñas — avance2_HTI

> Proyecto del Reto - LSCA2314 - Periodo AD26  
> Alumno: Gerardo Emilio Escamilla Cerda  
> Matricula: AL07001821  
> Tema elegido: 4 - Foro y reseñas

## Que hace esta aplicacion

Es una aplicacion web de foro y reseñas donde los usuarios pueden registrarse,
iniciar sesion, crear hilos de discusion, publicar comentarios y calificar hilos.

La aplicacion incluye una interfaz web completa y un sistema de moderacion
independiente. Cada comentario pasa por el servicio `moderador` antes de
publicarse. Este servicio valida reglas de longitud y palabras prohibidas.

Los comentarios rechazados quedan registrados en Amazon S3 con el motivo del rechazo.

Ademas, la aplicacion incorpora:

- roles de usuario y administrador;
- eliminacion de comentarios propios;
- panel administrativo;
- aprobacion y rechazo manual de comentarios;
- eliminacion de comentarios e hilos por administrador;
- calificaciones acumulativas por hilo;
- vista previa de reseñas con formato enriquecido;
- remediacion de una vulnerabilidad XSS.

## Como se levanta

```bash
cp .env.ejemplo .env
docker compose up -d --build
```

La aplicacion queda disponible en `http://localhost:5000`.

El endpoint de salud responde en `/salud`.

En AWS se accede usando la IP publica de la instancia EC2 correspondiente.

## Arquitectura

La aplicacion se compone de dos servicios propios en contenedores separados,
orquestados con Docker Compose.

### api

Backend principal en Flask.

Responsabilidades:

- renderiza el frontend web;
- registro e inicio de sesion;
- manejo de roles;
- creacion y listado de hilos;
- publicacion de comentarios;
- calificaciones;
- comunicacion con PostgreSQL RDS;
- comunicacion con el servicio de moderacion;
- almacenamiento de registros de comentarios rechazados en S3.

Archivo principal: `app/api/main.py`.

### moderador

Servicio Flask independiente dedicado a moderar contenido.

Responsabilidades:

- validar longitud del texto;
- detectar palabras prohibidas;
- aprobar o rechazar comentarios;
- generar la vista previa enriquecida;
- neutralizar HTML proporcionado por el usuario.

Archivos principales:

- `app/moderador/main.py`
- `app/moderador/vista_previa_resena.py`

## Servicios de AWS

| Servicio | Uso | Seguridad |
|---|---|---|
| EC2 | Ejecutar QA y Produccion | Security Groups con puertos controlados |
| RDS PostgreSQL | Usuarios, hilos, comentarios y calificaciones | Sin acceso publico, cifrado y SSL |
| S3 | Registro de comentarios rechazados | Acceso publico bloqueado y cifrado |
| IAM | Permisos de acceso a servicios AWS | Politicas asociadas a los recursos |

## Ambientes

El proyecto utiliza ambientes separados de QA y Produccion.

Flujo utilizado:

`Desarrollo -> QA -> Pipeline -> Produccion`

## Roles y permisos

### Usuario

Puede:

- crear hilos;
- publicar comentarios;
- calificar hilos;
- eliminar sus propios comentarios;
- utilizar la vista previa enriquecida.

### Administrador

Puede:

- realizar las acciones de un usuario;
- acceder al Panel Admin;
- ver comentarios aprobados y rechazados;
- aprobar o rechazar comentarios;
- eliminar cualquier comentario;
- eliminar hilos.

## Calificaciones

Cada usuario puede tener una sola calificacion por hilo.

La combinacion `hilo_id + usuario_id` es unica. Si el usuario vuelve a votar,
se actualiza su propia calificacion y no se crea un voto adicional.

La interfaz muestra el promedio general, el total de calificaciones y el voto personal.

## Funcionalidad nueva del parche

Tema asignado: **Foro y reseñas - Vista previa con formato enriquecido**.

La vista previa permite escribir contenido como `**texto**` y mostrarlo en negritas,
ademas de conservar saltos de linea.

## Hallazgo de seguridad: XSS

Durante la validacion del parche se detecto un riesgo de Cross-Site Scripting (XSS)
por el tratamiento inseguro de contenido proporcionado por el usuario.

Ejemplo de entrada peligrosa:

`<img src=x onerror=alert(1)>`

La remediacion implementada:

- escapa primero el contenido proporcionado por el usuario;
- aplica solamente el formato enriquecido permitido;
- elimina el uso inseguro de `|safe`;
- conserva la funcionalidad legitima.

Despues de la remediacion, la entrada peligrosa se muestra como texto y no ejecuta JavaScript.

## Pipeline de seguridad

El pipeline se ejecuta con:

`./pipeline/run_pipeline.sh`

Incluye cinco etapas:

1. **Gitleaks**: detecta secretos y bloquea si encuentra cualquiera.
2. **pip-audit**: detecta vulnerabilidades conocidas en dependencias Python.
3. **Hadolint**: revisa buenas practicas en Dockerfiles.
4. **Semgrep**: analiza estaticamente el codigo y detecta patrones inseguros como `|safe`.
5. **Trivy**: revisa la infraestructura como codigo y bloquea hallazgos CRITICAL.

El resultado final es `BLOQUEADO` o `PERMITIDO`.

La version remediada termino con `VEREDICTO FINAL: PERMITIDO`.

## Endpoints principales

### Sistema
- `GET /`
- `GET /salud`
- `POST /vista-previa`

### Usuarios
- `POST /registro`
- `POST /login`

### Hilos
- `GET /hilos`
- `POST /hilos`

### Comentarios
- `GET /hilos/<hilo_id>/comentarios`
- `POST /hilos/<hilo_id>/comentarios`
- `DELETE /comentarios/<comentario_id>`

### Calificaciones
- `GET /hilos/<hilo_id>/calificaciones`
- `POST /hilos/<hilo_id>/calificaciones`

### Administracion
- `GET /admin/comentarios`
- `PATCH /admin/comentarios/<comentario_id>/estado`
- `DELETE /admin/hilos/<hilo_id>`

## Evidencias

Archivos principales:

- `docs/clasificacion_hallazgo.md`
- `docs/respuesta_incidente.md`
- `docs/evidencia_produccion.md`
- `docs/declaracion_ia.md`
- `reportes/pipeline_bloqueado.txt`
- `reportes/pipeline_verde.txt`

## Variables de entorno

La configuracion sensible se carga desde `.env` y no se incluye en Git.

Variables principales:

- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `AWS_REGION`
- `S3_BUCKET`

## Estado actual

| Componente | Estado |
|---|---|
| Frontend web | OK |
| Backend Flask | OK |
| Servicio moderador | OK |
| PostgreSQL RDS | OK |
| Amazon S3 | OK |
| Roles usuario/admin | OK |
| Panel administrativo | OK |
| Calificaciones acumulativas | OK |
| Vista previa enriquecida | OK |
| Remediacion XSS | OK |
| Pipeline de 5 etapas | OK |
| QA | Validado |
| Produccion | Desplegado |
