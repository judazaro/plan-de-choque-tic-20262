# Plan de Choque — Panel de Control

Panel web con diagrama de Gantt y dashboard para dar seguimiento a un plan de choque:
categorías, avance por actividad, dependencias entre tareas, fechas planeadas vs. reales,
y estados automáticos (pendiente / en progreso / completado / atrasado / bloqueada).

No necesita servidor ni instalación: son 2 archivos (`index.html` + `data.json`).

## Qué trae esta versión

- **Panel tipo Power BI**: distribución de tareas por estado (dona), avance por
  categoría, carga de trabajo por responsable y una curva de avance planeado vs.
  real a la fecha, además de un resumen ejecutivo en texto y un banner de alertas.
- **Exportar informe a PDF**: el botón "Exportar informe (PDF)" usa la función de
  impresión del navegador con un formato ya preparado para gerencia (oculta
  botones y formularios, dejando KPIs, gráficas, resumen y tabla). En el diálogo
  de impresión eliges "Guardar como PDF" en vez de una impresora física.
- **Exportar CSV**: descarga la tabla completa de actividades en un archivo que
  abre directamente en Excel/Google Sheets.
- **Notificaciones automáticas**: un script + workflow de GitHub Actions que revisa
  `data.json` todos los días hábiles y avisa si hay actividades atrasadas o por
  vencer (ver sección "Notificaciones automáticas" más abajo).

## Qué trae la versión anterior

- **Categorías**: cada actividad tiene una categoría (ej. Análisis, Operación, Cierre).
  El Gantt las agrupa por secciones de color y hay una leyenda con el avance promedio
  de cada una arriba del cronograma.
- **Dependencias**: una actividad puede depender de una o varias anteriores. En el Gantt
  se dibujan flechas conectando el fin de la tarea previa con el inicio de la que depende
  de ella (puedes ocultarlas con el interruptor "Mostrar dependencias" si se ve muy cargado).
  El panel no te deja crear un ciclo (A depende de B y B depende de A).
- **Fecha planeada vs. fecha real**: cada barra del Gantt muestra dos elementos:
  una línea punteada con las fechas *planeadas* y una barra sólida con las fechas *reales*
  (o las planeadas si aún no hay fecha real) con el % de avance dentro.
- **Estado "Bloqueada"**: se marca sola cuando una actividad ya debería haber empezado
  pero su dependencia previa aún no está completa y su avance sigue en 0%.

## Notificaciones automáticas

Como es un sitio estático (sin servidor propio), las notificaciones "en vivo" se
resuelven con **GitHub Actions**: un robot que corre en horarios programados,
revisa `data.json` y avisa si algo está atrasado o por vencer. Ya viene incluido:

```
.github/workflows/alertas.yml   ← el horario y qué ejecutar
scripts/check_alertas.py        ← la lógica que revisa las fechas
```

**Funciona sin configurar nada extra:** al subir estos archivos al repositorio,
todos los días hábiles a las 8:00 am (hora Colombia/Perú/Ecuador) el robot:
1. Lee `data.json`.
2. Si hay actividades atrasadas o que vencen en los próximos 3 días, crea (o
   actualiza) un **Issue** en tu repositorio titulado "Alertas del plan de choque"
   con el detalle de cada una.
3. Si no hay nada pendiente, cierra ese Issue automáticamente.

Los Issues de GitHub notifican por correo a quienes "watchean" el repositorio,
así que con solo pedirle a tu equipo que le den "Watch" al repo ya reciben el aviso.

**Opcional — también avisar en Slack:**
1. En Slack, crea un "Incoming Webhook" para el canal que quieras (Slack →
   Apps → buscar "Incoming Webhooks" → Add to Slack).
2. Copia la URL que te da.
3. En tu repositorio: Settings → Secrets and variables → Actions → New repository
   secret. Nombre: `SLACK_WEBHOOK_URL`. Valor: la URL copiada.
4. Listo — el mismo mensaje se enviará también a ese canal.

**Para probarlo ya, sin esperar al horario programado:** ve a la pestaña
"Actions" de tu repositorio → "Alertas del plan de choque" → "Run workflow".

**Ajustar el horario o los días de anticipación:** edita el `cron` en
`alertas.yml` (usa horario UTC) o la constante `DIAS_ALERTA_PROXIMA` al inicio
de `check_alertas.py`.

### Recibir las alertas en 2 (o más) correos específicos

Además del Issue y de Slack, el workflow ya trae un paso listo para enviar un
correo por SMTP a las direcciones que tú quieras — no necesita ningún servicio
de pago, solo una cuenta de Gmail (o cualquier otro proveedor SMTP) que actúe
como remitente.

**Paso a paso con Gmail:**

1. **Activa la verificación en dos pasos** en la cuenta de Gmail que va a
   enviar los avisos: [myaccount.google.com/security](https://myaccount.google.com/security)
   → "Verificación en 2 pasos" → actívala (si no lo está).
2. **Genera una "contraseña de aplicación"**: en esa misma sección de
   seguridad, busca "Contraseñas de aplicaciones" (o entra directo a
   [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
   Crea una nueva, ponle un nombre como "Plan de choque", y copia el código de
   16 caracteres que te da. **No es tu contraseña normal de Gmail** — es una
   contraseña especial solo para esto.
3. **En tu repositorio de GitHub**, ve a Settings → "Secrets and variables" →
   "Actions". Ahí vas a crear dos secretos (pestaña "Secrets", botón
   "New repository secret"):
   - `MAIL_USERNAME` → el correo de Gmail que envía (ej. `tuplan@gmail.com`)
   - `MAIL_PASSWORD` → la contraseña de aplicación de 16 caracteres del paso 2
4. **En la pestaña "Variables"** (al lado de "Secrets", mismo menú), crea una
   variable nueva:
   - Nombre: `ALERT_EMAILS`
   - Valor: los dos correos separados por coma, sin espacios, ej.
     `gerencia@empresa.com,coordinacion@empresa.com`
5. Sube (commit) el `alertas.yml` actualizado si no lo has hecho.
6. Pruébalo ya: pestaña "Actions" → "Alertas del plan de choque" → "Run
   workflow". Si hay alguna tarea atrasada o por vencer en tu `data.json`,
   en un minuto debería llegar el correo a ambas direcciones.

**¿Usas Outlook, Yahoo u otro proveedor en vez de Gmail?** Solo cambia
`server_address` y `server_port` en `alertas.yml`:
- Outlook/Office365: `smtp.office365.com`, puerto `587`
- Yahoo: `smtp.mail.yahoo.com`, puerto `465`
(el usuario/contraseña de aplicación se genera de forma parecida, en la
configuración de seguridad de esa cuenta).

**Notas:**
- Si no configuras `MAIL_USERNAME`/`MAIL_PASSWORD`, ese paso simplemente se
  salta — no rompe nada, seguirás recibiendo el Issue en GitHub igual.
- Puedes agregar un tercer, cuarto correo, etc. — solo sepáralos por comas en
  `ALERT_EMAILS`.
- El correo solo se envía cuando hay algo que avisar (tareas atrasadas o por
  vencer). Si todo está al día, no llega ningún correo ese día.

## Cómo usarlo en tu computadora

1. Abre una terminal en esta carpeta.
2. Levanta un servidor local simple (necesario para que `index.html` pueda leer `data.json`):
   ```
   python3 -m http.server 8000
   ```
3. Abre `http://localhost:8000` en tu navegador.

> Si abres `index.html` haciendo doble clic (sin servidor), el navegador bloquea la
> lectura de `data.json` y el panel cargará datos de ejemplo internos en su lugar.
> Para trabajar con tus datos reales, usa siempre el servidor local o publícalo en GitHub Pages.

## Cómo publicarlo en GitHub Pages (para que otros lo vean)

1. Crea un repositorio nuevo en GitHub (público o privado, según quién deba verlo).
2. Sube `index.html` y `data.json` a la raíz del repositorio.
3. Entra a **Settings → Pages**.
4. En "Source" selecciona la rama `main` y la carpeta `/ (root)`. Guarda.
5. En un par de minutos tendrás una URL como:
   `https://tu-usuario.github.io/tu-repositorio/`
6. Comparte esa URL con quienes deban ver el avance del plan.

## Cómo editar las actividades

**A. Desde el panel (recomendado para el día a día)**
- "+ Nueva actividad" para agregar, el lápiz ✎ para editar.
- En el formulario eliges categoría (con sugerencias de las ya usadas), fechas planeadas,
  fechas reales (opcionales, las llenas cuando la tarea de verdad arranca/termina),
  avance, estado y de qué otras actividades depende.
- Los cambios se guardan en el navegador mientras trabajas. Para que se vean en la web
  publicada, haz clic en **"⬇ Descargar data.json"** y sube ese archivo al repositorio,
  reemplazando el anterior.

**B. Editando `data.json` directamente**
```json
{
  "id": "7",
  "categoria": "Operación",
  "nombre": "Nombre de la actividad",
  "responsable": "Quién la ejecuta",
  "dependencias": ["3"],
  "inicio_plan": "2026-09-10",
  "fin_plan": "2026-09-20",
  "inicio_real": "",
  "fin_real": "",
  "avance": 0,
  "estado": "pendiente",
  "prioridad": "alta"
}
```
- `dependencias` es una lista de `id` de otras actividades que deben completarse antes.
- `inicio_real` / `fin_real` se dejan como cadena vacía `""` hasta que la tarea
  realmente empiece o termine.
- `estado` puede ser `pendiente`, `en_progreso` o `completado`. Los estados
  `atrasado` y `bloqueada` los calcula el panel solo, no se escriben a mano.

## Ideas para seguir ampliando

- **Ruta crítica**: resaltar automáticamente la cadena de dependencias más larga,
  que es la que define la fecha mínima de cierre del plan.
- **Alertas por dependencia en riesgo**: avisar cuando una tarea con dependientes
  aguas abajo se atrasa, para anticipar el efecto dominó (hoy el robot solo mira
  fechas individuales, no el impacto en cadena).
- **Historial de avance real**: hoy la curva "plan vs. real" solo compara el avance
  planeado contra el avance actual en un único punto (hoy), porque `data.json` es
  una fotografía del momento, no una serie histórica. Si quieres una curva real
  completa a lo largo del tiempo, la forma más simple es que el workflow de
  Actions guarde una copia diaria de `data.json` (o solo del % de avance) en una
  carpeta `historial/`, y con eso ya se puede graficar la evolución real día a día.
- **Control de acceso**: repo privado + compartir solo el link de Pages, o pedir que
  las ediciones pasen por un Pull Request que tú apruebas.
- **Costos/presupuesto**: agregar un campo `presupuesto` y `gastado` por actividad
  si el plan de choque también necesita seguimiento financiero — encajaría bien
  como otra gráfica de barras junto a las que ya existen.

## Estructura de archivos

```
plan-choque/
├── index.html                        ← el panel (Gantt, dashboard, gráficas, PDF/CSV)
├── data.json                         ← las actividades (esto es lo que editas y subes)
├── README.md                         ← este archivo
├── scripts/
│   └── check_alertas.py              ← lógica de las alertas automáticas
└── .github/
    └── workflows/
        └── alertas.yml               ← horario y configuración de GitHub Actions
```
