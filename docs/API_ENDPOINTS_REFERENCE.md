# 📋 Referencia Completa de API Endpoints - MundoPeludo

## 🔑 Prerequisitos: Autenticación con cURL

### **Paso 1: Obtener CSRF Token**
```bash
curl -c cookies.txt http://localhost:8000/login/
```

### **Paso 2: Login**
```bash
curl -X POST http://localhost:8000/login/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/login/" \
  -d "username=mauricioramirez4747@gmail.com&password=black12345&csrfmiddlewaretoken=TU_CSRF_TOKEN"
```

### **Paso 3: Extraer CSRF Token de cookies.txt**
```bash
# En PowerShell
Get-Content cookies.txt | Select-String "csrftoken"

# En Linux/Mac
grep csrftoken cookies.txt
```

---

## 🌍 ENDPOINTS PÚBLICOS (sin autenticación)

### **Autenticación**

**Verificar estado de autenticación:**
```bash
curl http://localhost:8000/api/auth/status/ \
  -b cookies.txt

# Response (no autenticado):
{"isAuthenticated": false}

# Response (autenticado):
{
  "isAuthenticated": true,
  "userId": 1,
  "userEmail": "user@example.com",
  "userType": "cliente",
  "userName": "Juan Pérez"
}
```

---

### **Productos (Tienda)**

**Listar todos los productos:**
```bash
curl http://localhost:8000/inventario/api/productos/

# Response:
{
  "success": true,
  "total": 25,
  "productos": [
    {
      "id": 10,
      "nombre": "Alimento Premium para Perros 15kg",
      "descripcion": "Alimento balanceado de alta calidad",
      "categoria": "alimento",
      "categoria_nombre": "Alimento",
      "marca": "Royal Canin",
      "precio": 85000.0,
      "descuento_porcentaje": 10.0,
      "precio_final": 76500.0,
      "stock": 45,
      "stock_disponible": true,
      "tipo_animal": "perro",
      "tipo_animal_nombre": "Perro",
      "unidad_medida": "kg",
      "sku": "ALI-ALIPR-001",
      "imagen": "/inventario/imagen/5/",
      "fecha_creacion": "2025-10-15T10:30:00Z"
    }
  ]
}
```

**Filtrar productos:**
```bash
# Por categoría
curl "http://localhost:8000/inventario/api/productos/?categoria=alimento"

# Por animal
curl "http://localhost:8000/inventario/api/productos/?animal=perro"

# Por búsqueda
curl "http://localhost:8000/inventario/api/productos/?busqueda=royal"

# Solo con stock
curl "http://localhost:8000/inventario/api/productos/?disponible=true"

# Ordenar (nombre, -nombre, precio, -precio, -fecha_creacion)
curl "http://localhost:8000/inventario/api/productos/?orden=precio"

# Combinar filtros
curl "http://localhost:8000/inventario/api/productos/?categoria=alimento&animal=perro&orden=precio"
```

**Obtener detalle de un producto:**
```bash
curl http://localhost:8000/inventario/api/productos/10/

# Response:
{
  "success": true,
  "producto": {
    "id": 10,
    "nombre": "Alimento Premium para Perros 15kg",
    "descripcion": "Alimento balanceado de alta calidad para perros adultos",
    "categoria": "alimento",
    "categoria_nombre": "Alimento",
    "marca": "Royal Canin",
    "precio": 85000.0,
    "descuento_porcentaje": 10.0,
    "precio_final": 76500.0,
    "stock": 45,
    "stock_disponible": true,
    "stock_bajo": false,
    "stock_minimo": 5,
    "tipo_animal": "perro",
    "tipo_animal_nombre": "Perro",
    "unidad_medida": "kg",
    "unidad_medida_nombre": "Kilogramo",
    "peso": 15000.0,
    "lote": "LOT2025-456",
    "fecha_vencimiento": "2026-08-15",
    "sku": "ALI-ALIPR-001",
    "palabras_clave": "alimento, comida, perro, premium",
    "total_vendidos": 150,
    "imagenes": [
      {
        "id": 5,
        "url": "/inventario/imagen/5/",
        "nombre_archivo": "royal_canin_15kg.jpg",
        "tipo_contenido": "image/jpeg"
      }
    ],
    "cantidad_imagenes": 1,
    "fecha_creacion": "2025-10-15T10:30:00Z",
    "fecha_actualizacion": "2025-11-10T16:45:00Z"
  }
}
```

### **Especies**

**Listar todas las especies:**
```bash
curl http://localhost:8000/mascotas/api/especies/

# Response:
{
  "especies": [
    {"id": 1, "nombre": "Perro"},
    {"id": 2, "nombre": "Gato"},
    {"id": 3, "nombre": "Ave"}
  ]
}
```

### **Registro de Usuario**

**Registrar nuevo cliente:**
```bash
# Primero obtener CSRF token
curl -c cookies.txt http://localhost:8000/registro/

# Luego registrar
curl -X POST http://localhost:8000/registro/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/registro/" \
  -d "email=nuevo@example.com&nombre=Juan&apellidos=Pérez&password1=MiPassword123&password2=MiPassword123&telefono=5551234&direccion=Calle 123&csrfmiddlewaretoken=TU_CSRF_TOKEN"

# Response exitoso: Redirect 302 a /login/ o dashboard
```

**Registrar nuevo veterinario:**
```bash
curl -X POST http://localhost:8000/registro/veterinario/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/registro/veterinario/" \
  -d "email=vet@example.com&nombre=Dr. Carlos&apellidos=García&password1=VetPass123&password2=VetPass123&telefono=5559999&especialidades=1,2&csrfmiddlewaretoken=TU_CSRF_TOKEN"
```

---

## 🔐 ENDPOINTS PROTEGIDOS (@login_required o IsAuthenticated)

### **👤 Usuario - Perfil**

**Obtener perfil del usuario autenticado:**
```bash
curl http://localhost:8000/api/v1/user/profile/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "id": 1,
  "email": "user@example.com",
  "nombre": "Juan",
  "apellidos": "Pérez",
  "tipo": "cliente",
  "telefono": "555-1234",
  "direccion": "Calle 123"
}
```

**Actualizar perfil del usuario:**
```bash
curl -X PUT http://localhost:8000/api/v1/user/profile/update/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{"nombre": "Juan Carlos", "telefono": "555-5678", "direccion": "Calle 456"}'

# Response:
{
  "success": true,
  "message": "Perfil actualizado correctamente"
}
```

**Obtener información de sesión:**
```bash
curl http://localhost:8000/api/v1/user/session/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "isAuthenticated": true,
  "userType": "cliente",
  "userId": 1,
  "userEmail": "user@example.com"
}
```

### **🐾 Usuario - Mascotas**

**Listar mascotas del usuario:**
```bash
curl http://localhost:8000/api/v1/user/mascotas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 1,
    "nombre": "Firulais",
    "especie": "Perro",
    "raza": "Labrador",
    "edad": 3,
    "peso": 25.5,
    "fecha_nacimiento": "2022-05-15"
  }
]
```

### **📅 Usuario - Citas**

**Listar citas del usuario:**
```bash
curl http://localhost:8000/api/v1/user/citas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 1,
    "fecha": "2025-11-15",
    "hora": "10:00",
    "servicio": "Consulta General",
    "veterinario": "Dr. García",
    "mascota": "Firulais",
    "estado": "Programada"
  }
]
```

### **🛒 Carrito (Inventario)**

**Obtener carrito del usuario:**
```bash
curl http://localhost:8000/inventario/api/carrito/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "carrito": [
    {
      "id": "10",
      "nombre": "Shampoo para perros",
      "precio": 25000.00,
      "cantidad": 2,
      "imagen": "/media/productos/shampoo.jpg",
      "stock": 50,
      "subtotal": 50000.00
    }
  ],
  "total_items": 2,
  "subtotal": 50000.00,
  "total": 50000.00
}
```

**Agregar producto al carrito:**
```bash
curl -X POST http://localhost:8000/inventario/api/carrito/agregar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{"producto_id": 10, "cantidad": 2}'

# Response:
{
  "success": true,
  "message": "Producto agregado al carrito",
  "total_items": 2,
  "item_id": 5
}
```

**Sincronizar carrito desde localStorage:**
```bash
curl -X POST http://localhost:8000/inventario/api/carrito/sincronizar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "carrito": [
      {"id": "10", "nombre": "Shampoo", "precio": 25000, "cantidad": 2, "imagen": "/media/productos/shampoo.jpg"},
      {"id": "15", "nombre": "Collar", "precio": 15000, "cantidad": 1, "imagen": "/media/productos/collar.jpg"}
    ]
  }'

# Response: (igual que GET /inventario/api/carrito/)
```

**Actualizar cantidad de un item:**
```bash
curl -X PUT http://localhost:8000/inventario/api/carrito/actualizar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{"item_id": 5, "cantidad": 3}'

# Response:
{
  "success": true,
  "message": "Cantidad actualizada",
  "total_items": 3
}
```

**Eliminar item del carrito:**
```bash
curl -X DELETE http://localhost:8000/inventario/api/carrito/eliminar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{"item_id": 5}'

# Response:
{
  "success": true,
  "message": "Producto eliminado del carrito"
}
```

**Vaciar todo el carrito:**
```bash
curl -X POST http://localhost:8000/inventario/api/carrito/vaciar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "message": "Carrito vaciado correctamente"
}
```

---

## 👨‍⚕️ ENDPOINTS DE VETERINARIO (@login_required + tipo='veterinario')

**Obtener perfil del veterinario:**
```bash
curl http://localhost:8000/api/v1/vet/perfil/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "email": "vet@example.com",
  "nombre": "Dr. García",
  "apellidos": "López",
  "especialidades": ["Cirugía", "Dermatología"],
  "telefono": "555-9999"
}
```

**Actualizar perfil de veterinario:**
```bash
curl -X PUT http://localhost:8000/api/v1/vet/perfil/actualizar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{"telefono": "555-8888", "especialidades": [1, 2, 3]}'

# Response:
{
  "success": true,
  "message": "Perfil actualizado"
}
```

**Obtener citas del veterinario por fecha:**
```bash
curl http://localhost:8000/citas/fecha/2025-11-15/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 1,
    "hora": "10:00",
    "cliente": "Juan Pérez",
    "mascota": "Firulais",
    "servicio": "Consulta General",
    "estado": "Programada"
  }
]
```

**Obtener todas las citas programadas del veterinario:**
```bash
curl http://localhost:8000/citas/programadas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response: (array de citas)
```

---

## 👑 ENDPOINTS DE ADMINISTRADOR (@login_required + tipo='administrador')

### **📊 Estadísticas**

**Obtener estadísticas generales del sistema:**
```bash
curl http://localhost:8000/dashboard_admin/api/estadisticas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response: {
       "total_clientes": 19,
       "total_veterinarios": 7,
       "total_mascotas": 20,
       "total_citas": 5,
       "citas_por_estado": [
         {"nombre": "Pendiente", "total": 0},
         {"nombre": "Completada", "total": 2},
         {"nombre": "Cancelada", "total": 0},
         {"nombre": "Programada", "total": 3},
         {"nombre": "En Curso", "total": 0}
       ],
       "mascotas_por_especie": [
         {"nombre": "Perro", "total": 4},
         {"nombre": "Gato", "total": 6},
         {"nombre": "Reptil", "total": 1}
       ],
       "clientes_activos": 18,
       "clientes_inactivos": 1,
       "veterinarios_activos": 7,
       "veterinarios_inactivos": 0
     }

GET  /dashboard_admin/api/actividad_reciente/
     → Actividad reciente del sistema
     Response: [
       {
         "id": 1,
         "tipo": "cita_creada",
         "descripcion": "Nueva cita programada",
         "fecha": "2025-11-12T10:30:00Z",
         "usuario": "Juan Pérez"
       }
     ]
```

### **👥 Gestión de Veterinarios**

```
GET  /dashboard_admin/api/veterinarios/
     → Listar todos los veterinarios
     Response: [
       {
         "email": "vet@example.com",
         "nombre": "Dr. García",
         "apellidos": "López",
         "telefono": "555-9999",
         "especialidades": ["Cirugía"],
         "is_active": true
       }
     ]

GET  /dashboard_admin/api/veterinarios/{email}/
     → Obtener detalles de un veterinario específico

PUT  /dashboard_admin/api/veterinarios/{email}/
     → Actualizar veterinario
     Headers: X-CSRFToken
     Body: {
       "nombre": "Dr. Carlos",
       "telefono": "555-8888",
       "is_active": true
     }

DELETE /dashboard_admin/api/veterinarios/{email}/
       → Eliminar veterinario
       Headers: X-CSRFToken

GET  /dashboard_admin/api/veterinarios/{email}/detalle/
     → Detalles completos del veterinario (incluye citas, especialidades)
```

### **👨‍👩‍👧‍👦 Gestión de Clientes**

```
GET  /dashboard_admin/api/clientes/
     → Listar todos los clientes
     Response: [
       {
         "email": "cliente@example.com",
         "nombre": "Juan",
         "apellidos": "Pérez",
         "telefono": "555-1234",
         "direccion": "Calle 123",
         "is_active": true,
         "total_mascotas": 2
       }
     ]

POST /dashboard_admin/api/clientes/nuevo/
     → Crear nuevo cliente
     Headers: X-CSRFToken
     Body: {
       "email": "nuevo@example.com",
       "nombre": "María",
       "apellidos": "García",
       "password": "password123",
       "telefono": "555-5555"
     }

GET  /dashboard_admin/api/clientes/{email}/
     → Obtener detalles de un cliente

PUT  /dashboard_admin/api/clientes/{email}/
     → Actualizar cliente
     Headers: X-CSRFToken

DELETE /dashboard_admin/api/clientes/{email}/
       → Eliminar cliente
       Headers: X-CSRFToken

GET  /dashboard_admin/api/clientes/{cliente_id}/
     → Detalles completos del cliente (incluye mascotas, citas)
```

### **📅 Gestión de Citas**

```
GET  /dashboard_admin/api/citas/
     → Listar todas las citas del sistema
     Response: [
       {
         "id": 1,
         "fecha": "2025-11-15",
         "hora": "10:00",
         "cliente": "Juan Pérez",
         "veterinario": "Dr. García",
         "mascota": "Firulais",
         "servicio": "Consulta General",
         "estado": "Programada"
       }
     ]

GET  /dashboard_admin/api/citas/{cita_id}/
     → Detalles de una cita específica

PATCH /dashboard_admin/api/citas/{cita_id}/
      → Actualizar cita
      Headers: X-CSRFToken
      Body: {
        "estado": "Completada",
        "observaciones": "Consulta realizada exitosamente"
      }

DELETE /dashboard_admin/api/citas/{cita_id}/
       → Eliminar cita
       Headers: X-CSRFToken
```

### **🐾 Gestión de Mascotas**

```
GET  /dashboard_admin/api/mascotas/
     → Listar todas las mascotas
     Response: [
       {
         "id": 1,
         "nombre": "Firulais",
         "especie": "Perro",
         "raza": "Labrador",
         "edad": 3,
         "propietario": "Juan Pérez"
       }
     ]

GET  /dashboard_admin/api/mascotas/{id}/
     → Detalles de una mascota

PUT  /dashboard_admin/api/mascotas/{id}/
     → Actualizar mascota
     Headers: X-CSRFToken

DELETE /dashboard_admin/api/mascotas/{id}/
       → Eliminar mascota
       Headers: X-CSRFToken
```

### **🏥 Especialidades**

```
GET  /dashboard_admin/api/especialidades/
     → Listar todas las especialidades
     Response: [
       {"id": 1, "nombre": "Cirugía"},
       {"id": 2, "nombre": "Dermatología"}
     ]

POST /dashboard_admin/api/especialidades/nueva/
     → Crear nueva especialidad
     Headers: X-CSRFToken
     Body: {"nombre": "Cardiología"}

PUT  /dashboard_admin/api/especialidades/actualizar/{pk}/
     → Actualizar especialidad
     Headers: X-CSRFToken

DELETE /dashboard_admin/api/especialidades/eliminar/{pk}/
       → Eliminar especialidad
       Headers: X-CSRFToken
```

### **🦎 Especies**

```
GET  /dashboard_admin/api/especies/
     → Listar todas las especies
     Response: [
       {"id": 1, "nombre": "Perro"},
       {"id": 2, "nombre": "Gato"}
     ]

POST /mascotas/api/especies/nueva/
     → Crear nueva especie (solo admin)
     Headers: X-CSRFToken
     Body: {"nombre": "Reptil"}

PUT  /mascotas/api/especies/editar/{pk}/
     → Actualizar especie (solo admin)
     Headers: X-CSRFToken

DELETE /mascotas/api/especies/eliminar/{pk}/
       → Eliminar especie (solo admin)
       Headers: X-CSRFToken
```

---

## 👨‍💼 ENDPOINTS DE CLIENTE (@login_required + tipo='cliente')

```
GET  /api/v1/cliente/perfil/
     → Perfil del cliente autenticado

PUT  /api/v1/cliente/perfil/actualizar/
     → Actualizar perfil de cliente
     Headers: X-CSRFToken

GET  /api/v1/cliente/mascotas/
     → Mascotas del cliente

GET  /api/v1/cliente/mascotas/{mascota_id}/
     → Detalles de una mascota específica

GET  /api/v1/cliente/citas/
     → Citas del cliente

POST /api/v1/cliente/citas/solicitar/
     → Solicitar nueva cita
     Headers: X-CSRFToken
     Body: {
       "mascota_id": 1,
       "servicio_id": 2,
       "fecha": "2025-11-20",
       "hora": "10:00",
       "veterinario_id": 3
     }

GET  /api/v1/cliente/historial/
     → Historial médico de todas las mascotas del cliente

GET  /api/v1/cliente/servicios/
     → Servicios disponibles para el cliente
```

---

## 🧪 **GUÍA DE PRUEBAS CON JMETER**

### **ENDPOINTS PÚBLICOS** (Sin autenticación)
```
✅ NO necesitan cookies
✅ NO necesitan CSRF token
✅ Solo HTTP Request directo

Ejemplo JMeter:
  HTTP Request
    Method: GET
    Path: /mascotas/api/especies/
  
  JSON Assertion
    Assert JSON Path: $.especies
```

### **ENDPOINTS PROTEGIDOS** (Con @login_required)
```
✅ Necesitan login previo (cookies)
✅ GET: Solo cookies
✅ POST/PUT/DELETE: Cookies + CSRF token

Ejemplo JMeter:
  1. GET /login/ + extraer CSRF
  2. POST /login/ con credenciales
  3. HTTP Request
       Method: GET
       Path: /api/v1/user/profile/
       Cookie Manager: Automático
  
  JSON Assertion
    Assert JSON Path: $.email
```

### **ENDPOINTS CON PERMISOS** (Admin/Vet/Cliente)
```
✅ Necesitan login con usuario del tipo correcto
✅ Admin: mauricioramirez4747@gmail.com
✅ Veterinario: cuenta con tipo='veterinario'
✅ Cliente: cuenta con tipo='cliente'

Ejemplo JMeter Admin:
  1. Login con cuenta admin
  2. HTTP Request
       Method: GET
       Path: /dashboard_admin/api/estadisticas/
       Cookie Manager: Automático
       Header: X-CSRFToken: ${csrf_token}
  
  JSON Assertion
    Assert JSON Path: $.total_clientes
    Assert JSON Path: $.total_veterinarios
```

---

## 📝 **NOTAS IMPORTANTES**

1. **CSRF Token**: Requerido en todos los métodos POST, PUT, PATCH, DELETE
2. **Cookies**: Se manejan automáticamente con HTTP Cookie Manager en JMeter
3. **Content-Type**: 
   - `application/json` para APIs REST
   - `application/x-www-form-urlencoded` para login
4. **Permisos**: Verificar tipo de usuario antes de probar endpoints protegidos
5. **Estado de sesión**: La sesión dura 48 horas (SESSION_COOKIE_AGE = 172800)

---

## 🔧 **EJEMPLO COMPLETO DE TEST EN JMETER**

```
Thread Group
├── HTTP Cookie Manager ⭐
├── HTTP Request Defaults (localhost:8000)
│
├── 1. GET /login/ 
│   └── Regular Expression Extractor (csrf_token)
│
├── 2. POST /login/
│   └── Response Assertion (200|302)
│
├── 3. GET /api/auth/status/ (PÚBLICO)
│   └── JSON Assertion ($.isAuthenticated = true)
│
├── 4. GET /api/v1/user/profile/ (PROTEGIDO)
│   └── JSON Assertion ($.email exists)
│
├── 5. POST /inventario/api/carrito/agregar/ (PROTEGIDO + CSRF)
│   ├── Header Manager (X-CSRFToken: ${csrf_token})
│   └── JSON Assertion ($.success = true)
│
└── 6. GET /dashboard_admin/api/estadisticas/ (ADMIN ONLY)
    ├── Header Manager (X-CSRFToken: ${csrf_token})
    └── JSON Assertion ($.total_clientes exists)
```
