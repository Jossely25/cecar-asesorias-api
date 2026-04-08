from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import os
import json
from urllib.request import Request, urlopen

aplicacion = Flask(__name__)

CLAVE_API = os.environ.get("CLAVE_API", "CECAR-DEMO-KEY").strip()
MAKE_WEBHOOK_EVENTOS = os.environ.get("MAKE_WEBHOOK_EVENTOS", "").strip()

SOLICITUDES = []
EVENTOS = []
RESPUESTAS_DIRECTAS = []
ASESORIAS = []

URGENCIAS_VALIDAS = {"baja", "media", "alta"}
MEDIOS_ASESORIA_VALIDOS = {"meet", "zoom", "teams", "presencial"}

PALABRAS_COMPLEJAS = {
    "parcial",
    "final",
    "examen",
    "quiz",
    "taller",
    "proyecto",
    "asesoria",
    "asesoría",
    "tema completo",
    "varios puntos",
    "muchas dudas",
    "repaso",
    "sustentacion",
    "sustentación",
    "integracion",
    "integración",
    "webhooks",
    "eventos",
    "google sheets",
    "arquitectura"
}


def ahora_iso():
    return datetime.now().isoformat(timespec="seconds")


def generar_id(prefijo: str) -> str:
    return f"{prefijo}-{str(uuid.uuid4())[:8].upper()}"


def respuesta_error(codigo_http, codigo_error, mensaje, detalles=None):
    return jsonify({
        "ok": False,
        "codigo_error": codigo_error,
        "mensaje": mensaje,
        "detalles": detalles or {}
    }), codigo_http


def validar_api_key():
    clave_recibida = request.headers.get("X-API-key", "").strip()
    return clave_recibida == CLAVE_API


def parsear_fecha_iso(valor: str):
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except Exception:
        return None


def enviar_evento_a_make(evento: dict):
    if not MAKE_WEBHOOK_EVENTOS:
        print("MAKE_WEBHOOK_EVENTOS no está configurado")
        return

    try:
        data = json.dumps(evento, ensure_ascii=False).encode("utf-8")
        req = Request(
            MAKE_WEBHOOK_EVENTOS,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urlopen(req, timeout=8).read()
        print(f"Evento enviado a Make: {evento['tipo_evento']} - {evento['id_evento']}")
    except Exception as e:
        print("Error enviando evento a Make:", str(e))


def registrar_evento(tipo_evento: str, solicitud_id: str, datos=None):
    evento = {
        "id_evento": generar_id("EVT"),
        "tipo_evento": tipo_evento,
        "timestamp": ahora_iso(),
        "solicitud_id": solicitud_id,
        "origen": "api_flask_render",
        "version_evento": "1.0",
        "datos": datos or {}
    }
    EVENTOS.append(evento)
    enviar_evento_a_make(evento)
    return evento


def buscar_solicitud(solicitud_id: str):
    for solicitud in SOLICITUDES:
        if solicitud["id_solicitud"] == solicitud_id:
            return solicitud
    return None


def validar_solicitud(datos: dict):
    campos_obligatorios = [
        "nombre_estudiante",
        "curso",
        "tema",
        "descripcion_duda",
        "nivel_urgencia"
    ]

    for campo in campos_obligatorios:
        if campo not in datos:
            return False, f"Falta el campo obligatorio: {campo}"

    for campo in campos_obligatorios:
        if not isinstance(datos[campo], str) or not datos[campo].strip():
            return False, f"{campo} debe ser texto no vacío"

    urgencia = datos["nivel_urgencia"].strip().lower()
    if urgencia not in URGENCIAS_VALIDAS:
        return False, f"nivel_urgencia debe ser uno de: {', '.join(sorted(URGENCIAS_VALIDAS))}"

    if len(datos["descripcion_duda"].strip()) < 10:
        return False, "descripcion_duda debe tener al menos 10 caracteres"

    if "correo_estudiante" in datos:
        if not isinstance(datos["correo_estudiante"], str) or not datos["correo_estudiante"].strip():
            return False, "correo_estudiante debe ser texto no vacío"

    return True, None


def validar_respuesta_directa(datos: dict):
    campos_obligatorios = ["solicitud_id", "docente", "mensaje"]

    for campo in campos_obligatorios:
        if campo not in datos:
            return False, f"Falta el campo obligatorio: {campo}"

    for campo in campos_obligatorios:
        if not isinstance(datos[campo], str) or not datos[campo].strip():
            return False, f"{campo} debe ser texto no vacío"

    if len(datos["mensaje"].strip()) < 5:
        return False, "mensaje debe tener al menos 5 caracteres"

    return True, None


def validar_asesoria(datos: dict):
    campos_obligatorios = ["solicitud_id", "docente", "fecha_hora", "medio"]

    for campo in campos_obligatorios:
        if campo not in datos:
            return False, f"Falta el campo obligatorio: {campo}"

    for campo in campos_obligatorios:
        if not isinstance(datos[campo], str) or not datos[campo].strip():
            return False, f"{campo} debe ser texto no vacío"

    medio = datos["medio"].strip().lower()
    if medio not in MEDIOS_ASESORIA_VALIDOS:
        return False, f"medio debe ser uno de: {', '.join(sorted(MEDIOS_ASESORIA_VALIDOS))}"

    fecha = parsear_fecha_iso(datos["fecha_hora"].strip())
    if fecha is None:
        return False, "fecha_hora debe estar en formato ISO. Ejemplo: 2026-04-10T18:30:00"

    if "enlace" in datos and not isinstance(datos["enlace"], str):
        return False, "enlace debe ser texto"

    return True, None


def clasificar_solicitud(datos: dict):
    descripcion = datos["descripcion_duda"].strip().lower()
    tema = datos["tema"].strip().lower()
    urgencia = datos["nivel_urgencia"].strip().lower()

    razones = []
    es_compleja = False

    if urgencia == "alta":
        es_compleja = True
        razones.append("urgencia_alta")

    if len(descripcion) > 180:
        es_compleja = True
        razones.append("descripcion_extensa")

    if any(palabra in descripcion or palabra in tema for palabra in PALABRAS_COMPLEJAS):
        es_compleja = True
        razones.append("palabras_clave_complejidad")

    if " y " in descripcion and len(descripcion) > 80:
        es_compleja = True
        razones.append("multiples_puntos_en_la_misma_duda")

    if es_compleja:
        return "compleja", razones or ["requiere_revision_docente"]

    return "simple", razones or ["duda_puntual"]


@aplicacion.get("/")
def inicio():
    return jsonify({
        "servicio": "Sistema Inteligente de Atención y Asesorías Académicas - CECAR",
        "estado": "ok",
        "autenticacion": "Usar header X-API-key",
        "webhook_make_configurado": bool(MAKE_WEBHOOK_EVENTOS),
        "endpoints": [
            "POST /api/v1/solicitudes",
            "POST /api/v1/respuestas-directas",
            "POST /api/v1/asesorias",
            "GET /api/v1/solicitudes",
            "GET /api/v1/solicitudes/<id>",
            "GET /api/v1/eventos",
            "GET /api/v1/dashboard"
        ]
    })


@aplicacion.post("/api/v1/solicitudes")
def crear_solicitud():
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    datos = request.get_json(silent=True) or {}
    es_valido, razon = validar_solicitud(datos)
    if not es_valido:
        return respuesta_error(400, "FORMATO_INVALIDO", "El JSON no cumple el contrato.", {"razon": razon})

    clasificacion, razones = clasificar_solicitud(datos)

    solicitud = {
        "id_solicitud": generar_id("SOL"),
        "recibido_en": ahora_iso(),
        "nombre_estudiante": datos["nombre_estudiante"].strip(),
        "curso": datos["curso"].strip(),
        "tema": datos["tema"].strip(),
        "descripcion_duda": datos["descripcion_duda"].strip(),
        "nivel_urgencia": datos["nivel_urgencia"].strip().lower(),
        "correo_estudiante": datos.get("correo_estudiante", "").strip(),
        "clasificacion": clasificacion,
        "razones_clasificacion": razones,
        "estado": "PENDIENTE_RESPUESTA_DIRECTA" if clasificacion == "simple" else "PENDIENTE_ASESORIA"
    }

    SOLICITUDES.append(solicitud)

    evento_creada = registrar_evento(
        "solicitud_creada",
        solicitud["id_solicitud"],
        {
            "nombre_estudiante": solicitud["nombre_estudiante"],
            "correo_estudiante": solicitud["correo_estudiante"],
            "curso": solicitud["curso"],
            "tema": solicitud["tema"],
            "descripcion_duda": solicitud["descripcion_duda"],
            "nivel_urgencia": solicitud["nivel_urgencia"],
            "estado": solicitud["estado"]
        }
    )

    evento_clasificada = registrar_evento(
        "solicitud_clasificada",
        solicitud["id_solicitud"],
        {
            "nombre_estudiante": solicitud["nombre_estudiante"],
            "correo_estudiante": solicitud["correo_estudiante"],
            "curso": solicitud["curso"],
            "tema": solicitud["tema"],
            "clasificacion": solicitud["clasificacion"],
            "razones": solicitud["razones_clasificacion"],
            "estado": solicitud["estado"]
        }
    )

    evento_adicional = None
    if clasificacion == "compleja":
        evento_adicional = registrar_evento(
            "requiere_asesoria",
            solicitud["id_solicitud"],
            {
                "nombre_estudiante": solicitud["nombre_estudiante"],
                "correo_estudiante": solicitud["correo_estudiante"],
                "curso": solicitud["curso"],
                "tema": solicitud["tema"],
                "nivel_urgencia": solicitud["nivel_urgencia"],
                "motivo": "La solicitud fue clasificada como compleja",
                "clasificacion": solicitud["clasificacion"]
            }
        )

    eventos_generados = [evento_creada, evento_clasificada]
    if evento_adicional:
        eventos_generados.append(evento_adicional)

    return jsonify({
        "ok": True,
        "solicitud": solicitud,
        "eventos_generados": eventos_generados,
        "conteo_solicitudes": len(SOLICITUDES)
    }), 201


@aplicacion.post("/api/v1/respuestas-directas")
def enviar_respuesta_directa():
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    datos = request.get_json(silent=True) or {}
    es_valido, razon = validar_respuesta_directa(datos)
    if not es_valido:
        return respuesta_error(400, "FORMATO_INVALIDO", "El JSON no cumple el contrato.", {"razon": razon})

    solicitud = buscar_solicitud(datos["solicitud_id"].strip())
    if not solicitud:
        return respuesta_error(404, "NO_ENCONTRADA", "La solicitud indicada no existe")

    if solicitud["clasificacion"] != "simple":
        return respuesta_error(
            409,
            "CLASIFICACION_INVALIDA",
            "La solicitud no fue clasificada como simple, por tanto no admite respuesta directa."
        )

    if solicitud["estado"] == "RESPONDIDA":
        return respuesta_error(409, "YA_RESPONDIDA", "La solicitud ya tiene una respuesta directa registrada")

    respuesta = {
        "id_respuesta": generar_id("RPD"),
        "solicitud_id": solicitud["id_solicitud"],
        "docente": datos["docente"].strip(),
        "mensaje": datos["mensaje"].strip(),
        "enviada_en": ahora_iso()
    }

    RESPUESTAS_DIRECTAS.append(respuesta)

    solicitud["estado"] = "RESPONDIDA"
    solicitud["respuesta_directa_id"] = respuesta["id_respuesta"]

    evento = registrar_evento(
        "respuesta_directa_enviada",
        solicitud["id_solicitud"],
        {
            "id_respuesta": respuesta["id_respuesta"],
            "docente": respuesta["docente"],
            "mensaje": respuesta["mensaje"],
            "nombre_estudiante": solicitud["nombre_estudiante"],
            "correo_estudiante": solicitud["correo_estudiante"],
            "curso": solicitud["curso"],
            "tema": solicitud["tema"],
            "clasificacion": solicitud["clasificacion"],
            "estado": solicitud["estado"]
        }
    )

    return jsonify({
        "ok": True,
        "respuesta_directa": respuesta,
        "solicitud_actualizada": solicitud,
        "evento_generado": evento
    }), 201


@aplicacion.post("/api/v1/asesorias")
def programar_asesoria():
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    datos = request.get_json(silent=True) or {}
    es_valido, razon = validar_asesoria(datos)
    if not es_valido:
        return respuesta_error(400, "FORMATO_INVALIDO", "El JSON no cumple el contrato.", {"razon": razon})

    solicitud = buscar_solicitud(datos["solicitud_id"].strip())
    if not solicitud:
        return respuesta_error(404, "NO_ENCONTRADA", "La solicitud indicada no existe")

    if solicitud["clasificacion"] != "compleja":
        return respuesta_error(
            409,
            "CLASIFICACION_INVALIDA",
            "La solicitud no fue clasificada como compleja, por tanto no requiere asesoría."
        )

    if solicitud["estado"] == "ASESORIA_PROGRAMADA":
        return respuesta_error(409, "YA_PROGRAMADA", "La solicitud ya tiene una asesoría programada")

    asesoria = {
        "id_asesoria": generar_id("ASE"),
        "solicitud_id": solicitud["id_solicitud"],
        "docente": datos["docente"].strip(),
        "fecha_hora": datos["fecha_hora"].strip(),
        "medio": datos["medio"].strip().lower(),
        "enlace": datos.get("enlace", "").strip(),
        "programada_en": ahora_iso()
    }

    ASESORIAS.append(asesoria)

    solicitud["estado"] = "ASESORIA_PROGRAMADA"
    solicitud["asesoria_id"] = asesoria["id_asesoria"]

    evento = registrar_evento(
        "asesoria_programada",
        solicitud["id_solicitud"],
        {
            "id_asesoria": asesoria["id_asesoria"],
            "docente": asesoria["docente"],
            "fecha_hora": asesoria["fecha_hora"],
            "medio": asesoria["medio"],
            "enlace": asesoria["enlace"],
            "nombre_estudiante": solicitud["nombre_estudiante"],
            "correo_estudiante": solicitud["correo_estudiante"],
            "curso": solicitud["curso"],
            "tema": solicitud["tema"],
            "clasificacion": solicitud["clasificacion"],
            "estado": solicitud["estado"]
        }
    )

    return jsonify({
        "ok": True,
        "asesoria": asesoria,
        "solicitud_actualizada": solicitud,
        "evento_generado": evento
    }), 201


@aplicacion.get("/api/v1/solicitudes")
def listar_solicitudes():
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    return jsonify({
        "ok": True,
        "total": len(SOLICITUDES),
        "solicitudes": SOLICITUDES
    })


@aplicacion.get("/api/v1/solicitudes/<solicitud_id>")
def obtener_solicitud(solicitud_id):
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    solicitud = buscar_solicitud(solicitud_id)
    if not solicitud:
        return respuesta_error(404, "NO_ENCONTRADA", "La solicitud indicada no existe")

    eventos = [e for e in EVENTOS if e["solicitud_id"] == solicitud_id]
    respuesta = next((r for r in RESPUESTAS_DIRECTAS if r["solicitud_id"] == solicitud_id), None)
    asesoria = next((a for a in ASESORIAS if a["solicitud_id"] == solicitud_id), None)

    return jsonify({
        "ok": True,
        "solicitud": solicitud,
        "eventos": eventos,
        "respuesta_directa": respuesta,
        "asesoria": asesoria
    })


@aplicacion.get("/api/v1/eventos")
def listar_eventos():
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    solicitud_id = request.args.get("solicitud_id", "").strip()

    if solicitud_id:
        eventos_filtrados = [e for e in EVENTOS if e["solicitud_id"] == solicitud_id]
    else:
        eventos_filtrados = EVENTOS

    return jsonify({
        "ok": True,
        "total": len(eventos_filtrados),
        "eventos": eventos_filtrados
    })


@aplicacion.get("/api/v1/dashboard")
def dashboard():
    if not validar_api_key():
        return respuesta_error(401, "NO_AUTORIZADO", "Falta X-API-key o es incorrecta")

    simples = sum(1 for s in SOLICITUDES if s["clasificacion"] == "simple")
    complejas = sum(1 for s in SOLICITUDES if s["clasificacion"] == "compleja")

    return jsonify({
        "ok": True,
        "metricas": {
            "total_solicitudes": len(SOLICITUDES),
            "simples": simples,
            "complejas": complejas,
            "respondidas": len(RESPUESTAS_DIRECTAS),
            "asesorias_programadas": len(ASESORIAS),
            "total_eventos": len(EVENTOS)
        }
    })


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 3000))
    aplicacion.run(host="0.0.0.0", port=puerto)
