# ADR-001: Decisiones tecnicas de Foro y Reseñas (avance2_HTI)

Fecha: 2026-09-18
Estado: aceptada

## Contexto

Este proyecto se construyo en una sola sesion de trabajo, contra el tiempo de
entrega del mismo dia, usando una instancia EC2 del AWS Academy Learner Lab con
memoria limitada (t3.micro) y creditos acotados. Nunca antes habia desplegado
una aplicacion completa contra RDS y S3 reales desde cero, asi que prioricé
tener algo funcional de principio a fin sobre features adicionales.

## Decisiones

### 1. Framework del backend

**Elegi:** Flask
**Por que:** Es mas simple de levantar rapido para una API pequeña con pocos
endpoints, y tenia mas referencias previas de Flask que de FastAPI.
**Que descarte y por que:** FastAPI, porque su tipado con Pydantic agrega una
curva de aprendizaje que no me convenia dado el tiempo disponible, aunque
hubiera dado documentacion automatica de la API "gratis".

### 2. Separacion en servicios

**Elegi:** Dos contenedores: `api` (todos los endpoints, conexion a RDS y S3)
y `moderador` (revisa texto y regresa aprobado/rechazado, sin acceso a la base
de datos).
**Por que:** El requisito pide que la pieza distintiva de mi tema (moderacion)
sea un servicio separado, no una funcion dentro del mismo proceso. Ademas,
aislar el moderador significa que si en el futuro quiero cambiar sus reglas
o incluso su lenguaje, no toco la API principal.
**Que descarte y por que:** Meter la logica de moderacion como una funcion
dentro de `api/main.py`. Es mas simple de programar, pero no cumple el
requisito de que sea un servicio propio y separado, y mezclaria
responsabilidades distintas en un mismo contenedor.

### 3. Almacenamiento

**Elegi:** Todo el dato relacional (usuarios, hilos, comentarios,
calificaciones) va en RDS PostgreSQL. S3 solo guarda un registro JSON por
cada comentario rechazado por moderacion.
**Por que:** El dato transaccional del foro necesita consultas relacionales
(joins entre hilos y usuarios, por ejemplo), lo que encaja naturalmente en
una base SQL. S3 es mejor para objetos sueltos tipo log/evidencia, no para
datos que necesito consultar y actualizar constantemente.
**Que descarte y por que:** Guardar tambien los comentarios aprobados como
archivos en S3 ademas de RDS, para "usar mas" el bucket. Lo descarte porque
hubiera sido redundante y sin proposito real — el requisito pide un uso
genuino de S3, no un uso artificial solo para cumplir con la letra del
requisito.

## Consecuencias

Lo que se facilito: la separacion en dos contenedores resulto sencilla de
razonar y depurar por separado (revisar logs de `api` vs `moderador` por
separado ayudo mucho a diagnosticar problemas). Lo que se complico: la
conexion de la API a RDS tuvo dos tropiezos reales antes de funcionar —
primero un problema de seguridad de red (el security group de mi EC2 no
coincidia con el de RDS) y despues un problema de SSL (RDS exige conexion
cifrada y mi codigo inicial no la especificaba). Ambos se resolvieron, pero
me tomaron mas tiempo del que esperaba tener disponible para la parte de
infraestructura.
