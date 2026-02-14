# Plan: Mejora UI/UX Completa del Sistema Academico

## Contexto
El Sistema Academico tiene ~50+ templates (admin, jefe, profesor) con Bootstrap 5.1.3. Actualmente presenta inconsistencias en botones (texto, posicion, tamano), tablas con texto demasiado grande que no cabe ni en escritorio, tipografia sin jerarquia clara, y falta de responsividad para moviles/tablets/TV. Este plan estandariza todo el UI/UX sin romper funcionalidad.

---

## Fase 1: Fundacion CSS (solo `static/css/style.css`)
Riesgo: Bajo. Solo cambios CSS, sin tocar templates.

### 1A. Corregir breakpoints
- Reemplazar `min-width: 769px` por `min-width: 768px` (4 ocurrencias, lineas ~44, 301, 860, 935) para alinear con Bootstrap 5

### 1B. Tipografia con clamp() limpia
- Eliminar overrides redundantes de h1/h2/h3 dentro del media query `min-width: 769px` (lineas 45-55)
- Dejar solo los clamp() que ya escalan automaticamente
- Agregar clamp() para h4, h5, h6

### 1C. Estandarizar tablas - header
- Forzar un solo estilo dark para todos los `<thead>` via CSS (sin importar clase Bootstrap usada)
- Subir font-size de thead de 0.78rem a 0.82rem
- Reducir letter-spacing de 0.03em a 0.02em
- Hacer sticky todos los thead (position: sticky, top: 0)

### 1D. Arreglar texto de tablas (problema principal)
- Reducir font-size base de tablas: 0.9rem -> 0.875rem (desktop), 0.84rem -> 0.8rem (tablet), 0.78rem (movil)
- Agregar `max-width: 250px` y `overflow-wrap: anywhere` a `<td>` para evitar columnas infinitas
- Reducir min-width de tablas en movil ~30%:
  - table-narrow: 700px -> 500px
  - table-wide: 820px -> 600px
  - table-xwide: 980px -> 720px

### 1E. Estandarizar botones
- Tamano base uniforme: font-size 0.875rem, padding 0.4rem 0.85rem
- Botones en tablas siempre pequenos: font-size 0.8rem
- Min-height 42px en movil (touch targets), 34px en tablas

### 1F. Button groups responsivos
- Flex-wrap en movil para que no se desborden
- Page headers se apilan verticalmente en movil (titulo arriba, botones abajo)

### 1G. Modales en movil
- Aumentar max-width del dropdown navbar: 320px -> 380px
- Modal dialog: max-width: calc(100vw - 1rem) en pantallas pequenas

### 1H. Optimizacion tablet (768px-991px)
- Font-size tablas 0.85rem
- Reducir min-width de grids de horarios

### 1I. Indicador de scroll horizontal en tablas
- Gradiente visual en el borde derecho cuando la tabla es scrolleable (solo movil)

### 1J. Clases de utilidad para font-size
- `.fs-xs` (0.75rem), `.fs-sm` (0.8125rem), `.fs-base` (0.875rem)

### 1K. Checkbox uniformes
- Todos 1.25rem x 1.25rem via CSS (eliminar inline styles de 25px)

---

## Fase 2: Estandarizacion de botones en templates (~35 archivos)

### 2A. Diccionario de etiquetas estandar

| Accion | Texto estandar | Icono |
|--------|---------------|-------|
| Volver al dashboard | "Volver al Dashboard" | `fa-arrow-left` |
| Volver a lista | "Volver" | `fa-arrow-left` |
| Guardar/crear | "Guardar" | `fa-save` |
| Cancelar | "Cancelar" | `fa-times` |
| Eliminar | "Eliminar" | `fa-trash-alt` |
| Seleccionar todo | "Seleccionar todo" | `fa-check-double` |
| Deseleccionar todo | "Deseleccionar todo" | `fa-times` |
| Agregar entidad | "Agregar [Entidad]" | `fa-plus` |
| Importar | "Importar" | `fa-upload` |
| Exportar PDF | "Exportar PDF" | `fa-file-pdf` |

**Regla**: Todo en sentence case, nunca MAYUSCULAS.

### 2B. Header de pagina estandar
Todas las paginas usan:
```html
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="admin-page-title"><i class="fas fa-ICON me-2"></i>Titulo</h2>
    <div class="page-actions">
        <a href="..." class="btn btn-outline-secondary"><i class="fas fa-arrow-left me-1"></i>Volver al Dashboard</a>
        <a href="..." class="btn btn-primary"><i class="fas fa-plus me-1"></i>Agregar Entidad</a>
    </div>
</div>
```
- Siempre `<h2>` para titulo de pagina (no h1, no h3)
- Back button siempre `btn-outline-secondary`

### 2C. Footer de formularios estandar
```html
<div class="d-flex justify-content-end gap-2 mt-4">
    <a href="..." class="btn btn-outline-secondary"><i class="fas fa-times me-1"></i>Cancelar</a>
    <button type="submit" class="btn btn-primary"><i class="fas fa-save me-1"></i>Guardar</button>
</div>
```
- Cancelar siempre a la izquierda, Guardar a la derecha
- Nunca `btn-success` para guardar, siempre `btn-primary`
- Nunca `btn-lg` en formularios

### 2D. Templates a modificar (texto de botones)
**Back buttons** - cambiar a "Volver al Dashboard" o "Volver":
- `admin/grupos.html`, `admin/generar_horarios_masivo.html`, `admin/eliminar_horario_academico.html`
- `admin/admin_disponibilidad_profesores.html`, `admin/admin_horario_profesores.html`
- `admin/asignacion_masiva_materias.html`, `admin/horarios_academicos.html`
- `jefe/jefe_horario_grupos.html`, `jefe/asignacion_masiva_materias.html`
- `jefe/editar_disponibilidad_profesor.html`, `jefe/ver_disponibilidad_profesor.html`

**Save buttons** - cambiar a "Guardar":
- `admin/configuracion.html` (6 botones diferentes)
- `admin/asignacion_masiva_materias.html` ("GUARDAR CAMBIOS")
- `admin/admin_editar_disponibilidad_profesor.html` ("Guardar Disponibilidad")
- `profesor/disponibilidad.html` ("Guardar Disponibilidad")
- `admin/materia_form.html`, `admin/profesor_form.html` (btn-success -> btn-primary)

**Select/Deselect** - estandarizar a "Seleccionar todo" / "Deseleccionar todo":
- ~11 templates con variaciones ("Todos", "Todas", "Todo")

---

## Fase 3: Estandarizacion de tablas (~17 archivos)

### 3A. Todas las `<thead>` a `class="table-dark"`
Archivos con thead diferente:
- `admin/profesores.html`, `admin/horarios_academicos.html` (table-light)
- `admin/grupos.html` (thead-dark deprecated)
- `admin/importar_profesores.html` (table-success)
- `admin/ver_materias_grupo.html` (bg-light)
- `jefe/profesores.html`, `jefe/editar_profesor.html` (table-light)
- `register.html` (bg-light)
- ~10 archivos mas

### 3B. Eliminar inline styles de sticky headers
- 2 templates con `style="position: sticky..."` - eliminar (CSS ya lo maneja)

### 3C. Columna de acciones estandar
- Agregar clase `.col-actions` (width: 1%, nowrap, text-center) a todas las columnas de acciones

---

## Fase 4: Limpieza de inline styles y consolidacion CSS (~23 templates + style.css)

### 4A. Eliminar inline styles
- Checkbox sizing (`style="width: 25px..."`) -> clase CSS
- `style="display: none;"` -> clase `d-none`
- `style="font-size: 0.65rem;"` -> clase `fs-xs`
- Sticky headers inline -> CSS global

### 4B. Mover `<style>` blocks de templates a style.css
- `jefe/profesores.html` lineas 157-168
- `profesor/disponibilidad.html` lineas 251-265

### 4C. Consolidar media queries en style.css
Unificar en 4 bloques limpios:
1. `@media (min-width: 768px)` - desktop
2. `@media (min-width: 768px) and (max-width: 991.98px)` - tablet
3. `@media (max-width: 767.98px)` - movil
4. `@media (max-width: 575.98px)` - movil pequeno

---

## Fase 5: Soporte TV/4K y pulido final

### 5A. Breakpoint para pantallas grandes
```css
@media (min-width: 1920px) {
    .app-main .container-fluid { max-width: 1800px; margin: 0 auto; }
    body { font-size: 1rem; }
}
@media (min-width: 2560px) {
    .app-main .container-fluid { max-width: 2200px; }
    body { font-size: 1.05rem; }
}
```

### 5B. Ajustar script de auto-sizing en base.html
- Cambiar umbrales: 7+ columnas = wide, 9+ = xwide (antes era 6+ y 8+)

### 5C. Estilos de impresion
- Ocultar botones, navbar, footer en print
- Thead con fondo claro para impresion

---

## Archivos criticos

| Archivo | Cambios |
|---------|---------|
| `static/css/style.css` | Fase 1 completa, partes de Fase 4 y 5 |
| `templates/base.html` | Fase 5B (script auto-sizing) |
| `templates/admin/*.html` (~32 archivos) | Fases 2, 3, 4 |
| `templates/jefe/*.html` (~8 archivos) | Fases 2, 3, 4 |
| `templates/profesor/*.html` (~3 archivos) | Fases 2, 3, 4 |
| `templates/login.html`, `register.html` | Fase 3 |
| `templates/dashboard.html` | Fase 2 |
| `templates/index.html` | Revision menor |

---

## Verificacion

Despues de cada fase:
1. Probar en 375px (iPhone SE), 768px (iPad), 1024px (iPad landscape), 1366px (laptop), 1920px (desktop)
2. Verificar que las tablas son scrolleables sin recortar contenido
3. Verificar que los botones se apilan correctamente en movil
4. Verificar que los modales son usables en movil
5. Verificar que los formularios son accesibles en todas las pantallas
6. Comparar visualmente que todas las paginas del mismo tipo se ven identicas
7. Probar funcionalidad: login, crear/editar/eliminar entidades, generar horarios
