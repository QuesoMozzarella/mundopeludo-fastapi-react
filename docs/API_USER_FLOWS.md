# 🔄 Flujos Completos de Usuario - API MundoPeludo

> **Guía práctica para probar flujos completos de usuarios desde Postman/JMeter**

## 📋 Tabla de Contenidos
- [Prerequisitos](#-prerequisitos)
- [Flujo 1: Cliente Completo](#-flujo-1-cliente-completo)
- [Flujo 2: Veterinario Completo](#-flujo-2-veterinario-completo)
- [Flujo 3: Administrador Completo](#-flujo-3-administrador-completo)

---

## 🔑 Prerequisitos

### **Obtener CSRF Token (necesario para todos los POST)**
```bash
# Guardar cookies en archivo
curl -c cookies.txt http://localhost:8000/login/

# Ver el token en PowerShell
Get-Content cookies.txt | Select-String "csrftoken"

# Extraer el token (ejemplo)
# csrftoken: abc123def456...
```

**Variables a guardar:**
- `CSRF_TOKEN`: Token extraído de cookies
- `BASE_URL`: `http://localhost:8000`

---

## 👤 FLUJO 1: CLIENTE COMPLETO

### **📝 Paso 1: Registrarse como Cliente (con Mascota Obligatoria)**

**⚠️ IMPORTANTE:** El registro de cliente **requiere datos de mascota obligatoriamente**

**Endpoint:** `POST /registro/`

```bash
curl -X POST http://localhost:8000/registro/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/registro/" \
  -d "email=cliente_nuevo@example.com&nombre=Juan&apellidos=Pérez&documento=12345678&password=MiPass123!&password_confirmation=MiPass123!&telefono=5551234567&direccion=Calle Principal 123&mascota_nombre=Firulais&mascota_especie=1&mascota_raza=Labrador&mascota_edad=5&mascota_sexo=Macho&mascota_color=Dorado&mascota_peso=25.5&csrfmiddlewaretoken=TU_CSRF_TOKEN"

# Response: Redirect 302 → /dashboard_cliente/ (éxito, ya logueado)
```

**Postman:**
- Method: `POST`
- URL: `{{BASE_URL}}/registro/`
- Headers:
  - `Content-Type`: `application/x-www-form-urlencoded`
  - `Referer`: `{{BASE_URL}}/registro/`
- Body (x-www-form-urlencoded):
  
  **Datos del Cliente:**
  - `email`: `cliente_nuevo@example.com`
  - `nombre`: `Juan`
  - `apellidos`: `Pérez`
  - `documento`: `12345678`
  - `password`: `MiPass123!`
  - `password_confirmation`: `MiPass123!`
  - `telefono`: `5551234567`
  - `direccion`: `Calle Principal 123`
  
  **Datos de la Mascota (OBLIGATORIOS):**
  - `mascota_nombre`: `Firulais`
  - `mascota_especie`: `1` (ID de especie: 1=Perro, 2=Gato - ver paso previo)
  - `mascota_raza`: `Labrador`
  - `mascota_edad`: `5`
  - `mascota_sexo`: `Macho` (o `Hembra`)
  - `mascota_color`: `Dorado` (opcional)
  - `mascota_peso`: `25.5` (opcional)
  - `mascota_esta_esterilizado`: `true` o `false` (opcional)
  
  **Token:**
  - `csrfmiddlewaretoken`: `{{CSRF_TOKEN}}`

**📋 Paso previo - Obtener IDs de especies:**
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

---

### **🔐 Paso 2: Verificar Sesión (Ya estás logueado automáticamente)**

**💡 Nota:** El registro automáticamente te loguea, **NO necesitas hacer login por separado**.

```bash
curl http://localhost:8000/api/auth/status/ \
  -b cookies.txt

# Response:
{
  "isAuthenticated": true,
  "userId": 15,
  "userEmail": "cliente_nuevo@example.com",
  "userType": "cliente",
  "userName": "Juan Pérez"
}
```

**Si por alguna razón necesitas hacer login manualmente:**
```bash
curl -X POST http://localhost:8000/login/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/login/" \
  -d "username=cliente_nuevo@example.com&password=MiPass123!&csrfmiddlewaretoken=TU_CSRF_TOKEN"

# Response: Redirect 302 → /dashboard_cliente/
```

**Guardar:** La cookie `mundopeludo_sessionid` se guarda automáticamente en `cookies.txt`

---

### **📋 Paso 3: Ver Mis Mascotas**

**💡 Nota:** Ya tienes una mascota registrada (la que creaste durante el registro)

```bash
curl http://localhost:8000/api/v1/cliente/mascotas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 10,
      "nombre": "Firulais",
      "especie": "Perro",
      "raza": "Labrador",
      "edad_años": 5,
      "edad": 5,
      "sexo": "Macho",
      "color": "dorado",
      "peso": 25.5,
      "esta_esterilizado": false,
      "activo": true,
      "fecha_registro": "2025-11-12T10:30:00Z",
      "cliente": {
        "id": 15,
        "nombre": "Juan Pérez",
        "email": "cliente_nuevo@example.com",
        "telefono": "5559876543"
      },
      "propietario": "Juan Pérez",
      "estado_adopcion": "No disponible"
    }
  ]
}
```

---

### **🐶 Paso 4: Agregar Segunda Mascota (Opcional)**

```bash
curl -X POST http://localhost:8000/mascotas/api/mascotas/crear/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "nombre": "Michi",
    "especie": 2,
    "raza": "Persa",
    "fecha_nacimiento": "2021-03-20",
    "peso": 4.2,
    "sexo": "H",
    "color": "Blanco"
  }'

# Response:
{
  "success": true,
  "mascota_id": 11
}
```

---

### **✏️ Paso 5: Modificar Información de Mascota**

```bash
curl -X PUT http://localhost:8000/mascotas/api/mascotas/actualizar/10/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "peso": 27.0,
    "observaciones": "Aumentó de peso, muy activo"
  }'

# Response:
{
  "success": true,
  "message": "Mascota actualizada correctamente"
}
```

---

### **📅 Paso 6: Ver Servicios Disponibles**

```bash
curl http://localhost:8000/api/v1/cliente/servicios/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 1,
    "nombre": "Consulta General",
    "descripcion": "Revisión general del estado de salud de la mascota",
    "activo": true,
    "veterinarios": [5, 7],
    "especialidades": [
      {
        "id": 1,
        "nombre": "Medicina General",
        "codigo": "MED_GEN"
      }
    ]
  },
  {
    "id": 2,
    "nombre": "Vacunación",
    "descripcion": "Aplicación de vacunas preventivas según calendario",
    "activo": true,
    "veterinarios": [5, 8],
    "especialidades": [
      {
        "id": 1,
        "nombre": "Medicina General",
        "codigo": "MED_GEN"
      },
      {
        "id": 2,
        "nombre": "Medicina Preventiva",
        "codigo": "MED_PREV"
      }
    ]
  },
  {
    "id": 3,
    "nombre": "Cirugía",
    "descripcion": "Procedimientos quirúrgicos especializados",
    "activo": true,
    "veterinarios": [7],
    "especialidades": [
      {
        "id": 3,
        "nombre": "Cirugía",
        "codigo": "CIRUGIA"
      }
    ]
  }
]
```

---

### **🩺 Paso 7: Verificar Horarios Disponibles**

```bash
curl -X POST http://localhost:8000/citas/api/horarios-disponibles/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "servicio_id": 1,
    "veterinario_id": 5,
    "fecha": "2025-11-20"
  }'

# Response:
{
  "horarios_disponibles": [
    "09:00",
    "09:30",
    "10:00",
    "10:30",
    "14:00",
    "14:30",
    "15:00"
  ],
  "fecha": "2025-11-20",
  "veterinario": "Dr. García"
}
```

---

### **📝 Paso 8: Solicitar Cita**

```bash
curl -X POST http://localhost:8000/api/v1/cliente/citas/solicitar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "mascota_id": 10,
    "servicio_id": 1,
    "fecha": "2025-11-20",
    "horario": "10:00",
    "motivo": "Chequeo general y actualización de vacunas"
  }'

# Response:
{
  "success": true,
  "message": "Cita solicitada exitosamente",
  "cita_id": 25,
  "data": {
    "fecha": "2025-11-20",
    "horario": "10:00",
    "mascota": "Firulais",
    "servicio": "Consulta General",
    "veterinario": "Carlos García López"
  }
}
```

---

### **📋 Paso 9: Ver Mis Citas**

```bash
curl http://localhost:8000/api/v1/cliente/citas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 25,
      "fecha_hora": "2025-11-20T10:00:00Z",
      "mascota": 10,
      "mascota_nombre": "Firulais",
      "veterinario": 5,
      "veterinario_nombre": "Carlos García López",
      "servicio": 1,
      "servicio_nombre": "Consulta General",
      "estado": 2,
      "estado_nombre": "Programada",
      "motivo": "Chequeo general y actualización de vacunas",
      "notas": null,
      "peso": null,
      "fecha_creacion": "2025-11-10T15:30:00Z"
    },
    {
      "id": 24,
      "fecha_hora": "2025-11-15T14:00:00Z",
      "mascota": 10,
      "mascota_nombre": "Firulais",
      "veterinario": 7,
      "veterinario_nombre": "Ana María Rodríguez",
      "servicio": 2,
      "servicio_nombre": "Vacunación",
      "estado": 4,
      "estado_nombre": "Completada",
      "motivo": "Vacuna antirrábica anual",
      "notas": "Aplicada vacuna antirrábica. Próxima dosis en 1 año.",
      "peso": 26.5,
      "fecha_creacion": "2025-11-05T10:15:00Z"
    }
  ]
}
```

---

### **🛒 Paso 10: Agregar Producto al Carrito**

```bash
# Ver productos disponibles
curl http://localhost:8000/inventario/api/productos/

# Agregar al carrito
curl -X POST http://localhost:8000/inventario/api/carrito/agregar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{"producto_id": 10, "cantidad": 2}'

# Response:
{
  "success": true,
  "message": "Producto agregado al carrito",
  "total_items": 2
}
```
```

---

### **👤 Paso 11: Ver y Actualizar Mi Perfil**

**Ver perfil:**
```bash
curl http://localhost:8000/api/v1/cliente/perfil/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "email": "cliente_nuevo@example.com",
  "nombre": "Juan",
  "apellidos": "Pérez",
  "telefono": "5551234567",
  "direccion": "Calle Principal 123"
}
```

**Actualizar perfil:**
```bash
curl -X PUT http://localhost:8000/api/v1/cliente/perfil/actualizar/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "telefono": "5559876543",
    "direccion": "Nueva Avenida 456, Apto 3B"
  }'

# Response:
{
  "success": true,
  "message": "Perfil actualizado correctamente",
  "data": {
    "email": "cliente_nuevo@example.com",
    "nombre": "Juan",
    "apellidos": "Pérez",
    "telefono": "5559876543",
    "direccion": "Nueva Avenida 456, Apto 3B"
  }
}
```

---

### **🚪 Paso 12: Cerrar Sesión**

```bash
curl -X POST http://localhost:8000/logout/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response: Redirect 302 → /
```

---

## 🩺 FLUJO 2: VETERINARIO COMPLETO

### **⚠️ IMPORTANTE: Registro de Veterinarios**

Los veterinarios **SOLO pueden ser registrados por un Administrador autenticado** desde el dashboard admin.

**Ver Flujo 3 (Admin) - Paso 12 para crear veterinarios.**

---

### **🔐 Paso 1: Iniciar Sesión como Veterinario**

**⚠️ Prerequisito:** El veterinario debe estar **activo** (`activo=True` en su perfil)

```bash
curl -X POST http://localhost:8000/login/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/login/" \
  -d "username=dr.garcia@example.com&password=VetPass123!&csrfmiddlewaretoken=TU_CSRF_TOKEN"

# Response: Redirect 302 → /dashboard_vet/
```

---

### **✅ Paso 2: Verificar Sesión**

```bash
curl http://localhost:8000/api/auth/status/ \
  -b cookies.txt

# Response:
{
  "isAuthenticated": true,
  "userId": 20,
  "userEmail": "dr.garcia@example.com",
  "userType": "veterinario",
  "userName": "Carlos García López"
}
```

---

### **👤 Paso 3: Ver Mi Perfil de Veterinario**

```bash
curl http://localhost:8000/usuarios/api/v1/vet/perfil/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": {
    "email": "dr.garcia@example.com",
    "tipo": "veterinario",
    "nombre": "Carlos",
    "apellidos": "García López",
    "nombre_completo": "Carlos García López",
    "telefono": "5559998877",
    "direccion": "Calle Veterinaria 123",
    "fecha_contratacion": "2025-01-15",
    "documento": "VET12345",
    "especialidades": [
      {"id": 1, "nombre": "Medicina General", "codigo": "MED_GEN"},
      {"id": 2, "nombre": "Cirugía", "codigo": "CIRUGIA"}
    ],
    "activo": true
  }
}
```

---

### **📅 Paso 4: Ver Mi Disponibilidad Actual**

```bash
curl http://localhost:8000/citas/api/v1/disponibilidad/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 1,
    "dia_semana": 1,
    "dia_nombre": "Lunes",
    "hora_inicio": "09:00:00",
    "hora_fin": "17:00:00",
    "activo": true
  },
  {
    "id": 2,
    "dia_semana": 2,
    "dia_nombre": "Martes",
    "hora_inicio": "09:00:00",
    "hora_fin": "17:00:00",
    "activo": true
  }
]
```

---

### **➕ Paso 5: Agregar Nueva Disponibilidad**

```bash
curl -X POST http://localhost:8000/citas/api/v1/disponibilidad/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "dia_semana": 3,
    "hora_inicio": "10:00:00",
    "hora_fin": "18:00:00",
    "activo": true
  }'

# Response:
{
  "id": 5,
  "dia_semana": 3,
  "dia_nombre": "Miércoles",
  "hora_inicio": "10:00:00",
  "hora_fin": "18:00:00",
  "activo": true
}
```

**Días de la semana:**
- `1`: Lunes
- `2`: Martes
- `3`: Miércoles
- `4`: Jueves
- `5`: Viernes
- `6`: Sábado
- `7`: Domingo (0 también funciona)

---

### **✏️ Paso 6: Modificar Disponibilidad**

```bash
curl -X PUT http://localhost:8000/citas/api/v1/disponibilidad/5/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "hora_inicio": "08:00:00",
    "hora_fin": "16:00:00"
  }'

# Response:
{
  "id": 5,
  "dia_semana": 3,
  "hora_inicio": "08:00:00",
  "hora_fin": "16:00:00",
  "activo": true
}
```

---

### **🗑️ Paso 7: Eliminar Disponibilidad**

```bash
curl -X DELETE http://localhost:8000/citas/api/v1/disponibilidad/5/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response: 204 No Content (éxito)
```

---

### **📋 Paso 8: Ver Citas de Hoy**

```bash
curl http://localhost:8000/citas/api/v1/vet/citas_hoy/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 25,
      "fecha_hora": "2025-11-12T10:00:00Z",
      "estado_nombre": "Programada",
      "servicio_nombre": "Consulta General",
      "mascota_nombre": "Firulais",
      "mascota_especie": "Perro",
      "cliente_nombre": "Juan Pérez",
      "motivo": "Chequeo general",
      "notas": null,
      "veterinario_id": 5,
      "mascota_peso": 27.0
    }
  ]
}
```

---

### **📅 Paso 9: Ver Citas Programadas**

```bash
curl http://localhost:8000/citas/api/v1/vet/citas_programadas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 25,
      "fecha_hora": "2025-11-20T10:00:00Z",
      "estado_nombre": "Programada",
      "servicio_nombre": "Consulta General",
      "mascota_nombre": "Firulais",
      "mascota_especie": "Perro",
      "cliente_nombre": "Juan Pérez",
      "motivo": "Chequeo general",
      "notas": null,
      "veterinario_id": 5,
      "mascota_peso": 27.0
    },
    {
      "id": 26,
      "fecha_hora": "2025-11-21T14:30:00Z",
      "estado_nombre": "Programada",
      "servicio_nombre": "Vacunación",
      "mascota_nombre": "Michi",
      "mascota_especie": "Gato",
      "cliente_nombre": "María González",
      "motivo": "Vacunas anuales",
      "notas": null,
      "veterinario_id": 5,
      "mascota_peso": 4.2
    }
  ]
}
```

---

### **✅ Paso 10: Ver Citas Completadas**

```bash
curl http://localhost:8000/citas/api/v1/vet/citas_completadas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 20,
      "fecha_hora": "2025-11-10T11:00:00Z",
      "estado_nombre": "Completada",
      "servicio_nombre": "Consulta General",
      "mascota_nombre": "Rocky",
      "mascota_especie": "Perro",
      "cliente_nombre": "Pedro Martínez",
      "motivo": "Revisión general",
      "notas": "Cita completada - 10/11/2025 11:45",
      "veterinario_id": 5,
      "mascota_peso": 32.0
    }
  ]
}
```

---

### **❌ Paso 11: Ver Citas Canceladas**

```bash
curl http://localhost:8000/citas/api/v1/vet/citas_canceladas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 18,
      "fecha_hora": "2025-11-08T15:00:00Z",
      "estado_nombre": "Cancelada",
      "servicio_nombre": "Vacunación",
      "mascota_nombre": "Luna",
      "mascota_especie": "Gato",
      "cliente_nombre": "Ana Rodríguez",
      "motivo": "Vacunas",
      "notas": "Cliente canceló por emergencia",
      "veterinario_id": 5,
      "mascota_peso": 3.8
    }
  ]
}
```

---

### **🔄 Paso 12: Ver Citas en Curso**

```bash
curl http://localhost:8000/citas/api/v1/vet/citas_en_curso/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 27,
      "fecha_hora": "2025-11-12T09:00:00Z",
      "estado_nombre": "En Curso",
      "servicio_nombre": "Cirugía Menor",
      "mascota_nombre": "Max",
      "mascota_especie": "Perro",
      "cliente_nombre": "Luis Torres",
      "motivo": "Extracción de masa",
      "notas": "Cita en curso - 12/11/2025 09:05",
      "veterinario_id": 5,
      "mascota_peso": 18.5
    }
  ]
}
```

---

### **📝 Paso 13: Ver Detalle de una Cita**

```bash
curl http://localhost:8000/citas/api/v1/citas/25/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": {
    "id": 25,
    "fecha_hora": "2025-11-20T10:00:00Z",
    "estado_id": 2,
    "estado_nombre": "Programada",
    "servicio_id": 1,
    "servicio_nombre": "Consulta General",
    "mascota_id": 10,
    "mascota_nombre": "Firulais",
    "mascota_especie": "Perro",
    "mascota_raza": "Labrador",
    "mascota_edad": 5,
    "mascota_peso": 27.0,
    "cliente_id": 15,
    "cliente_nombre": "Juan Pérez",
    "cliente_telefono": "5559876543",
    "cliente_email": "cliente_nuevo@example.com",
    "motivo": "Chequeo general y actualización de vacunas",
    "notas": null,
    "observaciones": null,
    "estados_disponibles": [
      {"id": 1, "nombre": "Pendiente"},
      {"id": 2, "nombre": "Programada"},
      {"id": 3, "nombre": "En Curso"},
      {"id": 4, "nombre": "Completada"},
      {"id": 5, "nombre": "Cancelada"}
    ]
  }
}
```

---

### **🔄 Paso 14: Cambiar Estado de Cita**

**Estados disponibles:**
- `Programada`
- `En Curso`
- `Completada`
- `Cancelada`

```bash
curl -X PATCH http://localhost:8000/citas/api/v1/citas/25/cambiar_estado/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "estado": "En Curso"
  }'

# Response:
{
  "success": true,
  "message": "Estado de cita actualizado",
  "cita": {
    "id": 25,
    "estado": "En Curso"
  }
}
```

**Completar cita:**
```bash
curl -X PATCH http://localhost:8000/citas/api/v1/citas/25/cambiar_estado/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "estado": "Completada",
    "observaciones": "Paciente en buen estado. Se aplicaron vacunas. Próximo control en 6 meses."
  }'

# Response:
{
  "success": true,
  "message": "Cita completada exitosamente"
}
```

---

## 👑 FLUJO 3: ADMINISTRADOR COMPLETO

### **🔐 Paso 1: Iniciar Sesión como Admin**

```bash
curl -X POST http://localhost:8000/login/ \
  -b cookies.txt \
  -c cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:8000/login/" \
  -d "username=mauricioramirez4747@gmail.com&password=black12345&csrfmiddlewaretoken=TU_CSRF_TOKEN"

# Response: Redirect 302 → /dashboard_admin/
```

---

### **📊 Paso 2: Ver Estadísticas del Sistema**

```bash
curl http://localhost:8000/dashboard_admin/api/estadisticas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "total_clientes": 19,
  "total_veterinarios": 7,
  "total_mascotas": 20,
  "total_citas": 5,
  "citas_por_estado": [
    {"nombre": "Pendiente", "total": 0},
    {"nombre": "Completada", "total": 2},
    {"nombre": "Cancelada", "total": 0},
    {"nombre": "Programada", "total": 3}
  ],
  "mascotas_por_especie": [
    {"nombre": "Perro", "total": 4},
    {"nombre": "Gato", "total": 6}
  ],
  "clientes_activos": 18,
  "clientes_inactivos": 1,
  "veterinarios_activos": 6,
  "veterinarios_inactivos": 1
}
```

---

### **👥 Paso 3: Ver Todos los Clientes**

```bash
curl http://localhost:8000/dashboard_admin/api/clientes/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 15,
    "nombre": "Juan",
    "apellidos": "Pérez",
    "email": "cliente_nuevo@example.com",
    "telefono": "5559876543",
    "direccion": "Nueva Avenida 456",
    "documento": "CLI12345",
    "is_active": true,
    "num_mascotas": 2
  },
  {
    "id": 16,
    "nombre": "María",
    "apellidos": "González",
    "email": "maria@example.com",
    "telefono": "5554443322",
    "direccion": "Calle Principal 123",
    "documento": "CLI67890",
    "is_active": true,
    "num_mascotas": 1
  }
]
```

---

### **🐾 Paso 4: Ver Todas las Mascotas**

```bash
curl http://localhost:8000/dashboard_admin/api/mascotas/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 10,
    "nombre": "Firulais",
    "especie": "Perro",
    "raza": "Labrador",
    "edad_años": 5,
    "activo": true,
    "cliente": {
      "nombre": "Juan",
      "apellidos": "Pérez"
    }
  },
  {
    "id": 11,
    "nombre": "Michi",
    "especie": "Gato",
    "raza": "Persa",
    "edad_años": 4,
    "activo": true,
    "cliente": {
      "nombre": "Juan",
      "apellidos": "Pérez"
    }
  }
]
```

---

### **📦 Paso 5: Ver Productos (Inventario)**

```bash
curl http://localhost:8000/inventario/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Esta ruta devuelve HTML. Para API usar:
# (Nota: No hay endpoint API específico documentado para listar productos,
#  típicamente se maneja desde el panel de admin de Django)
```

**Alternativa - Acceder al admin de Django:**
```
URL: http://localhost:8000/admin/inventario/producto/
```

---

### **➕ Paso 6: Agregar Nuevo Producto**

**(Típicamente se hace desde Django Admin, pero si existe API personalizada):**

```bash
# Verificar si existe endpoint en inventario/urls.py
# Si no existe, crear producto desde /admin/
```

---

### **✏️ Paso 7: Modificar Producto**

```bash
# Similar al paso anterior, verificar endpoints disponibles
# o usar Django Admin: /admin/inventario/producto/{id}/change/
```

---

### **👨‍⚕️ Paso 8: Ver Todos los Veterinarios**

```bash
curl http://localhost:8000/dashboard_admin/api/veterinarios/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
[
  {
    "id": 5,
    "nombre": "Carlos",
    "apellidos": "García López",
    "email": "dr.garcia@example.com",
    "telefono": "5559998877",
    "especialidades": ["Medicina General", "Cirugía"],
    "is_active": true
  },
  {
    "id": 7,
    "nombre": "Ana María",
    "apellidos": "Rodríguez",
    "email": "dra.rodriguez@example.com",
    "telefono": "5558887766",
    "especialidades": ["Medicina Preventiva", "Nutrición"],
    "is_active": true
  }
]
```

---

### **📅 Paso 9: Ver Todas las Citas**

```bash
curl "http://localhost:8000/dashboard_admin/api/citas/?page=1&per_page=15" \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "data": [
    {
      "id": 25,
      "fecha_hora": "2025-11-20T10:00:00Z",
      "estado": "Programada",
      "estado_nombre": "Programada",
      "servicio": "Consulta General",
      "servicio_nombre": "Consulta General",
      "mascota": 10,
      "mascota_nombre": "Firulais",
      "mascota_especie": "Perro",
      "mascota_raza": "Labrador",
      "propietario": "cliente_nuevo@example.com",
      "propietario_nombre": "Juan Pérez",
      "veterinario": "dr.garcia@example.com",
      "veterinario_nombre": "Carlos García López",
      "motivo": "Chequeo general y actualización de vacunas",
      "notas": null,
      "peso": null
    },
    {
      "id": 24,
      "fecha_hora": "2025-11-15T14:00:00Z",
      "estado": "Completada",
      "estado_nombre": "Completada",
      "servicio": "Vacunación",
      "servicio_nombre": "Vacunación",
      "mascota": 10,
      "mascota_nombre": "Firulais",
      "mascota_especie": "Perro",
      "mascota_raza": "Labrador",
      "propietario": "cliente_nuevo@example.com",
      "propietario_nombre": "Juan Pérez",
      "veterinario": "dra.rodriguez@example.com",
      "veterinario_nombre": "Ana María Rodríguez",
      "motivo": "Vacuna antirrábica anual",
      "notas": "Aplicada vacuna antirrábica. Próxima dosis en 1 año.",
      "peso": 26.5
    }
  ],
  "pagination": {
    "count": 5,
    "num_pages": 1,
    "page_number": 1,
    "has_next": false,
    "has_previous": false,
    "next_page_number": null,
    "previous_page_number": null,
    "per_page": 15
  }
}
```

---

### **✏️ Paso 10: Modificar Cita**

```bash
curl -X PATCH http://localhost:8000/dashboard_admin/api/citas/25/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "servicio": 2,
    "veterinario": 7,
    "motivo": "Chequeo general completo",
    "notas": "Reprogramada por solicitud del cliente"
  }'

# Response:
{
  "success": true,
  "message": "Cita actualizada correctamente",
  "cita": {
    "id": 25,
    "servicio": 2,
    "veterinario": 7,
    "motivo": "Chequeo general completo",
    "notas": "Reprogramada por solicitud del cliente"
  }
}
```

---

### **🗑️ Paso 11: Eliminar Cita**

```bash
curl -X DELETE http://localhost:8000/dashboard_admin/api/citas/25/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response:
{
  "success": true,
  "message": "Cita eliminada correctamente"
}
```

---

### **➕ Paso 12: Crear Nuevo Veterinario (desde Admin)**

**⚠️ Este es el método recomendado para registrar veterinarios**

```bash
curl -X POST http://localhost:8000/usuarios/registro/veterinario/ \
  -b cookies.txt \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d "email=dr.nuevo@example.com&nombre=Carlos&apellidos=García&password1=VetPass123!&password2=VetPass123!&telefono=5559998877&documento=VET12345&direccion=Calle Veterinaria 123&especialidades=1&especialidades=2&desde_admin=true&csrfmiddlewaretoken=TU_CSRF_TOKEN"

# Response: Redirect 302 → /dashboard_admin/
```

**Postman:**
- Method: `POST`
- URL: `{{BASE_URL}}/usuarios/registro/veterinario/`
- Headers:
  - `Content-Type`: `application/x-www-form-urlencoded`
  - `X-CSRFToken`: `{{CSRF_TOKEN}}`
- Body (x-www-form-urlencoded):
  - `email`: `dr.nuevo@example.com`
  - `nombre`: `Carlos`
  - `apellidos`: `García`
  - `password1`: `VetPass123!`
  - `password2`: `VetPass123!`
  - `telefono`: `5559998877`
  - `documento`: `VET12345`
  - `direccion`: `Calle Veterinaria 123`
  - `especialidades`: `1` (repetir parámetro para cada especialidad)
  - `especialidades`: `2`
  - `desde_admin`: `true` ⚠️ **IMPORTANTE**
  - `csrfmiddlewaretoken`: `{{CSRF_TOKEN}}`

**💡 Nota:** El veterinario queda **INACTIVO** por defecto. Necesitas activarlo en el siguiente paso.

---

### **✅ Paso 13: Activar/Desactivar Veterinario**

```bash
# Obtener veterinarios para ver el nuevo
curl http://localhost:8000/dashboard_admin/api/veterinarios/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Método 1: Activar/Desactivar usando DELETE (toggle automático)
curl -X DELETE http://localhost:8000/dashboard_admin/api/veterinarios/dr.nuevo@example.com/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response (si estaba inactivo → activar):
{
  "success": true,
  "message": "Veterinario activado correctamente"
}

# Response (si estaba activo → desactivar):
{
  "success": true,
  "message": "Veterinario desactivado correctamente"
}

# Método 2: Actualizar campos usando PUT
curl -X PUT http://localhost:8000/dashboard_admin/api/veterinarios/dr.nuevo@example.com/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "nombre": "Carlos Eduardo",
    "telefono": "5559998800",
    "especialidades": [1, 3]
  }'

# Response:
{
  "success": true,
  "message": "Datos actualizados correctamente"
}
```

---

### **➕ Paso 14: Crear Nuevo Cliente (desde Admin)**

```bash
curl -X POST http://localhost:8000/dashboard_admin/api/clientes/nuevo/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "email": "nuevo_cliente@example.com",
    "nombre": "María",
    "apellidos": "González",
    "password": "ClientePass123!",
    "telefono": "5554443322",
    "direccion": "Calle Secundaria 789"
  }'

# Response:
{
  "success": true,
  "message": "Cliente creado correctamente",
  "cliente": {
    "id": 21,
    "email": "nuevo_cliente@example.com",
    "nombre": "María",
    "apellidos": "González"
  }
}
```

---

### **✏️ Paso 15: Modificar Cliente**

```bash
curl -X PUT http://localhost:8000/dashboard_admin/api/clientes/nuevo_cliente@example.com/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TU_CSRF_TOKEN" \
  -d '{
    "telefono": "5556667788",
    "is_active": true
  }'

# Response:
{
  "success": true,
  "message": "Cliente actualizado correctamente"
}
```

---

### **🗑️ Paso 16: Eliminar Cliente**

```bash
curl -X DELETE http://localhost:8000/dashboard_admin/api/clientes/nuevo_cliente@example.com/ \
  -b cookies.txt \
  -H "X-CSRFToken: TU_CSRF_TOKEN"

# Response (si estaba activo → desactivar):
{
  "success": true,
  "message": "Cliente y sus mascotas desactivados correctamente",
  "nuevo_estado": "inactivo"
}

# Response (si estaba inactivo → activar):
{
  "success": true,
  "message": "Cliente y sus mascotas reactivados correctamente",
  "nuevo_estado": "activo"
}
```

---

## 📝 RESUMEN DE ENDPOINTS POR FLUJO

### **PÚBLICO (sin autenticación):**
- ✅ `GET /inventario/api/productos/` - Listar productos
- ✅ `GET /inventario/api/productos/{id}/` - Detalle de producto
- ✅ `GET /mascotas/api/adopcion/publico/` - Mascotas en adopción
- ✅ `GET /mascotas/api/especies/` - Listar especies
- ✅ `GET /api/auth/status/` - Verificar sesión

### **CLIENTE:**
- ✅ `POST /registro/` - Registrarse
- ✅ `POST /login/` - Iniciar sesión
- ✅ `GET /api/auth/status/` - Verificar sesión
- ✅ `POST /mascotas/api/mascotas/crear/` - Crear mascota
- ✅ `GET /api/v1/cliente/mascotas/` - Ver mis mascotas
- ✅ `PUT /mascotas/api/mascotas/actualizar/{id}/` - Modificar mascota
- ✅ `GET /api/v1/cliente/servicios/` - Ver servicios
- ✅ `POST /citas/api/horarios-disponibles/` - Ver horarios
- ✅ `POST /api/v1/cliente/citas/solicitar/` - Solicitar cita
- ✅ `GET /api/v1/cliente/citas/` - Ver mis citas
- ✅ `GET /inventario/api/carrito/` - Ver mi carrito
- ✅ `POST /inventario/api/carrito/agregar/` - Agregar al carrito
- ✅ `POST /inventario/api/carrito/actualizar/` - Actualizar cantidad
- ✅ `POST /inventario/api/carrito/eliminar/` - Eliminar del carrito
- ✅ `POST /inventario/api/carrito/vaciar/` - Vaciar carrito
- ✅ `GET /api/v1/cliente/perfil/` - Ver perfil
- ✅ `PUT /api/v1/cliente/perfil/actualizar/` - Actualizar perfil
- ✅ `POST /mascotas/api/adopcion/solicitar/{id}/` - Solicitar adopción
- ✅ `GET /mascotas/api/adopcion/mis-solicitudes/` - Mis solicitudes de adopción

### **VETERINARIO:**
- ✅ `POST /registro/veterinario/` - Registrarse
- ✅ `POST /login/` - Iniciar sesión
- ✅ `GET /api/v1/vet/perfil/` - Ver perfil
- ✅ `GET /citas/api/v1/disponibilidad/` - Ver disponibilidad
- ✅ `POST /citas/api/v1/disponibilidad/` - Crear disponibilidad
- ✅ `PUT /citas/api/v1/disponibilidad/{id}/` - Modificar disponibilidad
- ✅ `DELETE /citas/api/v1/disponibilidad/{id}/` - Eliminar disponibilidad
- ✅ `GET /citas/api/v1/vet/citas_hoy/` - Citas de hoy
- ✅ `GET /citas/api/v1/vet/citas_programadas/` - Citas programadas
- ✅ `GET /citas/api/v1/vet/citas_completadas/` - Citas completadas
- ✅ `GET /citas/api/v1/vet/citas_canceladas/` - Citas canceladas
- ✅ `GET /citas/api/v1/vet/citas_en_curso/` - Citas en curso
- ✅ `GET /citas/api/v1/citas/{id}/` - Ver detalle de cita
- ✅ `PATCH /citas/api/v1/citas/{id}/cambiar_estado/` - Cambiar estado

### **ADMINISTRADOR:**
- ✅ `POST /login/` - Iniciar sesión
- ✅ `GET /dashboard_admin/api/estadisticas/` - Estadísticas
- ✅ `GET /dashboard_admin/api/clientes/` - Ver clientes
- ✅ `POST /dashboard_admin/api/clientes/nuevo/` - Crear cliente
- ✅ `PUT /dashboard_admin/api/clientes/{email}/` - Modificar cliente
- ✅ `DELETE /dashboard_admin/api/clientes/{email}/` - Eliminar cliente
- ✅ `GET /dashboard_admin/api/mascotas/` - Ver mascotas
- ✅ `GET /dashboard_admin/api/veterinarios/` - Ver veterinarios
- ✅ `PUT /dashboard_admin/api/veterinarios/{email}/` - Modificar veterinario
- ✅ `DELETE /dashboard_admin/api/veterinarios/{email}/` - Activar/desactivar veterinario
- ✅ `GET /dashboard_admin/api/citas/` - Ver citas (paginado)
- ✅ `PATCH /dashboard_admin/api/citas/{id}/` - Modificar cita
- ✅ `DELETE /dashboard_admin/api/citas/{id}/` - Eliminar cita
- ✅ `GET /mascotas/api/adopcion/admin/solicitudes/` - Ver solicitudes de adopción
- ✅ `POST /mascotas/api/adopcion/admin/procesar/{id}/` - Aprobar/rechazar adopción

---

## 🛍️ EJEMPLOS DE USO - ENDPOINTS DE PRODUCTOS

### **📦 Listar Todos los Productos (Público)**

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
      "descripcion": "Alimento balanceado de alta calidad para perros adultos",
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
    },
    {
      "id": 15,
      "nombre": "Antipulgas Revolution para Gatos",
      "descripcion": "Tratamiento tópico mensual contra pulgas y garrapatas",
      "categoria": "antipulgas",
      "categoria_nombre": "Antipulgas",
      "marca": "Zoetis",
      "precio": 35000.0,
      "descuento_porcentaje": 0.0,
      "precio_final": 35000.0,
      "stock": 20,
      "stock_disponible": true,
      "tipo_animal": "gato",
      "tipo_animal_nombre": "Gato",
      "unidad_medida": "unidad",
      "sku": "ANT-ANTREV",
      "imagen": "/inventario/imagen/12/",
      "fecha_creacion": "2025-10-20T14:15:00Z"
    }
  ]
}
```

**Con filtros:**
```bash
# Filtrar por categoría
curl "http://localhost:8000/inventario/api/productos/?categoria=alimento"

# Filtrar por tipo de animal
curl "http://localhost:8000/inventario/api/productos/?animal=perro"

# Buscar por texto
curl "http://localhost:8000/inventario/api/productos/?busqueda=royal"

# Solo productos con stock
curl "http://localhost:8000/inventario/api/productos/?disponible=true"

# Ordenar por precio ascendente
curl "http://localhost:8000/inventario/api/productos/?orden=precio"

# Ordenar por precio descendente
curl "http://localhost:8000/inventario/api/productos/?orden=-precio"

# Combinar filtros
curl "http://localhost:8000/inventario/api/productos/?categoria=alimento&animal=perro&disponible=true&orden=precio"
```

---

### **🔍 Detalle de Producto (Público)**

```bash
curl http://localhost:8000/inventario/api/productos/10/

# Response:
{
  "success": true,
  "producto": {
    "id": 10,
    "nombre": "Alimento Premium para Perros 15kg",
    "descripcion": "Alimento balanceado de alta calidad para perros adultos de razas medianas y grandes",
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
    "palabras_clave": "alimento, comida, perro, premium, adulto, royal canin",
    "total_vendidos": 150,
    "imagenes": [
      {
        "id": 5,
        "url": "/inventario/imagen/5/",
        "nombre_archivo": "royal_canin_15kg.jpg",
        "tipo_contenido": "image/jpeg"
      },
      {
        "id": 6,
        "url": "/inventario/imagen/6/",
        "nombre_archivo": "royal_canin_detalle.jpg",
        "tipo_contenido": "image/jpeg"
      }
    ],
    "cantidad_imagenes": 2,
    "fecha_creacion": "2025-10-15T10:30:00Z",
    "fecha_actualizacion": "2025-11-10T16:45:00Z"
  }
}
```

---

## 🎯 CHECKLIST RÁPIDO

### **Para Cliente:**
```
1. ✅ Registrarse → Login → Verificar sesión
2. ✅ Crear mascota(s)
3. ✅ Ver servicios disponibles
4. ✅ Ver horarios y solicitar cita
5. ✅ Ver mis citas
6. ✅ Agregar productos al carrito
7. ✅ Actualizar perfil
```

### **Para Veterinario:**
```
1. ✅ Registrarse → Login → Verificar sesión
2. ✅ Ver/modificar perfil
3. ✅ Configurar disponibilidad (CRUD completo)
4. ✅ Ver citas por estado (hoy, programadas, completadas, canceladas, en curso)
5. ✅ Ver detalle de citas
6. ✅ Cambiar estado de citas
```

### **Para Admin:**
```
1. ✅ Login → Ver estadísticas
2. ✅ Gestionar clientes (CRUD)
3. ✅ Ver todas las mascotas
4. ✅ Ver todos los veterinarios
5. ✅ Gestionar citas (leer, modificar, eliminar)
6. ⚠️ Gestionar productos (usar Django Admin)
```

---

## 📚 NOTAS FINALES

1. **Todos los POST/PUT/PATCH/DELETE** requieren header `X-CSRFToken`
2. **Cookies** se manejan automáticamente con `-b cookies.txt -c cookies.txt`
3. **Formato de fechas**: `YYYY-MM-DD` (ej: `2025-11-20`)
4. **Formato de horas**: `HH:MM:SS` o `HH:MM` (ej: `10:00:00` o `10:00`)
5. **IDs de especies**: Obtener con `GET /mascotas/api/especies/`
6. **IDs de especialidades**: Obtener con `GET /dashboard_admin/api/especialidades/`
7. **Estados de cita**: `Programada`, `En Curso`, `Completada`, `Cancelada`

---

**✨ ¡Documentación lista para pruebas completas con Postman/JMeter!**
