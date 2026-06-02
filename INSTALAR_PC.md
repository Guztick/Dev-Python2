# Instalar y ejecutar DiagnósticoPro en PC (Windows + VS Code)

## Requisitos previos

- **Python 3.10 o superior** — https://www.python.org/downloads/  
  ⚠️ Al instalar Python, marca **"Add Python to PATH"**
- **Git** — https://git-scm.com/downloads
- **VS Code** — https://code.visualstudio.com/ (con extensión Python)

---

## Pasos de instalación

### 1. Clonar / actualizar el proyecto

Si ya tienes la carpeta descargada, solo actualiza desde la rama correcta:

```bash
cd "C:\Users\jhona\Downloads\GITHUB\OBD2- Pyton\Dev-Python2-main"
git fetch origin
git checkout claude/android-testing-setup-ndElz
git pull
```

Si es la primera vez (clone desde cero):

```bash
git clone https://github.com/Guztick/Dev-Python2.git
cd Dev-Python2
git checkout claude/android-testing-setup-ndElz
```

---

### 2. Crear entorno virtual (recomendado)

Abre una terminal en la carpeta del proyecto:

```bash
python -m venv venv
venv\Scripts\activate
```

Verás `(venv)` al inicio de la línea de comandos — eso indica que el entorno está activo.

---

### 3. Instalar dependencias

```bash
pip install -r requirements-pc.txt
```

Esto instala: Kivy 2.3.1, KivyMD 1.2.0, Pillow y pyserial. Tarda unos minutos.

---

### 4. Ejecutar la aplicación

Desde la raíz del proyecto:

```bash
python run.py
```

O desde VS Code: abre `run.py` → botón ▶ (Run Python File).

La app abre una ventana de 480×860 px. Selecciona **Demo** y presiona **CONECTAR** para navegar toda la interfaz sin adaptador físico.

---

## Conectar un adaptador ELM327 real

### ELM327 por USB

1. Conecta el adaptador al puerto OBD-II del vehículo y al PC por USB.
2. Windows instala el driver automáticamente (CH340 o CP2102).  
   Si no lo reconoce: instala el driver desde https://www.wch-ic.com/downloads/CH341SER_EXE.html
3. Abre el **Administrador de dispositivos** → Puertos COM y LPT → anota el número de puerto (ej: `COM3`).
4. En la app: selecciona **USB** → escribe `COM3` → **CONECTAR**.

### ELM327 por Bluetooth

1. Enciende el adaptador (conéctalo al puerto OBD-II del vehículo, ignición en contacto).
2. En Windows: **Configuración → Bluetooth → Agregar dispositivo**.  
   PIN habitual: `1234` o `0000`.
3. Tras emparejar, Windows asigna automáticamente un **puerto COM de salida**  
   (ej: `COM5` o `COM6`).  
   Para ver cuál: **Administrador de dispositivos** → **Puertos COM y LPT** → busca "Bluetooth Serial Port".
4. En la app: selecciona **Bluetooth** → escribe `COM5` (tu número) → **CONECTAR**.
5. O usa el botón **BUSCAR DISPOSITIVOS** — la app lista todos los puertos COM disponibles automáticamente.

### ELM327 por WiFi

1. Conecta al adaptador (crea una red WiFi propia, SSID tipo `WiFi_OBDII`).
2. Conéctate a esa red desde Windows.
3. En la app: selecciona **WiFi** → IP por defecto `192.168.0.10:35000` → **CONECTAR**.

---

## Abrir en VS Code

1. **File → Open Folder** → selecciona la carpeta del proyecto.
2. VS Code detecta el entorno virtual automáticamente.  
   Si no: `Ctrl+Shift+P` → "Python: Select Interpreter" → elige el de la carpeta `venv`.
3. Para ejecutar: abre `run.py` y presiona `F5` o el botón ▶.

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `No module named 'kivy'` | Activa el entorno: `venv\Scripts\activate` y vuelve a instalar |
| La ventana no abre / error SDL | Instala Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe |
| Error al conectar al puerto COM | Verifica que el número sea correcto en el Administrador de dispositivos |
| `Permission denied` en el puerto | Cierra otros programas que puedan estar usando el puerto (otro escáner, etc.) |
| Kivy muy lento en PC | Actualiza drivers de GPU; Kivy usa aceleración por hardware |

---

## Estructura del proyecto

```
Dev-Python2-main/
├── run.py                      ← punto de entrada PC
├── requirements-pc.txt         ← dependencias para PC
├── INSTALAR_PC.md              ← esta guía
├── diagnostico_auto/
│   ├── main.py                 ← lanzador alternativo
│   ├── gui/
│   │   ├── app.py              ← app principal
│   │   ├── screens/            ← pantallas
│   │   └── components/         ← widgets reutilizables
│   ├── core/hardware/          ← conexiones (Serial, WiFi, BT)
│   ├── core/protocols/         ← OBD-II y UDS
│   ├── diagnostics/            ← lector DTCs, escáner, manual
│   ├── brands/renault/         ← módulos y PIDs del Duster
│   └── database/
│       ├── dtc_es.json         ← 1148 códigos de falla en español
│       └── manuales/           ← procedimientos y sistemas Duster
└── buildozer.spec              ← solo para compilar APK (ignorar en PC)
```
