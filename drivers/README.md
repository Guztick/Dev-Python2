# Carpeta de drivers

Coloca aquí los instaladores de drivers de tu adaptador ELM327 USB.
La aplicación los detectará y podrá ejecutarlos automáticamente desde la
sección **Drivers** de la pantalla de conexión.

## ¿Qué driver necesito?

Depende del **chip** de tu adaptador. La app lo detecta automáticamente,
pero aquí tienes la referencia:

| Chip | Archivo a colocar aquí | Descarga oficial |
|------|------------------------|------------------|
| **CH340 / CH341** (el más común en clones) | `CH341SER.EXE` | https://www.wch-ic.com/downloads/CH341SER_EXE.html |
| **CP210x** (Silicon Labs) | `CP210xVCPInstaller_x64.exe` | https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers |
| **FTDI FT232** (premium / OBDLink) | `CDM212364_Setup.exe` | https://ftdichip.com/drivers/vcp-drivers/ |
| **PL2303** (Prolific) | `PL2303_Prolific_Driver.exe` | https://www.prolific.com.tw/US/ShowProduct.aspx?p_id=225&pcid=41 |

## Cómo funciona

1. Conecta tu adaptador ELM327 al PC por USB.
2. Abre la app → pantalla de conexión → botón **DRIVERS**.
3. La app detecta el chip y te dice si el driver está instalado.
4. Si falta el driver:
   - Si colocaste el instalador en esta carpeta → la app lo ejecuta.
   - Si no → la app abre la página de descarga oficial.

## Nota sobre Bluetooth

Los adaptadores **Bluetooth NO necesitan driver**: usan el perfil estándar
del sistema (SPP). Solo tienes que emparejarlos desde la configuración de
Bluetooth de Windows, y el sistema crea un puerto COM saliente
automáticamente.

## Importante

Por motivos de licencia, los instaladores de drivers **no se incluyen** en
el repositorio. Descárgalos de los enlaces oficiales de arriba (son
gratuitos) y colócalos en esta carpeta con el nombre exacto indicado.
