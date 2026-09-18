# Tabla de decisiones de mi pipeline

Este documento justifica las decisiones de seguridad tomadas para el pipeline de mi aplicación de Foro y Reseñas.

## Riesgos que introduce mi aplicación

| # | Riesgo concreto de mi app | Qué control lo cubre | Por qué ese control |
|---|---|---|---|
| 1 | Mi aplicación usa credenciales de RDS y S3 mediante variables de entorno. Si una credencial se sube por error al repositorio, puede quedar expuesta y permitir acceso no autorizado a recursos de AWS. | Escaneo de secretos con gitleaks | Permite detectar credenciales, tokens o llaves que hayan sido colocadas accidentalmente en el código o archivos versionados. |
| 2 | El backend depende de librerías de terceros como Flask, requests, psycopg2 y boto3. Una versión vulnerable puede introducir un riesgo conocido en la aplicación. | Análisis de dependencias con pip-audit | Compara las dependencias instaladas contra bases de vulnerabilidades conocidas y permite detener el despliegue cuando existe un problema publicado. |
| 3 | La aplicación se ejecuta en contenedores. Un Dockerfile mal configurado podría ejecutar procesos como root, usar imágenes no fijadas o carecer de HEALTHCHECK. | Lint de Dockerfile con hadolint | Revisa automáticamente malas prácticas en la construcción de las imágenes y ayuda a mantener los contenedores con una configuración más segura. |
| 4 | Los usuarios pueden escribir texto libre en hilos y comentarios, por lo que pueden intentar publicar contenido ofensivo, spam o contenido que no cumpla las reglas del foro. | Servicio de moderación separado | Es un control de negocio de la aplicación que revisa el contenido antes de publicarlo y devuelve un resultado de aprobado o rechazado. |

## Mis etapas y sus umbrales

| Etapa | Herramienta | Qué revisa | Umbral que bloquea | Por qué ese umbral |
|---|---|---|---|---|
| Escaneo de secretos | gitleaks | Credenciales, tokens y llaves hardcodeadas o versionadas | Bloquea con cualquier secreto detectado | Una sola credencial real expuesta puede comprometer recursos de AWS, por lo que no considero aceptable permitir ningún secreto en el repositorio. |
| Análisis de dependencias | pip-audit | Vulnerabilidades conocidas en las dependencias Python de la aplicación | Bloquea cuando detecta una vulnerabilidad conocida | Si existe una vulnerabilidad publicada y hay una versión corregida disponible, prefiero remediarla antes de permitir el despliegue. |
| Lint de Dockerfile | hadolint | Buenas prácticas y problemas de seguridad/configuración en Dockerfiles | Bloquea ante errores configurados por la herramienta; los avisos de estilo no detienen el despliegue | Los errores pueden representar configuraciones inseguras, mientras que los warnings de estilo no siempre justifican detener una entrega. |

## Lo que decidí NO cubrir

| Riesgo que dejo fuera | Por qué lo dejo fuera | Qué haría si tuviera más tiempo |
|---|---|---|
| Análisis estático del código propio con Bandit | Priorizé primero secretos, dependencias y configuración de contenedores para terminar un pipeline funcional de principio a fin. | Agregaría Bandit como una etapa adicional para detectar patrones inseguros como uso de eval, exec o consultas SQL mal construidas. |
| Escaneo de vulnerabilidades de la imagen final de Docker con Trivy o Grype | Hadolint revisa el Dockerfile, pero no analiza todos los paquetes del sistema operativo contenidos en la imagen final. No agregué otra herramienta por tiempo. | Agregaría Trivy sobre cada imagen construida antes de permitir su despliegue. |
| Pruebas dinámicas o fuzzing de los endpoints | Este avance se concentró en controles del código, dependencias y contenedores. Las pruebas dinámicas requieren levantar un ambiente estable contra el cual ejecutar el análisis. | Agregaría OWASP ZAP contra un ambiente de QA para revisar los endpoints de la API antes de producción. |
