# Evidencia de Produccion

La version desplegada en Produccion corresponde al codigo remediado que
previamente paso el pipeline de QA en estado verde.

## Instancia

Nombre: EntregaFinal-Produccion

## Commit desplegado

f59cc51

## Verificaciones realizadas

- Los contenedores api y moderador quedaron en estado healthy.
- El endpoint /salud respondio HTTP 200.
- La instancia de Produccion pudo conectarse a RDS por SSL.
- La funcionalidad de vista previa de resenas se mantuvo operativa.
- El formato enriquecido legitimo siguio funcionando.
- El contenido HTML proporcionado por el usuario se muestra escapado.
- La version vulnerable nunca fue desplegada directamente en Produccion.

## Prueba funcional

Entrada legitima:

Resena **segura** en Produccion

Resultado:

Resena <b>segura</b> en Produccion

## Prueba de remediacion XSS

Entrada:

<img src=x onerror=alert(1)>

Resultado:

&lt;img src=x onerror=alert(1)&gt;

Esto confirma que el HTML proporcionado por el usuario ya no es
interpretado como contenido ejecutable.
