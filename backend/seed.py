import os
import sys
import sqlite3
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db

def seed_database():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("Base de datos ya poblada. Omitiendo seed.")
            return

        print("Poblando base de datos inicial de MundoPeludo...")

        # 1. Especies
        especies = [
            ("Canino (Perro)",),
            ("Felino (Gato)",),
            ("Ave",),
            ("Roedor",),
            ("Reptil",)
        ]
        cursor.executemany("INSERT INTO especies (nombre) VALUES (?)", especies)

        # 2. Usuarios (Clientes, Veterinarios, Administrador)
        users = [
            (1, "admin@mundopeludo.com", "admin123", "Maurizio", "Ramírez", "+56 9 8765 4321", "Av. Providencia 1234, Santiago", "administrador", "18.234.567-8", "Director General", 1),
            (2, "vet.garcia@mundopeludo.com", "vet123", "Dra. Andrea", "García Morales", "+56 9 7654 3210", "Calle Los Leones 540, Santiago", "veterinario", "16.890.123-4", "Cirugía y Medicina Interna", 1),
            (3, "vet.martinez@mundopeludo.com", "vet123", "Dr. Felipe", "Martínez Soto", "+56 9 6543 2109", "Av. Vitacura 2300, Santiago", "veterinario", "17.456.789-0", "Dermatología y Animales Exóticos", 1),
            (4, "maria.gonzalez@example.com", "cliente123", "María", "González Rojas", "+56 9 5432 1098", "Pasaje Miraflores 88, Las Condes", "cliente", "19.345.678-9", None, 1),
            (5, "carlos.ramirez@example.com", "cliente123", "Carlos", "Ramírez Vega", "+56 9 4321 0987", "Av. Apoquindo 4500, Santiago", "cliente", "20.123.456-7", None, 1),
            (6, "camila.valenzuela@example.com", "cliente123", "Camila", "Valenzuela Silva", "+56 9 3210 9876", "Calle Suecia 910, Providencia", "cliente", "18.765.432-1", None, 1)
        ]
        cursor.executemany("""
            INSERT INTO users (id, email, password, nombre, apellidos, telefono, direccion, tipo, documento, especialidad, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, users)

        # 3. Servicios
        servicios = [
            (1, "Consulta General y Preventiva", "Evaluación clínica integral de signos vitales, peso, ojos, orejas, pelaje y asesoría nutricional.", 30, 18000.0, 1),
            (2, "Vacunación y Desparasitación", "Administración de vacunas esenciales (Óctuple, Antirrábica, Triple Felina) y antiparasitarios internos.", 20, 22000.0, 1),
            (3, "Cirugía Menor y Esterilización", "Esterilización de machos y hembras, remoción de quistes y suturas en quirófano de alta tecnología.", 60, 65000.0, 1),
            (4, "Peluquería y Estética Canina", "Baño medicado, corte de pelo especializado por raza, corte de uñas y limpieza de oídos.", 45, 25000.0, 1),
            (5, "Odontología y Profilaxis", "Limpieza dental ultrasónica para prevención de sarro, gingivitis y halitosis con sedación segura.", 40, 45000.0, 1),
            (6, "Atención de Urgencias 24/7", "Tratamiento de traumas, intoxicaciones agudas, emergencias respiratorias y estabilización inmediata.", 60, 35000.0, 1)
        ]
        cursor.executemany("""
            INSERT INTO servicios (id, nombre, descripcion, duracion_min, precio, activo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, servicios)

        # 4. Mascotas
        mascotas = [
            (1, 4, 1, "Rocky", "Golden Retriever", 3, "Macho", "Dorado brillante", 28.5, 1, 1, "2024-01-15", "normal", "https://images.unsplash.com/photo-1552053831-71594a27632d?w=600&auto=format&fit=crop&q=80", "Perro muy activo, sociable y amigable con niños."),
            (2, 4, 2, "Luna", "Siamés", 2, "Hembra", "Crema y café", 4.2, 1, 1, "2024-03-20", "normal", "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&auto=format&fit=crop&q=80", "Gata tranquila, le encanta tomar siestas al sol."),
            (3, 5, 1, "Toby", "Beagle", 4, "Macho", "Tricolor", 14.0, 1, 1, "2023-11-10", "normal", "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?w=600&auto=format&fit=crop&q=80", "Muy juguetón con olfato increíble, adora pasear en el parque."),
            (4, 6, 2, "Milo", "Europeo Común", 1, "Macho", "Atigrado gris", 3.8, 0, 1, "2024-06-05", "normal", "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=600&auto=format&fit=crop&q=80", "Gatito juguetón y curioso, en proceso de vacunación."),
            # Mascotas en adopción
            (5, None, 1, "Max", "Pastor Alemán Mestizo", 2, "Macho", "Negro y fuego", 24.0, 1, 1, "2024-07-01", "en_adopcion", "https://images.unsplash.com/photo-1589941013453-ec89f33b5455?w=600&auto=format&fit=crop&q=80", "Rescatado con mucho amor. Inteligente, fiel, protector y muy cariñoso. Busca un hogar activo."),
            (6, None, 2, "Bella", "Angora Mestizo", 1, "Hembra", "Blanco puro", 3.2, 1, 1, "2024-07-10", "en_adopcion", "https://images.unsplash.com/photo-1543852786-1cf6624b9987?w=600&auto=format&fit=crop&q=80", "Rescatada con sus hermanitos. Ronronea sin parar, adora los mimos y convive excelente con otros gatos."),
            (7, None, 1, "Coco", "Cocker Spaniel Mestizo", 3, "Macho", "Caramelo", 12.5, 1, 1, "2024-08-01", "en_adopcion", "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=600&auto=format&fit=crop&q=80", "De mirada tierna y temperamento pacífico. Ideal para departamento o casa con patio pequeño.")
        ]
        cursor.executemany("""
            INSERT INTO mascotas (id, cliente_id, especie_id, nombre, raza, edad_anos, sexo, color, peso, esta_esterilizado, activo, fecha_registro, estado_adopcion, imagen_url, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, mascotas)

        # 5. Citas iniciales
        citas = [
            (1, 1, 2, 1, "2026-09-10 10:00:00", 28.5, "Chequeo semestral preventivo y control de peso", "El tutor reporta que come con normalidad", "Confirmada"),
            (2, 2, 2, 2, "2026-09-12 11:30:00", 4.2, "Refuerzo vacuna Triple Felina", "Revisión previa de temperatura", "Pendiente"),
            (3, 3, 3, 5, "2026-09-08 16:00:00", 14.0, "Limpieza dental por acumulación leve de sarro", "Ayuno previo de 8 horas", "Confirmada"),
            (4, 4, 3, 4, "2026-09-04 15:00:00", 3.8, "Baño sanitario y corte de uñas", "Atención realizada sin inconvenientes", "Completada")
        ]
        cursor.executemany("""
            INSERT INTO citas (id, mascota_id, veterinario_id, servicio_id, fecha_hora, peso, motivo, notas, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, citas)

        # 6. Historial Médico vinculado a cita completada
        cursor.execute("""
            INSERT INTO historiales_medicos (id, cita_id, mascota_id, veterinario_id, diagnostico, tratamiento, observaciones, fecha_creacion)
            VALUES (
                1, 4, 4, 3,
                'Paciente en excelente condición nutricional (Body Score 5/9). Sin ectoparásitos visibles, mucosa oral rosada hidratada.',
                'Baño con champú hipoalergénico de avena, recorte ungular cuidadoso y limpieza ótica con solución antiséptica.',
                'Continuar alimentación premium para cachorro y programar esterilización para el próximo mes.',
                '2026-09-04 15:45:00'
            )
        """)

        # 7. Solicitud de adopción de ejemplo
        cursor.execute("""
            INSERT INTO solicitudes_adopcion (id, mascota_id, cliente_id, fecha_solicitud, estado, notas_cliente, notas_revisor, revisado_por)
            VALUES (
                1, 5, 5, '2026-09-05 14:20:00', 'pendiente',
                'Tengo una casa con patio grande cerrado y experiencia previa con pastores alemanes. Vivirá con nosotros adentro de la casa.',
                'Pendiente de entrevista y verificación de domicilio.', NULL
            )
        """)

        # 8. Productos (Inventario / Tienda)
        productos = [
            (1, "Alimento Royal Canin Maxi Adult 15kg", "Nutrición a la medida para perros adultos de razas grandes (26-44 kg). Refuerza articulaciones y digestión.", "alimento", "Royal Canin", 64990.0, 10.0, 18, 5, 42, "perro", "kg", 15.0, "ALI-ROY-001", "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500&auto=format&fit=crop&q=80"),
            (2, "Antipulgas Bravecto 20-40kg (1 comprimido)", "Protección masticable contra pulgas y garrapatas de hasta 12 semanas continuas de duración.", "antipulgas", "MSD", 34990.0, 5.0, 25, 6, 88, "perro", "unidad", 0.05, "ANT-BRA-002", "https://images.unsplash.com/photo-1608248597359-5972825d18d8?w=500&auto=format&fit=crop&q=80"),
            (3, "Alimento Hills Science Diet Feline Adult 7kg", "Fórmula equilibrada para gatos adultos con taurina y antioxidantes clínicamente comprobados.", "alimento", "Hills", 48990.0, 15.0, 12, 4, 31, "gato", "kg", 7.0, "ALI-HIL-003", "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500&auto=format&fit=crop&q=80"),
            (4, "Shampoo Medicado Clorhexidina 250ml", "Shampoo antiséptico y antifúngico indicado para el tratamiento de dermatitis y piodermas.", "higiene", "Drag Pharma", 12500.0, 0.0, 30, 8, 54, "ambos", "ml", 250.0, "HIG-CLO-004", "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=500&auto=format&fit=crop&q=80"),
            (5, "Amoxicilina + Ácido Clavulánico 500mg (10 comp)", "Antibiótico de amplio espectro para infecciones respiratorias, urinarias y cutáneas.", "medicamento", "Cheminova", 9900.0, 0.0, 4, 10, 19, "ambos", "caja", 0.1, "MED-AMO-005", "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=500&auto=format&fit=crop&q=80"),
            (6, "Juguete Kong Classic Talla L", "Juguete de caucho natural ultra resistente para rellenar con snacks, alivia ansiedad por separación.", "juguete", "KONG", 16990.0, 20.0, 15, 5, 65, "perro", "unidad", 0.2, "JUG-KON-006", "https://images.unsplash.com/photo-1576201836106-db1758fd1c97?w=500&auto=format&fit=crop&q=80"),
            (7, "Suplemento Condrovet Force HA (120 comp)", "Condroprotector para la salud y regeneración del cartílago articular en perros.", "suplemento", "Bioibérica", 42990.0, 8.0, 8, 3, 22, "perro", "caja", 0.3, "SUP-CON-007", "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=80"),
            (8, "Rascador Torre para Gatos 3 Niveles", "Rascador con postes de sisal natural, plataforma acolchada y cueva de descanso.", "accesorio", "CatLovers", 38990.0, 12.0, 6, 2, 14, "gato", "unidad", 4.5, "ACC-RAS-008", "https://images.unsplash.com/photo-1545249390-6bdfa286032f?w=500&auto=format&fit=crop&q=80")
        ]
        cursor.executemany("""
            INSERT INTO productos (id, nombre, descripcion, categoria, marca, precio, descuento_porcentaje, stock, stock_minimo, total_vendidos, tipo_animal, unidad_medida, peso, sku, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, productos)

        print("Base de datos MundoPeludo poblada exitosamente!")

if __name__ == "__main__":
    seed_database()
