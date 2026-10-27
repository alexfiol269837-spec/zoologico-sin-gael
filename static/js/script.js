document.addEventListener("DOMContentLoaded", () => {
    // Confirmar antes de eliminar un animal.
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const mensaje = form.dataset.confirm;

            if (!window.confirm(mensaje)) {
                event.preventDefault();
            }
        });
    });

    // Mostrar una vista previa al pegar una URL de imagen.
    document.querySelectorAll("[data-image-url]").forEach((input) => {
        const contenedor = input
            .closest(".field")
            ?.querySelector("[data-image-preview]");

        const imagen = contenedor?.querySelector("img");

        if (!contenedor || !imagen) {
            return;
        }

        const actualizarVistaPrevia = () => {
            const url = input.value.trim();

            if (!url) {
                imagen.removeAttribute("src");
                contenedor.hidden = true;
                return;
            }

            contenedor.hidden = false;
            imagen.hidden = false;
            imagen.alt = "Vista previa de la fotografía";
            imagen.src = url;
        };

        imagen.addEventListener("error", () => {
            imagen.hidden = true;
        });

        imagen.addEventListener("load", () => {
            imagen.hidden = false;
        });

        input.addEventListener("input", actualizarVistaPrevia);
    });
});