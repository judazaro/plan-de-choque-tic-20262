#!/usr/bin/env python3
"""
Revisa data.json y genera alertas para actividades atrasadas o por vencer.

Por defecto, crea o actualiza un Issue de GitHub (usando el token automático
de GitHub Actions, sin configuración adicional). Si se define el secreto
SLACK_WEBHOOK_URL, también envía el mismo aviso a un canal de Slack.

Pensado para ejecutarse desde GitHub Actions (ver .github/workflows/alertas.yml),
pero también funciona en local si defines las variables de entorno necesarias.
"""
import json
import os
import time
import urllib.request
import urllib.error
from datetime import date, timedelta

DIAS_ALERTA_PROXIMA = 3
DATA_PATH = os.environ.get("DATA_PATH", "data.json")
REPO = os.environ.get("GITHUB_REPOSITORY")  # "usuario/repositorio", lo da Actions
TOKEN = os.environ.get("GITHUB_TOKEN")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL")


def cargar_datos():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def evaluar(tareas):
    hoy = date.today()
    limite = hoy + timedelta(days=DIAS_ALERTA_PROXIMA)
    atrasadas, proximas = [], []
    for t in tareas:
        if t.get("estado") == "completado":
            continue
        try:
            fin = date.fromisoformat(t["fin_plan"])
        except (KeyError, ValueError):
            continue
        avance = t.get("avance", 0)
        if fin < hoy and avance < 100:
            atrasadas.append(t)
        elif hoy <= fin <= limite:
            proximas.append(t)
    return atrasadas, proximas


def construir_mensaje(atrasadas, proximas):
    if not atrasadas and not proximas:
        return None
    lineas = ["### Alertas del plan de choque", ""]
    if atrasadas:
        lineas.append(f"**Atrasadas ({len(atrasadas)}):**")
        for t in atrasadas:
            lineas.append(
                f"- {t['nombre']} — responsable: {t.get('responsable', 'sin asignar')} "
                f"— vencía el {t['fin_plan']} — avance {t.get('avance', 0)}%"
            )
        lineas.append("")
    if proximas:
        lineas.append(f"**Por vencer en los próximos {DIAS_ALERTA_PROXIMA} días ({len(proximas)}):**")
        for t in proximas:
            lineas.append(
                f"- {t['nombre']} — responsable: {t.get('responsable', 'sin asignar')} "
                f"— vence el {t['fin_plan']} — avance {t.get('avance', 0)}%"
            )
    return "\n".join(lineas)


def gh_request(method, path, payload=None):
    url = f"https://api.github.com{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "plan-choque-bot",
        },
    )
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        return json.loads(body) if body else None


def actualizar_issue(mensaje):
    if not (TOKEN and REPO):
        print("GITHUB_TOKEN o GITHUB_REPOSITORY no disponibles; se omite la creación del Issue.")
        return
    issues = gh_request("GET", f"/repos/{REPO}/issues?labels=alerta-plan&state=open")
    if mensaje is None:
        for issue in issues or []:
            gh_request("PATCH", f"/repos/{REPO}/issues/{issue['number']}", {"state": "closed"})
        print("Sin alertas pendientes. Issues previos cerrados si existían.")
        return
    if issues:
        numero = issues[0]["number"]
        gh_request("PATCH", f"/repos/{REPO}/issues/{numero}", {"body": mensaje})
        print(f"Issue #{numero} actualizado con las alertas vigentes.")
    else:
        gh_request(
            "POST",
            f"/repos/{REPO}/issues",
            {"title": "Alertas del plan de choque", "body": mensaje, "labels": ["alerta-plan"]},
        )
        print("Issue de alertas creado.")


def enviar_slack(mensaje):
    if not SLACK_WEBHOOK or mensaje is None:
        return
    payload = json.dumps({"text": mensaje}).encode()
    req = urllib.request.Request(
        SLACK_WEBHOOK, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req)
        print("Aviso enviado a Slack.")
    except urllib.error.URLError as e:
        print("No se pudo enviar el aviso a Slack:", e)


def escribir_output(nombre, valor):
    """Expone un valor como 'output' del paso de GitHub Actions, para que el
    siguiente paso del workflow (el que envía el correo) pueda usarlo."""
    ruta = os.environ.get("GITHUB_OUTPUT")
    if not ruta:
        return  # corriendo fuera de Actions; no hay nada que escribir
    delimitador = f"EOF_{int(time.time() * 1000)}"
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(f"{nombre}<<{delimitador}\n{valor}\n{delimitador}\n")


def main():
    datos = cargar_datos()
    atrasadas, proximas = evaluar(datos.get("tareas", []))
    mensaje = construir_mensaje(atrasadas, proximas)
    if mensaje:
        print(mensaje)
    else:
        print("No hay actividades atrasadas ni por vencer.")
    actualizar_issue(mensaje)
    enviar_slack(mensaje)
    escribir_output("hay_alertas", "true" if mensaje else "false")
    escribir_output("mensaje", mensaje or "No hay actividades atrasadas ni por vencer hoy.")


if __name__ == "__main__":
    main()
