# Clasificacion del hallazgo

## Hallazgo

La nueva funcionalidad de vista previa de resenas agrega el endpoint:

POST /moderacion/resenas/<resena_id>/vista-previa

El endpoint recibe el parametro `contenido` proporcionado por el usuario
mediante `request.form`.

Posteriormente el contenido es procesado por
`formatear_texto_enriquecido()` y enviado a una plantilla Jinja.

La plantilla utilizaba:

{{ contenido_formateado | safe }}

El filtro `safe` evita el escape automatico de Jinja. Como consecuencia,
contenido HTML controlado por el usuario podia incorporarse a la respuesta
sin ser neutralizado.

## Tipo de vulnerabilidad

Cross-Site Scripting (XSS).

CWE-79: Improper Neutralization of Input During Web Page Generation.

## Severidad

Alta.

La funcionalidad esta disenada para mostrar a un moderador contenido
procedente de una resena. Un usuario podria proporcionar contenido HTML
malicioso que seria interpretado por el navegador al generar la vista
previa.

La explotacion requiere que el contenido malicioso llegue a la vista
previa del moderador, pero no requiere modificar el servidor ni el codigo
de la aplicacion.

## Falso positivo

No se considero un falso positivo.

Semgrep detecto el uso de `|safe` en contenido que procede de una entrada
del usuario. Ademas, la prueba manual confirmo que una etiqueta HTML
proporcionada mediante el parametro `contenido` aparecia en la respuesta
sin escapar.

Por lo tanto, existe un flujo real entre una entrada no confiable y HTML
marcado como seguro.
