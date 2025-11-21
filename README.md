# Manual de Usuario - Aplicación de Control Remoto Escolar

Esta aplicación permite conectar 3 dispositivos (1 Servidor y 2 Clientes) para realizar tareas de monitoreo y control remoto.

## Requisitos Previos
1. **Python 3.x** instalado en todos los equipos.
2. Instalar las dependencias en cada equipo:
   ```bash
   pip install -r requirements.txt
   ```
   (Las librerías necesarias son: `mss`, `pynput`, `Pillow`)

## Configuración de los Equipos

### Equipo 1: Servidor (Linux recomendado)
1. Abre una terminal en la carpeta del proyecto.
2. Ejecuta el servidor:
   ```bash
   python servidor.py
   ```
3. Anota la **IP** y el **Puerto** que aparecen en la ventana del servidor.

### Equipos 2 y 3: Clientes (Windows o Linux)
1. Abre una terminal en la carpeta del proyecto.
2. Ejecuta el cliente con un nombre único:
   ```bash
   # En el Equipo 2
   python cliente.py Cliente1

   # En el Equipo 3
   python cliente.py Cliente2
   ```
3. En la interfaz, ingresa la **IP del Servidor** y haz clic en **Conectar**.

## Funcionalidades (Guía de Uso)

### 3.1 Observar PC Remoto
- En el **Servidor**, selecciona un cliente de la lista.
- Haz clic en **"Ver Pantalla Cliente"**.
- Se abrirá una ventana mostrando lo que hace ese cliente en tiempo real.

### 3.2 Transferencia de Archivos
- En cualquier **Cliente**, haz clic en **"Enviar Archivo"**.
- Selecciona el archivo.
- El archivo se enviará al servidor y este lo reenviará a todos los demás clientes conectados.

### 3.3 Chat
- Escribe en la barra inferior de cualquier cliente y presiona **Enviar**.
- Todos los conectados verán el mensaje.

### 3.4 Exhibir un Cliente
- En el **Servidor**, selecciona el cliente que quieres mostrar (Origen).
- Haz clic en **"Exhibir Cliente a Cliente"**.
- Escribe el nombre del cliente que debe ver la pantalla (Destino).

### 3.5 Mostrar Servidor
- En el **Servidor**, haz clic en **"Mostrar Servidor a Cliente"**.
- (Nota: Esta función requiere que el servidor tenga entorno gráfico y `mss` configurado).

### 3.6 y 3.7 Bloquear/Desbloquear Input
- En el **Servidor**, selecciona un cliente.
- Haz clic en **"Bloquear Input"** para deshabilitar su teclado y mouse.
- Haz clic en **"Desbloquear Input"** para restaurar el control.

### 3.8 Apagar PC Remotamente
- En el **Servidor**, selecciona un cliente.
- Haz clic en **"Apagar Remoto"**.
- **¡Cuidado!** Esto apagará el equipo del cliente inmediatamente.

### 3.9 Denegar Acceso Web
- En el **Servidor**, selecciona un cliente.
- Haz clic en **"Bloquear Web"**.
- Ingresa la URL (ej: `www.facebook.com`).
- **Nota**: El cliente debe ejecutarse con permisos de Administrador/Root para que esto funcione.

### 3.10 Control de Ping
- En el **Servidor**, usa los botones **"Bloquear Ping"** o **"Permitir Ping"**.
- **Nota**: Requiere permisos de Administrador/Root en el cliente para modificar el firewall.

## Solución de Problemas
- **Permisos**: Si el bloqueo de web o ping no funciona, asegúrate de ejecutar `cliente.py` como administrador (`sudo python cliente.py` en Linux o "Ejecutar como administrador" en Windows).
- **Firewall**: Asegúrate de que el puerto 5000 esté abierto en el firewall del servidor.
