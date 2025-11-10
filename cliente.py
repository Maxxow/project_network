import socket
import os  # Necesario para comprobar si el archivo existe y su tamaño

# --- Constantes ---
HOST = '127.0.0.1'  # Cambia esto por la IP del servidor
PORT = 65432
BUFFER_SIZE = 4096  # 4KB

def enviar_archivo(s, ruta_archivo):
    """ Función dedicada a enviar un archivo """
    
    # 1. Comprobar si el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo '{ruta_archivo}' no existe.")
        return
        
    # 2. Obtener nombre y tamaño
    filename = os.path.basename(ruta_archivo)
    filesize = os.path.getsize(ruta_archivo)
    
    # 3. Enviar el "comando" al servidor
    print(f"Enviando comando: enviar_archivo::{filename}::{filesize}")
    s.sendall(f"enviar_archivo::{filename}::{filesize}".encode('utf-8'))
    
    # 4. Esperar la confirmación del servidor ("OK_LISTO")
    respuesta_servidor = s.recv(1024).decode('utf-8')
    
    if respuesta_servidor == "OK_LISTO":
        print("Servidor listo. Empezando a enviar el archivo...")
        
        # 5. Enviar el archivo en trozos (chunks)
        bytes_enviados = 0
        try:
            with open(ruta_archivo, 'rb') as f: # Abrir en modo "Read Binary" (rb)
                while bytes_enviados < filesize:
                    data = f.read(BUFFER_SIZE)
                    if not data:
                        break # Se terminó de leer el archivo
                    
                    s.sendall(data)
                    bytes_enviados += len(data)
                    
            print(f"Archivo enviado. Esperando confirmación final...")
            
            # 6. Esperar confirmación final
            confirmacion_final = s.recv(1024).decode('utf-8')
            print(f"[Servidor] {confirmacion_final}")
            
        except Exception as e:
            print(f"Error durante el envío: {e}")
            
    else:
        print(f"El servidor no pudo preparar la recepción: {respuesta_servidor}")


# --- Flujo Principal del Cliente ---

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Conectando a {HOST}:{PORT}...")
    s.connect((HOST, PORT))
    print("¡Conectado!")
    
    bienvenida = s.recv(1024).decode('utf-8')
    print(f"[Servidor] {bienvenida}")

    try:
        while True:
            mensaje = input("Escribe tu mensaje (o 'enviar_archivo <ruta>'): ")
            
            # --- NUEVA LÓGICA DE COMANDOS ---
            if mensaje.startswith('enviar_archivo '):
                # Obtenemos la ruta del archivo (ej. "mi_archivo.txt")
                ruta_archivo = mensaje.split(" ", 1)[1]
                enviar_archivo(s, ruta_archivo)
            
            # --- LÓGICA DE CHAT (como antes) ---
            elif mensaje.strip().lower() == 'adios':
                s.sendall(mensaje.encode('utf-8'))
                print("Desconectando...")
                break
            else:
                # Es un mensaje de chat normal
                s.sendall(mensaje.encode('utf-8'))
                # Esperamos la respuesta (eco) del servidor
                data = s.recv(1024)
                print(f"[Servidor] {data.decode('utf-8')}")
            
    except KeyboardInterrupt:
        print("\nCerrando conexión.")
    finally:
        s.close()