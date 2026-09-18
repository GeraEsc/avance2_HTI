# Declaracion de uso de inteligencia artificial

Las Notas de Ensenanza del curso permiten usar IA como apoyo, no como
sustituto. Esta declaracion es obligatoria y forma parte de la entrega.

## Que genere con ayuda de IA

| Parte del proyecto | Herramienta de IA | Que le pedi | Que cambie yo despues |
|---|---|---|---|
| Backend Flask (`app/api/main.py`) | Claude | Codigo base de los endpoints de registro, login, hilos, comentarios y calificaciones, con conexion a RDS y S3 | Nada en la logica; corregi errores de configuracion (SSL, contraseña) que no eran del codigo en si sino de la conexion a AWS |
| Servicio de moderacion (`app/moderador/main.py`) | Claude | Logica de moderacion basica: lista de palabras prohibidas, validacion de longitud | Ninguno, se uso tal cual para este avance |
| Dockerfiles endurecidos | Claude | Estructura con version fija de imagen, usuario no-root, HEALTHCHECK | Ninguno |
| Script del pipeline (`pipeline/run_pipeline.sh`) | Claude | Consolidar 3 controles (gitleaks, pip-audit, hadolint) en un solo veredicto bloquea/permite | Ninguno en la logica; yo ejecute las corridas y remedie los hallazgos reales manualmente |
| Configuracion de infraestructura (Terraform, `infra/main.tf`) | Claude | Describir mi bucket S3 y mi instancia RDS ya existentes | Ninguno |

## Que hice sin IA

Cree y configure los recursos reales de AWS (S3 y RDS) directamente en la
consola web, incluyendo resolver los errores de permisos con Aurora (bloqueado
por politica de AWS Academy) y ajustar los security groups para que mi
instancia EC2 pudiera conectarse a RDS. Tambien corri todas las pruebas
manuales de la aplicacion (registro, login, creacion de hilos, comentarios) y
verifique con mis propios ojos cada resultado antes de darlo por bueno.

## Algo que la IA me dio mal y tuve que corregir

El codigo inicial que me genero la IA para conectar a la base de datos no
incluia `sslmode="require"` en la conexion de psycopg2. RDS en AWS Academy
exige conexion cifrada por defecto, asi que la primera vez que intente
levantar la aplicacion, fallo con un error de "no encryption" en los logs.
Tuve que pedirle a la IA que ajustara la funcion de conexion para forzar SSL,
y despues de eso funciono. Ademas, las versiones de las librerias que la IA
puso originalmente en `requirements.txt` (Flask 3.0.3, requests 2.32.3)
resultaron tener vulnerabilidades conocidas (CVEs) que mi propio pipeline
detecto al correrlo por primera vez — tuve que actualizarlas manualmente a
versiones mas nuevas para que el pipeline dejara de bloquear.
