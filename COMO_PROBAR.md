# Cómo probar DiagnósticoPro en tu dispositivo Android

Tienes **dos formas** de probar la app en tu teléfono. La primera es
inmediata (para ver la interfaz ya), la segunda te da la app instalada
de verdad (APK) con acceso a Bluetooth y USB.

---

## 🚀 Opción 1: Probar YA con Pydroid 3 (rápido, sin compilar)

Ideal para ver y navegar la interfaz en **modo demo** en minutos.
No requiere adaptador OBD conectado.

### Pasos

1. **Instala Pydroid 3** desde Google Play (gratis):
   https://play.google.com/store/apps/details?id=ru.iiec.pydroid3

2. **Abre Pydroid 3** → menú lateral → **Pip** → instala estos paquetes
   uno por uno (escribe el nombre y pulsa "Install"):
   ```
   kivy==2.3.1
   kivymd==1.2.0
   pillow
   ```
   > La instalación de Kivy puede tardar unos minutos la primera vez.

3. **Descarga el código** del proyecto a tu teléfono:
   - Abre en el navegador: `https://github.com/Guztick/Dev-Python2`
   - Cambia a la rama `claude/android-testing-setup-ndElz`
   - Botón verde **Code** → **Download ZIP**
   - Descomprime el ZIP (con cualquier app de archivos)

4. **Abre el proyecto en Pydroid 3**:
   - Menú → **Open** → navega a la carpeta descomprimida →
     `diagnostico_auto/main.py`

5. **Ejecuta** (botón ▶ amarillo abajo a la derecha).

6. En la app, selecciona **Demo** y pulsa **CONECTAR**. Ya puedes
   navegar todo: dashboard, escaneo, DTCs, datos en vivo y el escáner.

> ⚠️ **Limitación de Pydroid:** el Bluetooth/USB real no funciona aquí
> (Pydroid no tiene acceso nativo de Android). El **modo Demo sí funciona
> completo** para ver y probar toda la interfaz. Para hardware real usa
> la Opción 2 (APK).

---

## 📱 Opción 2: Instalar el APK real (Bluetooth y USB funcionando)

Esta es la app instalada de verdad, con acceso a tu escáner Bluetooth
y a periféricos USB. El APK se **compila automáticamente en la nube**.

### Pasos

1. Ve a la pestaña de compilaciones del proyecto:
   **https://github.com/Guztick/Dev-Python2/actions**

2. Abre la ejecución más reciente de **"Compilar APK Android"**
   (espera a que termine — el ✓ verde; tarda 20-40 min la primera vez).

3. Baja hasta la sección **Artifacts** y descarga
   **`DiagnosticoPro-APK`** (es un ZIP con el `.apk` dentro).

4. En tu teléfono, descomprime y **abre el archivo `.apk`** para
   instalarlo. Android te pedirá permitir "instalar apps desconocidas"
   — acéptalo solo para esta vez.

5. Abre **DiagnósticoPro**. La primera vez te pedirá permisos de
   **Bluetooth** y **ubicación** (Android los exige para buscar
   dispositivos Bluetooth). Acéptalos.

### Para usar con tu Renault Duster

1. Empareja tu escáner ELM327 Bluetooth en los **ajustes de Bluetooth**
   de Android (PIN habitual: `1234` o `0000`).
2. Conecta el ELM327 al puerto OBD-II del Duster (debajo del volante)
   y pon el switch en contacto (sin arrancar).
3. En la app: selecciona **Bluetooth** → **BUSCAR DISPOSITIVOS** →
   elige tu adaptador (los OBD aparecen con ⭐) → **CONECTAR**.
4. Revisa primero la pestaña **Escáner** para ver el alcance de tu
   adaptador, luego **Escaneo** para detectar los módulos del Duster.

---

## 🖥️ Opción 3: Probar en computadora (desarrollo)

Si quieres probar en una PC/laptop:

```bash
cd diagnostico_auto
pip install kivy==2.3.1 kivymd==1.2.0 pillow pyserial
python main.py
```

Se abrirá una ventana con proporción de teléfono. Usa **Demo** para
explorar, o conecta un ELM327 WiFi/USB para diagnóstico real.

---

## ¿Cuál elijo?

| Quiero... | Usa |
|-----------|-----|
| Ver la interfaz **ya**, sin esperar | **Opción 1 (Pydroid)** |
| Usar mi **escáner Bluetooth** real en el Duster | **Opción 2 (APK)** |
| Desarrollar y depurar en PC | **Opción 3** |

La **Opción 2 (APK)** es la experiencia final que tendrá la app. La
**Opción 1** es la forma más rápida de ver el avance en tu teléfono
ahora mismo.
