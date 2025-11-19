# Importación Masiva de Carreras

## Descripción
Esta funcionalidad permite importar múltiples carreras al sistema de manera rápida y eficiente mediante un archivo CSV (valores separados por comas).

## Características Principales

### 1. Importación desde CSV
- Soporta múltiples carreras en un solo archivo
- Validación automática de datos
- Actualización de carreras existentes (basado en el código)
- Creación de nuevas carreras
- Reportes detallados de errores y éxitos

### 2. Formato del Archivo CSV

#### Columnas Requeridas
- **codigo**: Código único de la carrera (2-10 caracteres)
- **nombre**: Nombre completo de la carrera (5-150 caracteres)

#### Columnas Opcionales
- **descripcion**: Descripción de la carrera (máximo 500 caracteres)
- **facultad**: Nombre de la facultad (máximo 100 caracteres)

#### Ejemplo de Archivo CSV
```csv
codigo,nombre,descripcion,facultad
ING-SIS,Ingeniería en Sistemas Computacionales,Carrera de ingeniería enfocada en desarrollo de software,Facultad de Ingeniería
ADM-EMP,Administración de Empresas,Carrera enfocada en gestión empresarial,Facultad de Ciencias Económicas
DER,Derecho,Carrera de ciencias jurídicas,Facultad de Derecho
```

## Cómo Usar la Funcionalidad

### Paso 1: Acceder al Módulo
1. Inicia sesión como **Administrador**
2. Navega a **Gestión de Carreras**
3. Haz clic en el botón **"Importar desde CSV"**

### Paso 2: Descargar Plantilla (Opcional)
- En la página de importación, puedes descargar una plantilla de ejemplo
- La plantilla incluye ejemplos de carreras con el formato correcto
- Modifica la plantilla con tus propias carreras

### Paso 3: Preparar el Archivo CSV
1. Crea o edita un archivo CSV con las columnas requeridas
2. Asegúrate de que:
   - La primera fila contenga los nombres de las columnas
   - Los códigos sean únicos
   - Los nombres tengan al menos 5 caracteres
   - No haya filas vacías entre datos

### Paso 4: Importar el Archivo
1. Selecciona tu archivo CSV usando el botón "Examinar"
2. Haz clic en **"Importar Carreras"**
3. El sistema procesará el archivo y mostrará los resultados

## Validaciones Automáticas

### Validaciones de Formato
- ✅ Códigos entre 2 y 10 caracteres
- ✅ Nombres entre 5 y 150 caracteres
- ✅ Descripciones máximo 500 caracteres
- ✅ Facultades máximo 100 caracteres
- ✅ Códigos únicos (no duplicados)
- ✅ Nombres únicos (no duplicados)

### Comportamiento de Actualización
- Si existe una carrera con el **mismo código**: se actualiza
- Si existe una carrera con el **mismo nombre** pero diferente código: se genera error
- Si no existe la carrera: se crea como nueva

## Resultados de la Importación

### Mensajes de Éxito
El sistema mostrará:
- Número de carreras creadas
- Número de carreras actualizadas
- Lista de carreras procesadas con su acción (creada/actualizada)

### Mensajes de Error
Si hay errores, el sistema mostrará:
- Fila específica donde ocurrió el error
- Descripción detallada del problema
- Los primeros 5 errores encontrados (si hay más, se indica el total)

### Ejemplos de Errores Comunes
- **"Código o nombre vacío"**: Falta información obligatoria
- **"El código debe tener entre 2 y 10 caracteres"**: Código muy corto o muy largo
- **"Ya existe una carrera con el nombre X"**: Nombre duplicado
- **"Columnas faltantes"**: El archivo no tiene las columnas requeridas

## Consejos y Mejores Prácticas

### 1. Preparación de Datos
- ✅ Verifica que no haya espacios extra en los códigos
- ✅ Usa códigos descriptivos (ej: ING-SIS, ADM-EMP)
- ✅ Incluye descripciones claras para facilitar la identificación
- ✅ Agrupa carreras por facultad para mejor organización

### 2. Manejo de Errores
- Si el sistema reporta errores, corrígelos en el CSV y vuelve a importar
- Las carreras que se procesaron correctamente no se duplicarán
- Usa la plantilla de ejemplo como guía de formato

### 3. Actualización de Carreras Existentes
- Para actualizar una carrera, usa el mismo código
- Puedes cambiar nombre, descripción o facultad
- El código es el identificador único

### 4. Codificación del Archivo
- El sistema soporta UTF-8, Latin-1 e ISO-8859-1
- Se recomienda UTF-8 para caracteres especiales (ñ, á, é, etc.)
- Excel guarda por defecto en el formato correcto

## Plantilla de Ejemplo

El sistema incluye una plantilla de ejemplo que puedes descargar:

**plantilla_carreras.csv**
```csv
codigo,nombre,descripcion,facultad
ING-SIS,Ingeniería en Sistemas Computacionales,Carrera de ingeniería enfocada en desarrollo de software,Facultad de Ingeniería
ADM-EMP,Administración de Empresas,Carrera enfocada en gestión empresarial,Facultad de Ciencias Económicas
DER,Derecho,Carrera de ciencias jurídicas,Facultad de Derecho
```

## Archivos Relacionados

### Código Backend
- **forms.py**: `ImportarCarrerasForm` - Formulario de importación
- **utils.py**: `procesar_archivo_carreras()` - Procesamiento del CSV
- **utils.py**: `generar_plantilla_csv_carreras()` - Generación de plantilla
- **app.py**: Rutas `/admin/carreras/importar` y `/admin/carreras/plantilla`

### Templates
- **templates/admin/importar_carreras.html**: Interfaz de importación
- **templates/admin/carreras.html**: Botón de acceso a importación

## Solución de Problemas

### Problema: "Columnas faltantes"
**Solución**: Verifica que tu archivo tenga al menos las columnas `codigo` y `nombre`

### Problema: "Error al procesar el archivo"
**Solución**: Verifica que el archivo sea un CSV válido y no esté corrupto

### Problema: "Ya existe una carrera con código X"
**Solución**: Este es un comportamiento esperado, la carrera se actualizará

### Problema: Caracteres especiales no se ven correctamente
**Solución**: Guarda el archivo CSV con codificación UTF-8

## Seguridad

- ✅ Solo usuarios con rol **Administrador** pueden importar carreras
- ✅ Todas las operaciones se auditan con el ID del usuario
- ✅ Validaciones estrictas de datos antes de guardar
- ✅ Transacciones de base de datos: si hay error, no se guarda nada

## Notas Adicionales

- La importación no elimina carreras existentes
- Las carreras importadas quedan activas por defecto
- Se puede asignar jefe de carrera después de importar
- Los profesores deben asociarse manualmente a las carreras importadas
