# CECAR Asesorías API

## Descripción

Este proyecto corresponde a una **API REST desarrollada con Flask** para la gestión de asesorías académicas de la Corporación Universitaria del Caribe (CECAR).

La API permite administrar la información relacionada con las asesorías, facilitando el registro, consulta y gestión de los datos mediante servicios HTTP.

---

## Objetivos

- Implementar una API REST con Python y Flask.
- Exponer endpoints para la gestión de asesorías.
- Facilitar la integración con aplicaciones web o móviles.
- Demostrar el uso de servicios REST desplegados en la nube mediante Render.

---

## Tecnologías

- Python 3
- Flask
- REST API
- Render
- JSON

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/USUARIO/cecar-asesorias-api.git

cd cecar-asesorias-api
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el proyecto

```bash
python main.py
```

La aplicación estará disponible en:

```
http://localhost:10000
```

---

## Endpoints

### Obtener asesorías

```
GET /asesorias
```

Retorna el listado de asesorías registradas.

---

### Obtener una asesoría

```
GET /asesorias/<id>
```

Consulta una asesoría específica.

---

### Registrar una asesoría

```
POST /asesorias
```

Ejemplo de solicitud:

```json
{
    "estudiante": "Juan Pérez",
    "docente": "María González",
    "materia": "Programación Web",
    "fecha": "2026-07-20",
    "hora": "14:00"
}
```

Respuesta:

```json
{
    "mensaje": "Asesoría registrada correctamente"
}
```

---

### Actualizar una asesoría

```
PUT /asesorias/<id>
```

Permite modificar la información de una asesoría existente.

---

### Eliminar una asesoría

```
DELETE /asesorias/<id>
```

Elimina una asesoría del sistema.

---

## Ejemplo de respuesta

```json
[
    {
        "id": 1,
        "estudiante": "Juan Pérez",
        "docente": "María González",
        "materia": "Base de Datos",
        "fecha": "2026-07-20",
        "hora": "09:00"
    }
]
```

---

## Estructura del proyecto

```
.
├── main.py
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Despliegue en Render

El proyecto incluye el archivo **render.yaml**, por lo que puede desplegarse directamente en Render.

Configuración:

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
python main.py
```

---

## Características

- API REST.
- Intercambio de datos en formato JSON.
- Operaciones CRUD.
- Despliegue en la nube mediante Render.
- Código simple para fines académicos.

---

## Autor

Proyecto académico desarrollado para la asignatura de Desarrollo de APIs REST en la **Corporación Universitaria del Caribe (CECAR)**.
