# 🐾 MundoPeludo — Sistema de Gestión Veterinaria

> **Stack Moderno**: **FastAPI** (Python 3.11) + **Node.js** (Express Proxy) + **React 18** (TypeScript, Tailwind CSS)

Plataforma integral para clínicas veterinarias que gestiona pacientes, agenda de citas, historiales clínicos, centro de adopciones, farmacia/tienda con control de inventario y panel analítico para personal médico y tutores.

---

## 🚀 Arquitectura

```
├── backend/                  # API REST con FastAPI y SQLite
│   ├── main.py               # Endpoints REST y modelos Pydantic
│   ├── database.py           # Conexión SQLite y esquema de tablas
│   ├── seed.py               # Datos iniciales para pruebas
│   ├── requirements.txt      # Dependencias Python
│   └── mundopeludo.db        # Base de datos SQLite
├── src/                      # Frontend SPA React 18 con TypeScript
│   ├── components/           # Vistas (Citas, Mascotas, Tienda, Historial, etc.)
│   ├── api.ts                # Capa cliente de comunicación con FastAPI
│   ├── types.ts              # Tipos TypeScript de dominio
│   └── App.tsx               # Orquestador principal y navegación
├── server.ts                 # Servidor Node.js Express con proxy inverso
├── vite.config.ts            # Configuración Vite con proxy automático a FastAPI
├── legacy_django/            # Versión original preservada de Django
└── package.json              # Dependencias del frontend y servidor
```

---

## ✨ Características Principales

1. **Gestión de Pacientes**: Registro completo de mascotas con peso, edad, especie, estado de esterilización y asociación con su tutor.
2. **Agenda de Citas**: Reservas con duración estimada, asignación de médico veterinario y seguimiento de estados (*Pendiente*, *Confirmada*, *Completada*, *Cancelada*).
3. **Fichas e Historiales Clínicos**: Registro de diagnósticos, tratamientos y observaciones médicas vinculados a citas previas.
4. **Módulo de Adopciones**: Catálogo de mascotas rescatadas con postulación de tutores y flujo de revisión y aprobación administrativa.
5. **Farmacia y Tienda Clínica**: Catálogo de medicamentos, insumos y alimentos con carrito de compras, cálculo de despacho y control de stock mínimo.
6. **Dashboard y Métricas**: Indicadores de rendimiento, citas del día e ingresos calculados en tiempo real.
7. **Simulador de Roles**: Alternancia instantánea entre perfiles de **Cliente**, **Médico Veterinario** y **Administrador**.
8. **Documentación Swagger Interactiva**: Interfaz OpenAPI accesible directamente en `/docs` o mediante el modal de consola en la barra superior.

---

## 🛠️ Instalación y Ejecución Local

### Requisitos Previos
- **Node.js 18+** y `npm`
- **Python 3.10+** y `pip`

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/mundopeludo-fastapi-react.git
cd mundopeludo-fastapi-react
```

### 2. Instalar dependencias
```bash
# Dependencias Node.js
npm install

# Dependencias Python (FastAPI y Uvicorn)
pip install -r backend/requirements.txt
```

### 3. Iniciar el entorno de desarrollo
```bash
npm run dev
```

El servidor Vite levantará automáticamente tanto el frontend como el backend de FastAPI en segundo plano:
- **Aplicación Web**: [http://localhost:3000](http://localhost:3000)
- **Documentación Swagger**: [http://localhost:3000/docs](http://localhost:3000/docs)
- **Especificación OpenAPI**: [http://localhost:3000/openapi.json](http://localhost:3000/openapi.json)

---

## 📦 Construcción para Producción

```bash
# Compilar frontend
npm run build

# Iniciar servidor Node.js
npm start
```

---

## 📁 Versión Histórica (Django)

La implementación anterior basada en Django 5.2 y MySQL ha sido preservada de forma íntegra en la carpeta [`legacy_django/`](./legacy_django/), junto con sus instrucciones y migraciones originales.
