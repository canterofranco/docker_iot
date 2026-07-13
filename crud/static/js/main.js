// ============== Borrar con confirmación ==============
const btnDelete = document.querySelectorAll('.btn-borrar');
if (btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (!confirm('¿Está seguro de querer borrar?')) {
        e.preventDefault();
      }
    });
  });
}

// ============== Selector de tema ==============
// Diccionario con los temas disponibles
const TEMAS = {
  claro:  'https://bootswatch.com/5/cosmo/bootstrap.min.css',
  oscuro: 'https://bootswatch.com/5/darkly/bootstrap.min.css'
};
const linkTema = document.getElementById('tema-css');

// Al cargar la página, aplico el tema guardado (si hay)
const temaGuardado = localStorage.getItem('tema') || 'claro';
if (linkTema && TEMAS[temaGuardado]) {
  linkTema.href = TEMAS[temaGuardado];
}

// Listener para los items del dropdown
document.querySelectorAll('.btn-tema-select').forEach((item) => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    const tema = item.getAttribute('data-tema');
    if (TEMAS[tema]) {
      linkTema.href = TEMAS[tema];
      localStorage.setItem('tema', tema);
    }
  });
});
