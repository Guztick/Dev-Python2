# Instalar y ejecutar DiagnósticoPro en PC (Windows + VS Code)

## Inicio rápido (lo más fácil) ⚡

1. Instala **Python 3.10 o superior** desde https://www.python.org/downloads/  
   ⚠️ Marca **"Add Python to PATH"** durante la instalación.
2. Haz **doble clic en `iniciar.bat`**.

Eso es todo. La primera vez, el `.bat`:
- crea el entorno virtual,
- instala las dependencias automáticamente,
- y abre la aplicación.

Las siguientes veces solo abre la app (ya queda todo instalado).

Selecciona **Demo** → **CONECTAR** para navegar toda la interfaz sin
adaptador físico.

---

## Requisitos previos

- **Python 3.10 o superior** — https://www.python.org/downloads/  
  ⚠️ Marca **"Add Python to PATH"**
- **Git** (opcional, para actualizar) — https://git-scm.com/downloads
- **VS Code** (opcional) — https://code.visualstudio.com/ con la extensión Python

---

## Archivos `.bat` incluidos

| Archivo | Para qué sirve |
|---------|----------------|
| **`iniciar.bat`** | Ejecuta la app. Crea el entorno e instala dependencias la primera vez. Usa el lanzador `py` de Windows. |
| **`instalar.bat`** | Solo instala/repara las dependencias, sin abrir la app. |

Ambos detectan automáticamente el lanzador `py` (o `python` como respaldo).

---

## Ejecutar y testear desde VS Code

1. **File → Open Folder** → selecciona la carpeta del proyecto.
2. La carpeta incluye configuración lista en `.vscode/`:
   - **F5** → ejecuta `run.py` con el depurador (configuración *"DiagnosticoPro (ejecutar)"*).
   - **Terminal → Run Task → "Ejecutar DiagnosticoPro (iniciar.bat)"** → lanza el `.bat`.
   - **Terminal → Run Task → "Verificar dependencias"** → comprueba que todo esté instalado.
3. Si VS Code no toma el intérprete del entorno virtual:  
   `Ctrl+Shift+P` → **Python: Select Interpreter** → elige `venv\Scripts\python.exe`.

El programa se ejecuta con **`py run.py`** (o `python run.py` dentro del venv).

---

## Instalación manual (alternativa al `.bat`)

Si prefieres hacerlo a mano en la terminal:

```bash
REM 1. Crear entorno virtual
py -m venv venv

REM 2. Activarlo
venv\Scripts\activate

REM 3. Instalar dependencias
pip install -r requirements-pc.txt

REM 4. Ejecutar
py run.py
```

---

## Conectar un adaptador ELM327 real

La app soporta **USB, Bluetooth y WiFi**.

### ELM327 por USB

1. Conecta el adaptador al puerto OBD-II del vehículo y al PC por USB.
2. Windows intenta instalar el driver automáticamente.  
   **Si el adaptador no aparece**, usa el asistente de drivers de la app
   (ver sección siguiente).
3. Abre el **Administrador de dispositivos** → *Puertos COM y LPT* → anota
   el número (ej: `COM3`).
4. En la app: **USB** → escribe `COM3` → **CONECTAR**.

### ELM327 por Bluetooth

1. Conecta el adaptador al puerto OBD-II (ignición en contacto).
2. Windows: **Configuración → Bluetooth → Agregar dispositivo**.  
   PIN habitual: `1234` o `0000`.
3. Al emparejar, Windows crea un **puerto COM saliente** (ej: `COM5`).  
   Para verlo: **Administrador de dispositivos → Puertos COM y LPT**, o
   *Más opciones Bluetooth → pestaña COM*.
4. En la app: **Bluetooth** → escribe `COM5` → **CONECTAR**.  
   O pulsa **BUSCAR DISPOSITIVOS** — la app lista los puertos COM y los
   dispositivos Bluetooth emparejados, marcando los OBD con ⭐.

> Los adaptadores Bluetooth **no necesitan driver**: usan el perfil SPP
> estándar de Windows.

### ELM327 por WiFi

1. Conéctate a la red WiFi del adaptador (SSID tipo `WiFi_OBDII`).
2. En la app: **WiFi** → IP por defecto `192.168.0.10:35000` → **CONECTAR**.

---

## Asistente de drivers (USB)

La app puede ayudarte a instalar el driver correcto de tu adaptador USB:

1. En la pantalla de conexión, pulsa **"¿Problemas con el adaptador USB?
   Verificar drivers"**.
2. La app analiza los adaptadores conectados e identifica el **chip**
   (CH340, CP210x, FTDI, PL2303…).
3. Te indica si el driver está **instalado** ✓ o **falta** ⚠️.
4. Si falta:
   - Si colocaste el instalador en la carpeta `drivers/` → la app lo ejecuta.
   - Si no → la app abre la **página de descarga oficial** del driver.
5. También puedes abrir el **Administrador de dispositivos** desde ahí.

Consulta `drivers/README.md` para saber qué instalador descargar según tu chip.

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `Python no está en el PATH` | Reinstala Python marcando "Add Python to PATH" |
| `No module named 'kivy'` | Ejecuta `instalar.bat` o `pip install -r requirements-pc.txt` |
| La ventana no abre / error SDL | Instala Visual C++ Redist: https://aka.ms/vs/17/release/vc_redist.x64.exe |
| El adaptador USB no crea puerto COM | Usa el **asistente de drivers** de la app |
| `Permission denied` en el puerto COM | Cierra otros programas que usen el puerto (otro escáner) |
| El ELM327 BT no tiene puerto COM | *Más opciones Bluetooth → COM → Agregar → Saliente* |

---

## Estructura del proyecto

```
Dev-Python2-main/
├── iniciar.bat                 ← doble clic para ejecutar (usa py)
├── instalar.bat                ← solo instalar dependencias
├── run.py                      ← punto de entrada PC
├── requirements-pc.txt         ← dependencias para PC
├── INSTALAR_PC.md              ← esta guía
├── .vscode/                    ← config lista para VS Code (F5, tasks)
├── drivers/                    ← coloca aquí los instaladores de drivers
│   └── README.md
├── diagnostico_auto/
│   ├── main.py                 ← lanzador alternativo
│   ├── gui/                    ← interfaz (pantallas, componentes)
│   ├── core/hardware/          ← conexiones (Serial, WiFi, BT) + drivers
│   ├── core/protocols/         ← OBD-II y UDS
│   ├── diagnostics/            ← lector DTCs, escáner, manual
│   ├── brands/renault/         ← módulos y PIDs del Duster
│   └── database/               ← códigos DTC y manuales del Duster
└── buildozer.spec              ← solo para APK Android (ignorar en PC)
```
