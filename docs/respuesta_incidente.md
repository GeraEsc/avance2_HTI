# Respuesta al incidente

## Contencion inmediata

La version vulnerable se mantuvo exclusivamente en el ambiente de QA.

El pipeline de seguridad detecto el hallazgo mediante Semgrep y termino
con VEREDICTO FINAL: BLOQUEADO, evitando que esta version fuera promovida
a Produccion.

En un sistema real, mientras se desarrolla la correccion, tambien se
podria deshabilitar temporalmente el endpoint mediante una bandera de
configuracion.

La contencion limita la exposicion, pero no elimina la causa raiz.

## Prevencion y remediacion

La causa raiz fue confiar en contenido procedente del usuario y
deshabilitar el escape automatico de Jinja mediante el filtro `|safe`.

La remediacion consiste en escapar primero todo contenido proporcionado
por el usuario y permitir solamente el HTML que la propia aplicacion
genera de forma controlada para la funcionalidad de texto enriquecido.

Adicionalmente, se incorporo Semgrep como etapa SAST del pipeline para
detectar este patron inseguro antes de futuros despliegues.

Tambien se incorporo Trivy para analizar la infraestructura como codigo.
