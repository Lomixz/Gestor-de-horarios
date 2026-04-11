# API Académica - Documentación Completa

## Índice

1. [Overview](#overview)
2. [Autenticación](#autenticación)
3. [Respuestas y Códigos de Error](#respuestas-y-códigos-de-error)
4. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Autenticación](#autenticación-1)
   - [Carreras](#carreras)
   - [Cuatrimestres](#cuatrimestres)
   - [Relaciones Docente-Materia-Carrera](#relaciones-docente-materia-carrera)
5. [Casos de Uso Comunes](#casos-de-uso-comunes)
6. [Estructura de Datos](#estructura-de-datos)

---

## Overview

Esta API proporciona acceso a los datos académicos del **Gestor de Horarios**, permitiendo que sistemas externos (como el sistema de evaluación docente) accedan de forma segura a:

- **Usuarios y Autenticación**: Verificar credenciales sin duplicar cuentas
- **Carreras**: Programas académicos disponibles
- **Cuatrimestres**: Períodos académicos y sus materias
- **Relaciones Académicas**: Qué profesor imparte qué materia en qué carrera

**URL Base**: `https://horarios.ddns.net/api/ext/`

**Versión**: 1.0  
**Última actualización**: Abril 2026  
**Tipo de Datos**: JSON  
**Protocolo**: HTTPS (recomendado)

---

## Autenticación

Todos los endpoints (excepto `/api/ext/ping`) **requieren autenticación por API Key**.

### Esquema: Header X-API-Key

La clave API debe incluirse como header HTTP en cada request:

```
X-API-Key: <EXTERNAL_API_KEY>
```

### Obtener la API Key

La variable de entorno `EXTERNAL_API_KEY` debe configurarse en el servidor. Contacta al administrador del Gestor de Horarios para obtenerla.

```bash
# Ejemplo en .env del servidor
EXTERNAL_API_KEY=tu_clave_secreta_aqui_123456
```

### Ejemplo con cURL

```bash
curl -X GET "https://tu-dominio/api/ext/carreras" \
  -H "X-API-Key: tu_clave_secreta_aqui_123456"
```

### Ejemplo con JavaScript/Node.js

```javascript
const API_KEY = process.env.EXTERNAL_API_KEY;
const response = await fetch('https://tu-dominio/api/ext/carreras', {
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
```

### Ejemplo con Python

```python
import requests

API_KEY = "tu_clave_secreta_aqui_123456"
headers = {"X-API-Key": API_KEY}

response = requests.get(
    "https://tu-dominio/api/ext/carreras",
    headers=headers
)
data = response.json()
```

---

## Respuestas y Códigos de Error

### Códigos HTTP Comunes

| Código | Significado | Descripción |
|--------|-------------|-------------|
| `200` | OK | Request exitoso, datos retornados |
| `400` | Bad Request | Datos inválidos o incompletos en el request |
| `401` | Unauthorized | API Key ausente, inválida o expirada |
| `403` | Forbidden | Usuario no autorizado o cuenta inactiva |
| `404` | Not Found | Recurso no existe |
| `500` | Internal Server Error | Error en el servidor |

### Estructura de Errores

Todas las respuestas de error siguen este formato:

```json
{
  "error": "Descripción clara del error"
}
```

### Ejemplo: Error de Autenticación

```bash
$ curl -X GET "https://tu-dominio/api/ext/carreras" \
  -H "X-API-Key: CLAVE_INVALIDA"

HTTP/1.1 401 Unauthorized
{
  "error": "API Key inválida o ausente"
}
```

---

## Endpoints

### Health Check

#### `GET /api/ext/ping`

**Descripción**: Verifica que la API está activa. No requiere autenticación.

**Parámetros**: Ninguno

**Respuesta (200 OK)**:
```json
{
  "status": "ok",
  "message": "API académica activa"
}
```

**Caso de uso**: Verificar conectividad antes de hacer requests autenticados.

```bash
curl -X GET "https://tu-dominio/api/ext/ping"
```

---

### Autenticación

#### `POST /api/ext/auth/login`

**Descripción**: Autentica un usuario del Gestor de Horarios sin exponer su contraseña. Reutiliza las mismas cuentas del sistema, evitando duplicidad de credenciales.

**Requiere**: `X-API-Key` header

**Body JSON**:
```json
{
  "login": "username_o_email",
  "password": "contraseña_del_usuario",
  "rol": "profesor_completo"  // OPCIONAL: si solo quieres que se autentique si tiene este rol
}
```

**Parámetros Query** (alternativa a body):
- `rol=profesor_completo|profesor_asignatura|admin|jefe_carrera|...` (opcional)

**Respuesta (200 OK)** — Autenticación exitosa:
```json
{
  "autenticado": true,
  "usuario": {
    "id": 42,
    "username": "jdoe",
    "nombre": "Juan",
    "apellido": "Doe",
    "nombre_completo": "Juan Doe",
    "email": "juan.doe@university.edu",
    "rol": "profesor_completo",
    "roles": ["profesor_completo", "jefe_carrera"],
    "tipo_profesor": "profesor_completo",
    "activo": true,
    "carreras": [
      {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      },
      {
        "id": 2,
        "nombre": "Ingeniería en Informática",
        "codigo": "IIT"
      }
    ]
  }
}
```

**Respuesta (404 Not Found)** — Usuario no encontrado:
```json
{
  "autenticado": false,
  "error": "Usuario no encontrado"
}
```

**Respuesta (401 Unauthorized)** — Contraseña incorrecta:
```json
{
  "autenticado": false,
  "error": "Contraseña incorrecta"
}
```

**Respuesta (403 Forbidden)** — Cuenta inactiva:
```json
{
  "autenticado": false,
  "error": "Cuenta inactiva"
}
```

**Respuesta (403 Forbidden)** — No tiene el rol requerido:
```json
{
  "autenticado": false,
  "error": "El usuario no tiene el rol requerido: administrador"
}
```

**Ejemplos de Uso**:

```bash
# Login básico
curl -X POST "https://tu-dominio/api/ext/auth/login" \
  -H "X-API-Key: tu_clave_secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "login": "jdoe",
    "password": "su_contraseña"
  }'

# Login con verificación de rol (solo profesor)
curl -X POST "https://tu-dominio/api/ext/auth/login" \
  -H "X-API-Key: tu_clave_secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "login": "jdoe@university.edu",
    "password": "su_contraseña",
    "rol": "profesor_completo"
  }'
```

**Integración con NextAuth.js (CredentialsProvider)**:

```javascript
// pages/api/auth/[...nextauth].js
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        login: { label: "Usuario o Email", type: "text" },
        password: { label: "Contraseña", type: "password" }
      },
      async authorize(credentials) {
        const res = await fetch('https://tu-dominio/api/ext/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': process.env.EXTERNAL_API_KEY
          },
          body: JSON.stringify({
            login: credentials?.login,
            password: credentials?.password,
            rol: 'profesor_completo' // opcional: requiere que sea profesor
          })
        });

        const data = await res.json();

        if (res.ok && data.autenticado) {
          // Retornar usuario en formato NextAuth
          return {
            id: data.usuario.id.toString(),
            name: data.usuario.nombre_completo,
            email: data.usuario.email,
            roles: data.usuario.roles,
            tipo_profesor: data.usuario.tipo_profesor,
            carreras: data.usuario.carreras
          };
        }
        
        // Autenticación fallida
        throw new Error(data.error || 'Autenticación fallida');
      }
    })
  ]
};
```

---

### Carreras

#### `GET /api/ext/carreras`

**Descripción**: Retorna listado de todas las carreras registradas en el sistema.

**Requiere**: `X-API-Key` header

**Parámetros Query**:
- `activa=true|false` (opcional) — Filtrar por estado activo/inactivo (default: todos)

**Respuesta (200 OK)**:
```json
{
  "total": 3,
  "carreras": [
    {
      "id": 1,
      "nombre": "Ingeniería en Sistemas",
      "codigo": "ISI",
      "descripcion": "Formación de ingenieros en desarrollo de sistemas informáticos",
      "facultad": "Facultad de Ingeniería",
      "activa": true,
      "fecha_creacion": "2023-01-15T10:30:00"
    },
    {
      "id": 2,
      "nombre": "Ingeniería en Informática",
      "codigo": "IIT",
      "descripcion": "Especialización en tecnologías de información",
      "facultad": "Facultad de Ingeniería",
      "activa": true,
      "fecha_creacion": "2023-01-15T10:32:00"
    },
    {
      "id": 3,
      "nombre": "Ingeniería en Gestión Administrativa",
      "codigo": "IGA",
      "descripcion": "Formación en administración de empresas",
      "facultad": "Facultad de Administración",
      "activa": true,
      "fecha_creacion": "2023-01-15T10:35:00"
    }
  ]
}
```

**Ejemplo de Uso**:
```bash
# Obtener todas las carreras
curl -X GET "https://tu-dominio/api/ext/carreras" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener solo carreras activas
curl -X GET "https://tu-dominio/api/ext/carreras?activa=true" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener solo carreras inactivas
curl -X GET "https://tu-dominio/api/ext/carreras?activa=false" \
  -H "X-API-Key: tu_clave_secreta"
```

**Casos de Uso**:
- Llenar dropdown/select de carreras en formularios
- Sincronizar catálogo de carreras con sistema externo
- Validar que una carrera existe antes de hacer otros queries

---

#### `GET /api/ext/carreras/<id>`

**Descripción**: Retorna información completa de una carrera específica, incluyendo sus materias y profesores asignados.

**Requiere**: `X-API-Key` header

**Parámetros**:
- `id` (URL path, requerido) — ID de la carrera

**Respuesta (200 OK)**:
```json
{
  "id": 1,
  "nombre": "Ingeniería en Sistemas",
  "codigo": "ISI",
  "descripcion": "Formación de ingenieros en desarrollo de sistemas informáticos",
  "facultad": "Facultad de Ingeniería",
  "activa": true,
  "fecha_creacion": "2023-01-15T10:30:00",
  "materias": [
    {
      "id": 101,
      "nombre": "Programación I",
      "codigo": "ISI-101",
      "descripcion": "Fundamentos de programación",
      "cuatrimestre": 1,
      "creditos": 4,
      "horas_semanales": 4,
      "activa": true,
      "carrera": {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      }
    },
    {
      "id": 102,
      "nombre": "Estructuras Discretas",
      "codigo": "ISI-102",
      "descripcion": "Matemática aplicada a sistemas",
      "cuatrimestre": 1,
      "creditos": 3,
      "horas_semanales": 3,
      "activa": true,
      "carrera": {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      }
    }
  ],
  "profesores": [
    {
      "id": 42,
      "username": "jdoe",
      "nombre": "Juan",
      "apellido": "Doe",
      "nombre_completo": "Juan Doe",
      "email": "juan.doe@university.edu",
      "tipo_profesor": "profesor_completo",
      "activo": true
    },
    {
      "id": 43,
      "username": "msmith",
      "nombre": "María",
      "apellido": "Smith",
      "nombre_completo": "María Smith",
      "email": "maria.smith@university.edu",
      "tipo_profesor": "profesor_asignatura",
      "activo": true
    }
  ]
}
```

**Respuesta (404 Not Found)** — Carrera no existe:
```json
{
  "error": "Carrera no encontrada"
}
```

**Ejemplo de Uso**:
```bash
# Obtener detalle de carrera ID 1
curl -X GET "https://tu-dominio/api/ext/carreras/1" \
  -H "X-API-Key: tu_clave_secreta"
```

**Casos de Uso**:
- Mostrar detalles de una carrera en una página de detalle
- Obtener todas las materias de una carrera
- Obtener profesores disponibles para una carrera

---

### Cuatrimestres

#### `GET /api/ext/cuatrimestres`

**Descripción**: Retorna los cuatrimestres/semestres que existen en el sistema, con conteo de materias por carrera.

**Requiere**: `X-API-Key` header

**Parámetros Query**:
- `carrera_id=<int>` (opcional) — Filtrar por carrera específica

**Respuesta (200 OK)**:
```json
{
  "total": 3,
  "cuatrimestres": [
    {
      "numero": 1,
      "nombre": "Cuatrimestre 1",
      "total_materias": 6,
      "carreras": [
        {
          "id": 1,
          "nombre": "Ingeniería en Sistemas",
          "codigo": "ISI",
          "materias_count": 3
        },
        {
          "id": 2,
          "nombre": "Ingeniería en Informática",
          "codigo": "IIT",
          "materias_count": 2
        },
        {
          "id": 3,
          "nombre": "Ingeniería en Gestión Administrativa",
          "codigo": "IGA",
          "materias_count": 1
        }
      ]
    },
    {
      "numero": 2,
      "nombre": "Cuatrimestre 2",
      "total_materias": 5,
      "carreras": [
        {
          "id": 1,
          "nombre": "Ingeniería en Sistemas",
          "codigo": "ISI",
          "materias_count": 2
        },
        {
          "id": 2,
          "nombre": "Ingeniería en Informática",
          "codigo": "IIT",
          "materias_count": 3
        }
      ]
    },
    {
      "numero": 3,
      "nombre": "Cuatrimestre 3",
      "total_materias": 4,
      "carreras": [
        {
          "id": 1,
          "nombre": "Ingeniería en Sistemas",
          "codigo": "ISI",
          "materias_count": 4
        }
      ]
    }
  ]
}
```

**Ejemplo de Uso**:
```bash
# Obtener todos los cuatrimestres
curl -X GET "https://tu-dominio/api/ext/cuatrimestres" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener cuatrimestres de una carrera específica
curl -X GET "https://tu-dominio/api/ext/cuatrimestres?carrera_id=1" \
  -H "X-API-Key: tu_clave_secreta"
```

**Casos de Uso**:
- Llenar selector de cuatrimestres en formularios de evaluación
- Mostrar estructura curricular de una carrera
- Filtrar materias disponibles por período

---

#### `GET /api/ext/cuatrimestres/<numero>/materias`

**Descripción**: Retorna todas las materias de un cuatrimestre específico.

**Requiere**: `X-API-Key` header

**Parámetros**:
- `numero` (URL path, requerido) — Número del cuatrimestre (1, 2, 3, etc.)
- `carrera_id=<int>` (query, opcional) — Filtrar por carrera específica

**Respuesta (200 OK)**:
```json
{
  "cuatrimestre": 1,
  "nombre": "Cuatrimestre 1",
  "total": 2,
  "materias": [
    {
      "id": 101,
      "nombre": "Programación I",
      "codigo": "ISI-101",
      "descripcion": "Fundamentos de programación",
      "cuatrimestre": 1,
      "creditos": 4,
      "horas_semanales": 4,
      "activa": true,
      "carrera": {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      }
    },
    {
      "id": 102,
      "nombre": "Estructuras Discretas",
      "codigo": "ISI-102",
      "descripcion": "Matemática aplicada a sistemas",
      "cuatrimestre": 1,
      "creditos": 3,
      "horas_semanales": 3,
      "activa": true,
      "carrera": {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      }
    }
  ]
}
```

**Respuesta (404 Not Found)** — Cuatrimestre no existe:
```json
{
  "error": "Cuatrimestre 99 no encontrado"
}
```

**Ejemplo de Uso**:
```bash
# Obtener materias del cuatrimestre 1
curl -X GET "https://tu-dominio/api/ext/cuatrimestres/1/materias" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener materias del cuatrimestre 2 de la carrera ISI (id=1)
curl -X GET "https://tu-dominio/api/ext/cuatrimestres/2/materias?carrera_id=1" \
  -H "X-API-Key: tu_clave_secreta"
```

**Casos de Uso**:
- Mostrar catálogo de materias para un período académico
- Filtrar materias disponibles para evaluación
- Validar que una materia pertenece a un cuatrimestre antes de crear evaluaciones

---

### Relaciones Docente-Materia-Carrera

#### `GET /api/ext/relaciones`

**Descripción**: Retorna las relaciones entre profesores, materias y carreras. Cada registro indica qué profesor imparte (o puede impartir) una materia de una carrera.

**Requiere**: `X-API-Key` header

**Parámetros Query** (todos opcionales):
- `carrera_id=<int>` — Filtrar por carrera
- `cuatrimestre=<int>` — Filtrar por cuatrimestre de la materia
- `profesor_id=<int>` — Filtrar por profesor específico
- `activo=true|false` — Filtrar por estado del profesor (default: true)

**Respuesta (200 OK)**:
```json
{
  "total": 4,
  "relaciones": [
    {
      "profesor": {
        "id": 42,
        "username": "jdoe",
        "nombre": "Juan",
        "apellido": "Doe",
        "nombre_completo": "Juan Doe",
        "email": "juan.doe@university.edu",
        "tipo_profesor": "profesor_completo",
        "activo": true
      },
      "materia": {
        "id": 101,
        "nombre": "Programación I",
        "codigo": "ISI-101",
        "descripcion": "Fundamentos de programación",
        "cuatrimestre": 1,
        "creditos": 4,
        "horas_semanales": 4,
        "activa": true,
        "carrera": {
          "id": 1,
          "nombre": "Ingeniería en Sistemas",
          "codigo": "ISI"
        }
      },
      "carrera": {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      }
    },
    {
      "profesor": {
        "id": 42,
        "username": "jdoe",
        "nombre": "Juan",
        "apellido": "Doe",
        "nombre_completo": "Juan Doe",
        "email": "juan.doe@university.edu",
        "tipo_profesor": "profesor_completo",
        "activo": true
      },
      "materia": {
        "id": 201,
        "nombre": "Programación II",
        "codigo": "ISI-201",
        "descripcion": "Programación orientada a objetos",
        "cuatrimestre": 2,
        "creditos": 4,
        "horas_semanales": 4,
        "activa": true,
        "carrera": {
          "id": 1,
          "nombre": "Ingeniería en Sistemas",
          "codigo": "ISI"
        }
      },
      "carrera": {
        "id": 1,
        "nombre": "Ingeniería en Sistemas",
        "codigo": "ISI"
      }
    }
  ]
}
```

**Respuesta (200 OK)** — Sin resultados:
```json
{
  "total": 0,
  "relaciones": []
}
```

**Ejemplos de Uso**:

```bash
# Obtener todas las relaciones
curl -X GET "https://tu-dominio/api/ext/relaciones" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener relaciones de una carrera específica
curl -X GET "https://tu-dominio/api/ext/relaciones?carrera_id=1" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener materias que imparte un profesor específico
curl -X GET "https://tu-dominio/api/ext/relaciones?profesor_id=42" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener profesores que enseñan en el cuatrimestre 1 de la carrera 1
curl -X GET "https://tu-dominio/api/ext/relaciones?carrera_id=1&cuatrimestre=1" \
  -H "X-API-Key: tu_clave_secreta"

# Obtener solo profesores activos de una carrera
curl -X GET "https://tu-dominio/api/ext/relaciones?carrera_id=1&activo=true" \
  -H "X-API-Key: tu_clave_secreta"
```

**Casos de Uso**:
- Obtener lista de profesores a evaluar en una materia
- Cargar opciones de materias disponibles para un profesor
- Sincronizar estructura académica (profesor-materia-carrera) con sistema externo
- Validar relaciones antes de crear evaluaciones

---

## Casos de Uso Comunes

### Caso 1: Login en Sistema Externo

Un usuario intenta iniciar sesión en el sistema de evaluación docente. El sistema externo debe:

1. Recibir credenciales del usuario
2. Llamar a `POST /api/ext/auth/login` para verificar
3. Si es exitosa, crear sesión en el sistema externo
4. Almacenar información del usuario (roles, carreras, etc.)

```javascript
// En el sistema externo (Next.js)
async function loginUser(username, password) {
  const response = await fetch('https://gestor-horarios.edu/api/ext/auth/login', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.EXTERNAL_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      login: username,
      password: password,
      rol: 'profesor_completo' // opcional: solo profesores
    })
  });

  if (!response.ok) {
    throw new Error('Autenticación fallida');
  }

  return response.json();
}
```

---

### Caso 2: Cargar Carreras en Dropdown

Mostrar lista de carreras disponibles en un formulario:

```javascript
async function loadCareers() {
  const response = await fetch('https://gestor-horarios.edu/api/ext/carreras?activa=true', {
    headers: {
      'X-API-Key': process.env.EXTERNAL_API_KEY
    }
  });

  const { carreras } = await response.json();
  
  // Renderizar opciones
  const select = document.getElementById('carrera-select');
  carreras.forEach(carrera => {
    const option = document.createElement('option');
    option.value = carrera.id;
    option.textContent = `${carrera.nombre} (${carrera.codigo})`;
    select.appendChild(option);
  });
}
```

---

### Caso 3: Cargar Materias por Cuatrimestre y Carrera

Un jefe de carrera quiere ver todas las materias del cuatrimestre 1 de su carrera:

```javascript
async function loadMaterials(carreraId, cuatrimestre) {
  const url = new URL('https://gestor-horarios.edu/api/ext/cuatrimestres/1/materias');
  url.searchParams.set('carrera_id', carreraId);

  const response = await fetch(url, {
    headers: {
      'X-API-Key': process.env.EXTERNAL_API_KEY
    }
  });

  const { materias } = await response.json();
  return materias;
}
```

---

### Caso 4: Obtener Profesores para Evaluación

Un estudiante necesita evaluar a los profesores de sus materias. El sistema obtiene las materias del estudiante y luego obtiene los profesores:

```javascript
async function getProfesorsToEvaluate(carrierId) {
  // 1. Obtener materias de la carrera en cuatrimestre actual
  const materiasResponse = await fetch(
    `https://gestor-horarios.edu/api/ext/cuatrimestres/3/materias?carrera_id=${carrierId}`,
    {
      headers: { 'X-API-Key': process.env.EXTERNAL_API_KEY }
    }
  );
  const { materias } = await materiasResponse.json();

  // 2. Obtener profesores que enseñan estas materias
  const relacionesResponse = await fetch(
    `https://gestor-horarios.edu/api/ext/relaciones?carrera_id=${carrierId}&cuatrimestre=3`,
    {
      headers: { 'X-API-Key': process.env.EXTERNAL_API_KEY }
    }
  );
  const { relaciones } = await relacionesResponse.json();

  return relaciones;
}
```

---

### Caso 5: Sincronización Inicial

Un administrador quiere sincronizar todos los datos académicos del Gestor de Horarios con el sistema externo:

```javascript
async function syncAcademicData() {
  try {
    // 1. Obtener todas las carreras
    const carreras = await fetch('https://gestor-horarios.edu/api/ext/carreras', {
      headers: { 'X-API-Key': process.env.EXTERNAL_API_KEY }
    }).then(r => r.json());

    // 2. Para cada carrera, obtener sus materias
    const materiasPorCarrera = {};
    for (const carrera of carreras.carreras) {
      const cuatrimestres = await fetch(
        `https://gestor-horarios.edu/api/ext/cuatrimestres?carrera_id=${carrera.id}`,
        { headers: { 'X-API-Key': process.env.EXTERNAL_API_KEY } }
      ).then(r => r.json());
      
      materiasPorCarrera[carrera.id] = cuatrimestres.cuatrimestres;
    }

    // 3. Obtener todas las relaciones
    const relaciones = await fetch('https://gestor-horarios.edu/api/ext/relaciones', {
      headers: { 'X-API-Key': process.env.EXTERNAL_API_KEY }
    }).then(r => r.json());

    // 4. Guardar en base de datos local
    await saveSyncData({
      carreras: carreras.carreras,
      materias: materiasPorCarrera,
      relaciones: relaciones.relaciones,
      syncedAt: new Date()
    });

    console.log('Sincronización completada');
  } catch (error) {
    console.error('Error en sincronización:', error);
  }
}
```

---

## Estructura de Datos

### Objeto Usuario

```json
{
  "id": 42,
  "username": "jdoe",
  "nombre": "Juan",
  "apellido": "Doe",
  "nombre_completo": "Juan Doe",
  "email": "juan.doe@university.edu",
  "rol": "profesor_completo",
  "roles": ["profesor_completo", "jefe_carrera"],
  "tipo_profesor": "profesor_completo",
  "activo": true,
  "carreras": [
    {
      "id": 1,
      "nombre": "Ingeniería en Sistemas",
      "codigo": "ISI"
    }
  ]
}
```

### Objeto Carrera

```json
{
  "id": 1,
  "nombre": "Ingeniería en Sistemas",
  "codigo": "ISI",
  "descripcion": "Formación de ingenieros en desarrollo de sistemas informáticos",
  "facultad": "Facultad de Ingeniería",
  "activa": true,
  "fecha_creacion": "2023-01-15T10:30:00"
}
```

### Objeto Materia

```json
{
  "id": 101,
  "nombre": "Programación I",
  "codigo": "ISI-101",
  "descripcion": "Fundamentos de programación",
  "cuatrimestre": 1,
  "creditos": 4,
  "horas_semanales": 4,
  "activa": true,
  "carrera": {
    "id": 1,
    "nombre": "Ingeniería en Sistemas",
    "codigo": "ISI"
  }
}
```

### Objeto Cuatrimestre

```json
{
  "numero": 1,
  "nombre": "Cuatrimestre 1",
  "total_materias": 6,
  "carreras": [
    {
      "id": 1,
      "nombre": "Ingeniería en Sistemas",
      "codigo": "ISI",
      "materias_count": 3
    }
  ]
}
```

### Objeto Relación (Docente-Materia-Carrera)

```json
{
  "profesor": {
    "id": 42,
    "username": "jdoe",
    "nombre": "Juan",
    "apellido": "Doe",
    "nombre_completo": "Juan Doe",
    "email": "juan.doe@university.edu",
    "tipo_profesor": "profesor_completo",
    "activo": true
  },
  "materia": {
    "id": 101,
    "nombre": "Programación I",
    "codigo": "ISI-101",
    "descripcion": "Fundamentos de programación",
    "cuatrimestre": 1,
    "creditos": 4,
    "horas_semanales": 4,
    "activa": true,
    "carrera": {
      "id": 1,
      "nombre": "Ingeniería en Sistemas",
      "codigo": "ISI"
    }
  },
  "carrera": {
    "id": 1,
    "nombre": "Ingeniería en Sistemas",
    "codigo": "ISI"
  }
}
```

---

## Guía de Implementación para NextAuth.js

Si estás integrando con NextAuth.js (como en sistema-evaluacion-docente), aquí está el setup mínimo:

**Archivo: `lib/auth.ts`**

```typescript
import { type NextAuthConfig } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const EXTERNAL_API_KEY = process.env.EXTERNAL_API_KEY || "";
const API_URL = process.env.NEXT_PUBLIC_HORARIOS_API_URL || 
                "https://tu-dominio/api/ext";

export const authConfig: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        login: { label: "Usuario o Email", type: "text" },
        password: { label: "Contraseña", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.login || !credentials?.password) {
          throw new Error("Credenciales inválidas");
        }

        try {
          const res = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-API-Key": EXTERNAL_API_KEY
            },
            body: JSON.stringify({
              login: credentials.login,
              password: credentials.password
            })
          });

          if (!res.ok) {
            throw new Error("Autenticación fallida");
          }

          const data = await res.json();

          if (data.autenticado && data.usuario) {
            return {
              id: data.usuario.id.toString(),
              name: data.usuario.nombre_completo,
              email: data.usuario.email,
              image: null,
              // Propiedades custom
              roles: data.usuario.roles,
              tipo_profesor: data.usuario.tipo_profesor,
              carreras: data.usuario.carreras
            };
          }

          throw new Error(data.error || "Autenticación fallida");
        } catch (error) {
          console.error("Auth error:", error);
          throw error;
        }
      }
    })
  ],
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.roles = (user as any).roles;
        token.tipo_profesor = (user as any).tipo_profesor;
        token.carreras = (user as any).carreras;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user) {
        (session.user as any).roles = token.roles;
        (session.user as any).tipo_profesor = token.tipo_profesor;
        (session.user as any).carreras = token.carreras;
      }
      return session;
    }
  },
  pages: {
    signIn: "/login"
  }
};
```

---

## Notas de Seguridad

1. **API Key**: Mantén `EXTERNAL_API_KEY` en variables de entorno seguras. No la expongas en código frontend.
2. **HTTPS**: Siempre usa HTTPS en producción. El API inyecta headers de seguridad.
3. **Rate Limiting**: El servidor aplica límite de 200 requests por hora por IP.
4. **CORS**: Los requests deben venir del dominio autenticado. Configura CORS si es necesario.
5. **Contraseñas**: Las contraseñas se validan con bcrypt en el servidor. Nunca se retornan.

---

## Contacto y Soporte

Para reportar bugs, sugerencias o integración:

- **Email del Admin**: admin@university.edu
- **Repositorio**: https://github.com/tu-repo/gestor-de-horarios
- **Documentación Adicional**: Ver `API_PROFESORES.md` en el mismo repositorio

---

**Última actualización**: Abril 2026  
**Versión del API**: 1.0
