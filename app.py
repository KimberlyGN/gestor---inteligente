from flask import Flask, render_template, request, redirect, send_file
import json
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

ARCHIVO_JSON = "actividades.json"


# =========================
# CARGAR Y GUARDAR DATOS
# =========================

def cargar_datos():
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, "r") as f:
            data = json.load(f)

            # Asegurar que todas tengan completada
            for act in data:
                if "completada" not in act:
                    act["completada"] = False

            return data
    return []


def guardar_datos(data):
    with open(ARCHIVO_JSON, "w") as f:
        json.dump(data, f, indent=4)


# =========================
# ANÁLISIS INTELIGENTE
# =========================

def analizar_actividades(actividades):
    total = len(actividades)
    completadas = sum(1 for a in actividades if a.get("completada", False))
    pendientes = total - completadas
    porcentaje = int((completadas / total) * 100) if total > 0 else 0

    if porcentaje == 100:
        mensaje = "Excelente trabajo. Has completado todas tus actividades."
    elif porcentaje >= 50:
        mensaje = "Vas por buen camino, sigue así."
    else:
        mensaje = "Tienes varias tareas pendientes. Organiza tu tiempo."

    return {
        "total": total,
        "completadas": completadas,
        "pendientes": pendientes,
        "porcentaje": porcentaje,
        "mensaje": mensaje
    }


# =========================
# PROMPT ENGINEERING
# =========================

def construir_prompt(actividades):
    texto = "Analiza las siguientes actividades del usuario:\n\n"

    for act in actividades:
        estado = "Completada" if act.get("completada", False) else "Pendiente"
        texto += f"- {act['titulo']} ({act['categoria']}) → {estado}\n"

    texto += """
Basado en esto:
1. Detecta patrones de productividad.
2. Identifica posibles sobrecargas.
3. Sugiere estrategias de mejora.
Responde en un tono motivador y profesional.
"""
    return texto


def generar_recomendacion_llm(actividades):
    if not actividades:
        return "No hay actividades suficientes para generar análisis inteligente."

    total = len(actividades)
    completadas = sum(1 for a in actividades if a.get("completada", False))
    pendientes = total - completadas

    categorias = {}
    for a in actividades:
        categorias[a["categoria"]] = categorias.get(a["categoria"], 0) + 1

    categoria_dominante = max(categorias, key=categorias.get)

    if pendientes > completadas:
        return (
            f"Detecto que tienes mayor carga pendiente en la categoría '{categoria_dominante}'. "
            "Te recomiendo priorizar tareas pequeñas primero para generar impulso y reducir la sensación de sobrecarga."
        )
    else:
        return (
            "Excelente progreso. Mantén tu ritmo actual y considera agrupar tareas similares "
            "para optimizar tu tiempo y energía."
        )


# =========================
# RUTAS
# =========================

@app.route("/")
def index():
    actividades = cargar_datos()
    analisis = analizar_actividades(actividades)
    return render_template("index.html", actividades=actividades, analisis=analisis)


@app.route("/agregar", methods=["POST"])
def agregar():
    actividades = cargar_datos()

    nueva = {
        "titulo": request.form["titulo"],
        "categoria": request.form["categoria"],
        "completada": False
    }

    actividades.append(nueva)
    guardar_datos(actividades)
    return redirect("/")


@app.route("/completar/<int:index>")
def completar(index):
    actividades = cargar_datos()
    actividades[index]["completada"] = not actividades[index].get("completada", False)
    guardar_datos(actividades)
    return redirect("/")


@app.route("/eliminar/<int:index>")
def eliminar(index):
    actividades = cargar_datos()
    actividades.pop(index)
    guardar_datos(actividades)
    return redirect("/")


@app.route("/recomendacion")
def recomendacion():
    actividades = cargar_datos()
    analisis = analizar_actividades(actividades)
    recomendacion = generar_recomendacion_llm(actividades)

    return render_template(
        "index.html",
        actividades=actividades,
        analisis=analisis,
        recomendacion=recomendacion
    )


@app.route("/descargar_pdf")
def descargar_pdf():
    actividades = cargar_datos()

    doc = SimpleDocTemplate("reporte.pdf")
    elementos = []

    estilos = getSampleStyleSheet()
    elementos.append(Paragraph("Reporte de Actividades", estilos["Heading1"]))
    elementos.append(Spacer(1, 0.5 * inch))

    for act in actividades:
        estado = "Completada" if act.get("completada", False) else "Pendiente"
        texto = f"{act['titulo']} - {act['categoria']} - {estado}"
        elementos.append(Paragraph(texto, estilos["Normal"]))
        elementos.append(Spacer(1, 0.2 * inch))

    doc.build(elementos)

    return send_file("reporte.pdf", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)