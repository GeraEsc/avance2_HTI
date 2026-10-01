let token = localStorage.getItem("token");
let usuario = localStorage.getItem("usuario");
let rol = localStorage.getItem("rol");
let usuarioId = localStorage.getItem("usuarioId");

let hilosCache = [];
let hiloActual = null;


document.addEventListener("DOMContentLoaded", () => {
    actualizarSesion();

    if (token && usuario) {
        mostrarSeccion("foro");
    } else {
        mostrarSeccion("acceso");
    }
});


function mostrarSeccion(id) {
    if (
        ["foro", "moderacion", "detalle", "admin"].includes(id)
        && !token
    ) {
        id = "acceso";
    }

    if (id === "admin" && rol !== "admin") {
        id = "foro";
    }

    document.querySelectorAll(".seccion")
        .forEach(seccion => seccion.classList.add("hidden"));

    const destino = document.getElementById(id);

    if (!destino) {
        console.error(`Seccion no encontrada: ${id}`);
        return;
    }

    destino.classList.remove("hidden");

    if (id === "foro") {
        cargarHilos();
    }

    if (id === "admin") {
        cargarAdminComentarios();
    }
}


function actualizarSesion() {
    const panel = document.getElementById("usuarioPanel");
    const btnAcceso = document.getElementById("btnAcceso");
    const btnNuevoHilo = document.getElementById("btnNuevoHilo");
    const nuevoComentario = document.getElementById("nuevoComentarioCard");

    const navForo = document.getElementById("navForo");
    const navModeracion = document.getElementById("navModeracion");
    const navAdmin = document.getElementById("navAdmin");

    if (token && usuario) {
        panel.classList.remove("hidden");

        document.getElementById("usuarioActual").textContent =
            rol === "admin"
                ? `${usuario} · Administrador`
                : usuario;

        btnAcceso.classList.add("hidden");
        navForo.classList.remove("hidden");
        navModeracion.classList.remove("hidden");
        btnNuevoHilo.classList.remove("hidden");

        if (rol === "admin") {
            navAdmin.classList.remove("hidden");
        } else {
            navAdmin.classList.add("hidden");
        }

        if (hiloActual) {
            nuevoComentario.classList.remove("hidden");
        } else {
            nuevoComentario.classList.add("hidden");
        }

    } else {
        panel.classList.add("hidden");

        btnAcceso.classList.remove("hidden");
        navForo.classList.add("hidden");
        navModeracion.classList.add("hidden");
        navAdmin.classList.add("hidden");
        btnNuevoHilo.classList.add("hidden");
        nuevoComentario.classList.add("hidden");
    }
}


async function registrar() {
    const nombre_usuario =
        document.getElementById("registroUsuario").value.trim();

    const email =
        document.getElementById("registroEmail").value.trim();

    const password =
        document.getElementById("registroPassword").value;

    const mensaje =
        document.getElementById("registroMensaje");

    try {
        const respuesta = await fetch("/registro", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre_usuario,
                email,
                password
            })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(datos.error || "No se pudo registrar");
        }

        mensaje.className = "mensaje ok";
        mensaje.textContent =
            "Cuenta creada. Ya puedes iniciar sesión.";

        document.getElementById("loginUsuario").value =
            nombre_usuario;

    } catch (error) {
        mensaje.className = "mensaje error";
        mensaje.textContent = error.message;
    }
}


async function login() {
    const nombre_usuario =
        document.getElementById("loginUsuario").value.trim();

    const password =
        document.getElementById("loginPassword").value;

    const mensaje =
        document.getElementById("loginMensaje");

    try {
        const respuesta = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre_usuario,
                password
            })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.error || "No fue posible iniciar sesión"
            );
        }

        token = datos.token;
        usuario = datos.usuario;
        rol = datos.rol;
        usuarioId = String(datos.id);

        localStorage.setItem("token", token);
        localStorage.setItem("usuario", usuario);
        localStorage.setItem("rol", rol);
        localStorage.setItem("usuarioId", usuarioId);

        mensaje.className = "mensaje ok";
        mensaje.textContent = "Sesión iniciada.";

        actualizarSesion();
        mostrarSeccion("foro");

    } catch (error) {
        mensaje.className = "mensaje error";
        mensaje.textContent = error.message;
    }
}


function cerrarSesion() {
    localStorage.removeItem("token");
    localStorage.removeItem("usuario");
    localStorage.removeItem("rol");
    localStorage.removeItem("usuarioId");

    token = null;
    usuario = null;
    rol = null;
    usuarioId = null;
    hiloActual = null;

    actualizarSesion();
    mostrarSeccion("acceso");
}


async function cargarHilos() {
    const contenedor =
        document.getElementById("listaHilos");

    try {
        const respuesta = await fetch("/hilos");

        if (!respuesta.ok) {
            throw new Error("No se pudieron cargar los hilos");
        }

        hilosCache = await respuesta.json();

        if (hilosCache.length === 0) {
            contenedor.innerHTML =
                '<div class="card">No hay hilos todavía.</div>';
            return;
        }

        contenedor.innerHTML = "";

        hilosCache.forEach(hilo => {
            const card = document.createElement("div");
            card.className = "hilo-card";

            const titulo = document.createElement("h3");
            titulo.textContent = hilo.titulo;

            const meta = document.createElement("div");
            meta.className = "meta";

            const autor = document.createElement("span");
            autor.textContent = `Autor: ${hilo.autor}`;

            const categoria = document.createElement("span");
            categoria.textContent =
                `Categoría: ${hilo.categoria || "General"}`;

            const fecha = document.createElement("span");
            fecha.textContent =
                new Date(hilo.fecha).toLocaleString();

            meta.append(autor, categoria, fecha);

            card.append(titulo, meta);

            if (rol === "admin") {
                const botonEliminar = document.createElement("button");

                botonEliminar.className = "btn-danger";
                botonEliminar.textContent = "Eliminar hilo";

                botonEliminar.onclick = async (evento) => {
                    evento.stopPropagation();
                    await eliminarHilo(hilo.id);
                };

                card.appendChild(botonEliminar);
            }

            card.addEventListener(
                "click",
                () => abrirHilo(hilo.id)
            );

            contenedor.appendChild(card);
        });

    } catch (error) {
        contenedor.innerHTML =
            `<div class="card">${error.message}</div>`;
    }
}


function alternarNuevoHilo() {
    document
        .getElementById("nuevoHiloCard")
        .classList.toggle("hidden");
}


async function crearHilo() {
    if (!token) {
        mostrarSeccion("acceso");
        return;
    }

    const titulo =
        document.getElementById("nuevoTitulo").value.trim();

    const categoria =
        document.getElementById("nuevaCategoria").value.trim();

    const mensaje =
        document.getElementById("nuevoHiloMensaje");

    try {
        const respuesta = await fetch("/hilos", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                titulo,
                categoria
            })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.error || "No se pudo crear el hilo"
            );
        }

        mensaje.className = "mensaje ok";
        mensaje.textContent = `Hilo creado con ID ${datos.id}.`;

        document.getElementById("nuevoTitulo").value = "";
        document.getElementById("nuevaCategoria").value = "";

        await cargarHilos();

    } catch (error) {
        mensaje.className = "mensaje error";
        mensaje.textContent = error.message;
    }
}


async function abrirHilo(id) {
    hiloActual = id;

    const hilo =
        hilosCache.find(item => item.id === id);

    if (!hilo) {
        return;
    }

    document.getElementById("detalleTitulo").textContent =
        hilo.titulo;

    document.getElementById("detalleAutor").textContent =
        `Autor: ${hilo.autor}`;

    document.getElementById("detalleCategoria").textContent =
        `Categoría: ${hilo.categoria || "General"}`;

    document.getElementById("detalleFecha").textContent =
        new Date(hilo.fecha).toLocaleString();

    mostrarSeccion("detalle");
    actualizarSesion();

    await cargarComentarios(id);
    await cargarCalificacion(id);
}


async function cargarComentarios(id) {
    const contenedor =
        document.getElementById("listaComentarios");

    try {
        const respuesta =
            await fetch(`/hilos/${id}/comentarios`);

        if (!respuesta.ok) {
            throw new Error(
                "No se pudieron cargar los comentarios"
            );
        }

        const comentarios = await respuesta.json();

        if (comentarios.length === 0) {
            contenedor.textContent =
                "Todavía no hay comentarios aprobados.";
            return;
        }

        contenedor.innerHTML = "";

        comentarios.forEach(comentario => {
            const div = document.createElement("div");
            div.className = "comentario";

            const texto = document.createElement("p");
            texto.textContent = comentario.texto;

            const meta = document.createElement("small");
            meta.textContent =
                `${comentario.autor} · ` +
                new Date(comentario.fecha).toLocaleString();

            div.append(texto, meta);

            const puedeEliminar =
                String(comentario.usuario_id) === String(usuarioId)
                || rol === "admin";

            if (puedeEliminar) {
                const botonEliminar = document.createElement("button");

                botonEliminar.className = "btn-danger";
                botonEliminar.textContent = "Eliminar";

                botonEliminar.onclick = () =>
                    eliminarComentario(comentario.id);

                div.appendChild(document.createElement("br"));
                div.appendChild(botonEliminar);
            }

            contenedor.appendChild(div);
        });

    } catch (error) {
        contenedor.textContent = error.message;
    }
}


async function publicarComentario() {
    if (!token || !hiloActual) {
        mostrarSeccion("acceso");
        return;
    }

    const texto =
        document.getElementById("nuevoComentario").value.trim();

    const mensaje =
        document.getElementById("comentarioMensaje");

    try {
        const respuesta =
            await fetch(
                `/hilos/${hiloActual}/comentarios`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ texto })
                }
            );

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.error || "No se pudo enviar el comentario"
            );
        }

        if (datos.estado === "aprobado") {
            mensaje.className = "mensaje ok";
            mensaje.textContent =
                "Comentario aprobado por el moderador.";

            document.getElementById(
                "nuevoComentario"
            ).value = "";

            await cargarComentarios(hiloActual);

        } else {
            mensaje.className = "mensaje error";
            mensaje.textContent =
                "Comentario rechazado por el moderador.";
        }

    } catch (error) {
        mensaje.className = "mensaje error";
        mensaje.textContent = error.message;
    }
}


async function calificar(puntuacion) {
    const mensaje =
        document.getElementById("calificacionMensaje");

    if (!token) {
        mensaje.className = "mensaje error";
        mensaje.textContent =
            "Debes iniciar sesión para calificar.";
        return;
    }

    if (!hiloActual) {
        mensaje.className = "mensaje error";
        mensaje.textContent =
            "No hay un hilo seleccionado.";
        return;
    }

    try {
        const respuesta = await fetch(
            `/hilos/${hiloActual}/calificaciones`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    puntuacion
                })
            }
        );

        const tipo =
            respuesta.headers.get("content-type") || "";

        if (!tipo.includes("application/json")) {
            throw new Error(
                "El servidor devolvió una respuesta inesperada."
            );
        }

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.error ||
                "No se pudo registrar la calificación"
            );
        }

        mensaje.className = "mensaje ok";
        mensaje.textContent =
            `Tu calificación: ${puntuacion}/5.`;

        await cargarCalificacion(hiloActual);

    } catch (error) {
        mensaje.className = "mensaje error";
        mensaje.textContent = error.message;
    }
}


async function generarPreview() {
    const contenido =
        document.getElementById("contenidoPreview").value;

    const resultado =
        document.getElementById("previewResultado");

    try {
        const datos = new URLSearchParams();
        datos.append("contenido", contenido);

        const respuesta =
            await fetch("/vista-previa", {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },
                body: datos.toString()
            });

        const html = await respuesta.text();

        if (!respuesta.ok) {
            throw new Error(
                "No se pudo generar la vista previa"
            );
        }

        resultado.innerHTML = html;

    } catch (error) {
        resultado.textContent = error.message;
    }
}


async function probarXSS() {
    document.getElementById(
        "contenidoPreview"
    ).value =
        "<img src=x onerror=alert(1)>";

    await generarPreview();
}




async function eliminarComentario(comentarioId) {
    if (!confirm("¿Deseas eliminar este comentario?")) {
        return;
    }

    const respuesta = await fetch(
        `/comentarios/${comentarioId}`,
        {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    const datos = await respuesta.json();

    if (!respuesta.ok) {
        alert(datos.error || "No se pudo eliminar el comentario");
        return;
    }

    if (hiloActual) {
        await cargarComentarios(hiloActual);
    }

    if (rol === "admin") {
        await cargarAdminComentarios();
    }
}


async function cargarAdminComentarios() {
    const contenedor =
        document.getElementById("listaAdminComentarios");

    try {
        const respuesta = await fetch(
            "/admin/comentarios",
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const comentarios = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                comentarios.error ||
                "No se pudieron cargar los comentarios"
            );
        }

        contenedor.innerHTML = "";

        if (comentarios.length === 0) {
            contenedor.textContent = "No hay comentarios.";
            return;
        }

        comentarios.forEach(comentario => {
            const div = document.createElement("div");
            div.className = "comentario admin-comentario";

            const texto = document.createElement("p");
            texto.textContent = comentario.texto;

            const info = document.createElement("small");
            info.textContent =
                `#${comentario.id} · Hilo ${comentario.hilo_id} · ` +
                `${comentario.autor} · Estado: ${comentario.estado}`;

            const acciones = document.createElement("div");
            acciones.className = "admin-acciones";

            const aprobar = document.createElement("button");
            aprobar.className = "btn-primary";
            aprobar.textContent = "Aprobar";
            aprobar.onclick = () =>
                cambiarEstadoComentario(
                    comentario.id,
                    "aprobado"
                );

            const rechazar = document.createElement("button");
            rechazar.className = "btn-secondary";
            rechazar.textContent = "Rechazar";
            rechazar.onclick = () =>
                cambiarEstadoComentario(
                    comentario.id,
                    "rechazado"
                );

            const eliminar = document.createElement("button");
            eliminar.className = "btn-danger";
            eliminar.textContent = "Eliminar";
            eliminar.onclick = () =>
                eliminarComentario(comentario.id);

            acciones.append(
                aprobar,
                rechazar,
                eliminar
            );

            div.append(
                texto,
                info,
                acciones
            );

            contenedor.appendChild(div);
        });

    } catch (error) {
        contenedor.textContent = error.message;
    }
}


async function cambiarEstadoComentario(comentarioId, estado) {
    const respuesta = await fetch(
        `/admin/comentarios/${comentarioId}/estado`,
        {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                estado
            })
        }
    );

    const datos = await respuesta.json();

    if (!respuesta.ok) {
        alert(
            datos.error ||
            "No se pudo cambiar el estado"
        );
        return;
    }

    await cargarAdminComentarios();

    if (hiloActual) {
        await cargarComentarios(hiloActual);
    }
}


async function eliminarHilo(hiloId) {
    if (!confirm("¿Deseas eliminar este hilo y su contenido?")) {
        return;
    }

    const respuesta = await fetch(
        `/admin/hilos/${hiloId}`,
        {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    const datos = await respuesta.json();

    if (!respuesta.ok) {
        alert(datos.error || "No se pudo eliminar el hilo");
        return;
    }

    await cargarHilos();
}


async function cargarCalificacion(hiloId) {
    const resumen =
        document.getElementById("resumenCalificacion");

    const mensaje =
        document.getElementById("calificacionMensaje");

    mensaje.textContent = "";
    mensaje.className = "mensaje";

    try {
        const respuesta = await fetch(
            `/hilos/${hiloId}/calificaciones`,
            {
                headers: token
                    ? {
                        "Authorization": `Bearer ${token}`
                    }
                    : {}
            }
        );

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.error ||
                "No fue posible cargar la calificación"
            );
        }

        if (datos.total === 0) {
            resumen.textContent =
                "Sin calificaciones todavía.";
        } else {
            resumen.textContent =
                `Promedio: ${datos.promedio}/5 · ` +
                `${datos.total} calificación` +
                `${datos.total === 1 ? "" : "es"}`;
        }

        if (datos.mi_puntuacion) {
            mensaje.className = "mensaje ok";
            mensaje.textContent =
                `Tu calificación: ${datos.mi_puntuacion}/5.`;
        }

        document
            .querySelectorAll("#estrellas button")
            .forEach((estrella, indice) => {
                if (
                    datos.mi_puntuacion &&
                    indice < datos.mi_puntuacion
                ) {
                    estrella.classList.add("seleccionada");
                } else {
                    estrella.classList.remove("seleccionada");
                }
            });

    } catch (error) {
        resumen.textContent =
            "No fue posible cargar las calificaciones.";
    }
}
