# [NOMBRE DE TU APLICACION]

> Avance 2 del Reto - LSCA2314 - Periodo AD26
> Alumno: [COMPLETAR]   |   Matricula: [COMPLETAR]   |   Tema elegido: [COMPLETAR]

## Que hace esta aplicacion

[COMPLETAR: dos o tres frases. Que problema resuelve y para quien.]

## Como se levanta

```bash
cp .env.ejemplo .env     # y llena tus valores
docker compose up --build
```

La aplicacion queda en http://localhost:[COMPLETAR] y su endpoint de salud
responde en /salud.

## Arquitectura

[COMPLETAR: describe en un parrafo como se comunican tus servicios.]

Ver el diagrama en `docs/diagrama_arquitectura.png`.

## Servicios de AWS que usa

| Servicio | Para que lo uso | Como lo asegure |
|---|---|---|
| S3 | [COMPLETAR] | [COMPLETAR: cifrado, bloqueo de acceso publico] |
| RDS | [COMPLETAR] | [COMPLETAR: cifrado, sin acceso publico, grupo de seguridad] |

## Requisitos minimos del tema

| Requisito de mi tema | Donde se cumple |
|---|---|
| [COMPLETAR] | [COMPLETAR] |

## Como se corre el pipeline

```bash
[COMPLETAR: el comando que corre tu pipeline]
```
