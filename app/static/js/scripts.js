document.addEventListener('DOMContentLoaded', (event) => {
    // Código que se ejecuta cuando el DOM está completamente cargado

    // Ejemplo: Confirmación antes de eliminar un registro (como un síntoma, enfermedad o usuario)
    const deleteButtons = document.querySelectorAll('.delete-btn');
    for (const button of deleteButtons) {
        button.addEventListener('click', (e) => {
            const confirmation = confirm('¿Estás seguro de que deseas eliminar este registro?');
            if (!confirmation) {
                e.preventDefault(); // Previene la acción predeterminada si el usuario cancela
            }
        });
    }

    // Aquí puedes agregar más funciones o escuchadores de eventos según lo necesites
});
