import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Listbox, MULTIPLE
from PIL import Image, ImageTk  # Importar Pillow para manejar imágenes
import subprocess
import sys
import threading
import os

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta a un recurso incluido en el ejecutable."""
    if hasattr(sys, '_MEIPASS'):
        # Si el programa está empaquetado, usa la carpeta temporal
        base_path = sys._MEIPASS
    else:
        # Si no está empaquetado, usa la ruta normal
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_ffmpeg_path():
    """Obtiene la ruta a ffmpeg.exe."""
    return get_resource_path("ffmpeg.exe")

class YTDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Riprush")  # Nombre del programa actualizado

        # Cambiar el ícono de la ventana
        try:
            self.root.iconbitmap(get_resource_path("logo.ico"))  # Asegúrate de que "logo.ico" esté en el mismo directorio
        except Exception as e:
            print(f"No se pudo cargar el ícono: {e}")

        # Variables
        self.url_var = tk.StringVar()
        self.video_quality_var = tk.StringVar()
        self.audio_tracks_var = tk.StringVar()
        self.download_type_var = tk.StringVar(value="Video")  # Valor por defecto
        self.formats_info = ""  # Almacena la información de formatos
        self.video_formats = []  # Almacena los formatos de video
        self.audio_formats = []  # Almacena los formatos de audio

        # Estilos para modo claro y oscuro
        self.light_mode = {
            "bg": "white",
            "fg": "black",
            "button_bg": "lightgray",
            "button_fg": "black"
        }
        self.dark_mode = {
            "bg": "black",
            "fg": "white",
            "button_bg": "gray",
            "button_fg": "white"
        }
        self.current_mode = self.light_mode

        # Botón para cambiar entre modo claro y oscuro
        self.mode_button = ttk.Button(root, text="Modo Oscuro", command=self.toggle_mode)
        self.mode_button.grid(row=7, column=0, padx=10, pady=5)

        # Botón de Créditos
        self.credits_button = ttk.Button(root, text="Créditos", command=self.show_credits)
        self.credits_button.grid(row=7, column=1, padx=10, pady=5)

        # Entrada de URL (más ancha, igual que la lista de pistas de audio)
        ttk.Label(root, text="Pega el enlace aqui:").grid(row=0, column=0, padx=10, pady=5)  # Ajuste de espaciado
        self.url_entry = ttk.Entry(root, textvariable=self.url_var, width=100)  # Ancho igual al de la lista de audio
        self.url_entry.grid(row=0, column=1, padx=10, pady=5)  # Ajuste de espaciado

        # Botón de Analizar
        self.analyze_button = ttk.Button(root, text="Analizar", command=self.start_analyze_thread)
        self.analyze_button.grid(row=0, column=2, padx=10, pady=5)  # Ajuste de espaciado

        # Etiqueta de estado
        self.status_label = ttk.Label(root, text="", foreground="blue")
        self.status_label.grid(row=1, column=0, columnspan=3, pady=5)  # Ajuste de espaciado

        # Combobox de Tipo de Descarga
        ttk.Label(root, text="Tipo de Descarga:").grid(row=2, column=0, padx=10, pady=5)  # Ajuste de espaciado
        self.download_type_combobox = ttk.Combobox(root, textvariable=self.download_type_var, values=["Video", "Solo Audio"], state="readonly")
        self.download_type_combobox.grid(row=2, column=1, padx=10, pady=5)  # Ajuste de espaciado
        self.download_type_combobox.bind("<<ComboboxSelected>>", self.update_download_type)  # Actualizar al cambiar

        # Combobox de Calidad de Video
        ttk.Label(root, text="Seleccionar Calidad de Video:").grid(row=3, column=0, padx=10, pady=5)  # Ajuste de espaciado
        self.video_quality_combobox = ttk.Combobox(root, textvariable=self.video_quality_var, width=100)
        self.video_quality_combobox.grid(row=3, column=1, padx=10, pady=5)  # Ajuste de espaciado

        # Listbox de Pistas de Audio (más alto)
        ttk.Label(root, text="Seleccionar Pistas de Audio:").grid(row=4, column=0, padx=10, pady=5)  # Ajuste de espaciado
        self.audio_tracks_listbox = Listbox(root, selectmode=MULTIPLE, width=100, height=8)  # Aumentamos la altura a 8
        self.audio_tracks_listbox.grid(row=4, column=1, padx=10, pady=5)  # Ajuste de espaciado

        # Cargar y mostrar la imagen justo debajo del texto "Seleccionar Pistas de Audio"
        try:
            self.image = Image.open(get_resource_path("riprush.png"))  # Cargar la imagen
            self.image = self.image.resize((150, 150), Image.Resampling.LANCZOS)  # Redimensionar a 150x150
            self.photo = ImageTk.PhotoImage(self.image)  # Convertir a formato compatible con Tkinter
            self.image_label = ttk.Label(root, image=self.photo)
            self.image_label.grid(row=4, column=2, padx=10, pady=5, sticky="w")  # Posicionar en la misma fila, columna 2
        except Exception as e:
            print(f"No se pudo cargar la imagen: {e}")

        # Barra de progreso de descarga (más estrecha)
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")  # Ancho ajustado
        self.progress_bar.grid(row=5, column=0, columnspan=3, pady=5, padx=10)  # Ajuste de espaciado

        # Etiqueta de porcentaje de descarga (superpuesta en la barra de progreso)
        self.progress_label = ttk.Label(self.progress_bar, text="", background="lightgray", font=("Arial", 10))
        self.progress_label.place(relx=0.5, rely=0.5, anchor="center")  # Centrar la etiqueta en la barra

        # Botón de Descargar
        self.download_button = ttk.Button(root, text="Descargar", command=self.start_download_thread)
        self.download_button.grid(row=6, column=0, columnspan=3, pady=10)  # Ajuste de espaciado

    def toggle_mode(self):
        if self.current_mode == self.light_mode:
            self.current_mode = self.dark_mode
            self.mode_button.config(text="Modo Claro")
        else:
            self.current_mode = self.light_mode
            self.mode_button.config(text="Modo Oscuro")
        self.apply_mode()

    def apply_mode(self):
        # Configurar el fondo de la ventana principal
        self.root.configure(bg=self.current_mode["bg"])

        # Recorrer todos los widgets y aplicar el modo correspondiente
        for widget in self.root.winfo_children():
            if isinstance(widget, (ttk.Label, ttk.Button, ttk.Entry, ttk.Combobox)):
                # Aplicar estilos a los widgets ttk
                widget.configure(style="TLabel" if isinstance(widget, ttk.Label) else
                                "TButton" if isinstance(widget, ttk.Button) else
                                "TEntry" if isinstance(widget, ttk.Entry) else
                                "TCombobox")
            elif isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Listbox)):
                # Configurar colores directamente para los widgets de tkinter
                widget.configure(bg=self.current_mode["bg"], fg=self.current_mode["fg"])
            elif isinstance(widget, ttk.Progressbar):
                # Configurar la barra de progreso
                widget.configure(style="TProgressbar")
            else:
                # Configurar el fondo para otros widgets
                widget.configure(bg=self.current_mode["bg"])

    def show_credits(self):
        credits_window = tk.Toplevel(self.root)
        credits_window.title("Créditos")
        credits_window.geometry("300x250")  # Aumentamos el alto de la ventana a 250

        # Configurar el ícono de la ventana de créditos
        try:
            credits_window.iconbitmap(get_resource_path("logo.ico"))  # Mismo ícono que la ventana principal
        except Exception as e:
            print(f"No se pudo cargar el ícono: {e}")

        # Texto de créditos
        ttk.Label(credits_window, text="Creado por Vesgamer").pack(pady=10)

        # Cargar y mostrar la imagen
        try:
            image = Image.open(get_resource_path("riprush.png"))
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            image_label = ttk.Label(credits_window, image=photo)
            image_label.image = photo  # Mantener una referencia para evitar que la imagen sea eliminada por el recolector de basura
            image_label.pack(pady=10)
        except Exception as e:
            print(f"No se pudo cargar la imagen: {e}")

        # Botón "Listo"
        ttk.Button(credits_window, text="Listo", command=credits_window.destroy).pack(pady=10)

    def start_analyze_thread(self):
        # Deshabilitar el botón de Analizar
        self.analyze_button.config(state="disabled")
        # Iniciar el análisis en un hilo separado para no bloquear la interfaz
        analyze_thread = threading.Thread(target=self.analyze_url)
        analyze_thread.start()

    def analyze_url(self):
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Por favor, ingresa un enlace valido")
            self.analyze_button.config(state="normal")  # Rehabilitar el botón
            return

        # Verificar si yt-dlp.exe existe
        yt_dlp_path = get_resource_path("yt-dlp.exe")
        if not os.path.exists(yt_dlp_path):
            messagebox.showerror("Error", "yt-dlp.exe no encontrado.")
            self.analyze_button.config(state="normal")  # Rehabilitar el botón
            return

        # Mostrar mensaje de "Analizando..."
        self.status_label.config(text="Analizando...", foreground="blue")
        self.root.update()  # Actualizar la interfaz

        # Ejecutar yt-dlp -F para obtener la información de formatos
        command = [yt_dlp_path, "-F", url]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            self.formats_info = result.stdout

            # Extraer formatos de video y audio
            self.extract_formats()

            # Mostrar mensaje de "Análisis completo"
            self.status_label.config(text="Análisis completo", foreground="green")
        except subprocess.CalledProcessError as e:
            self.status_label.config(text="Error al analizar", foreground="red")
            messagebox.showerror("Error", f"Error al analizar el enlace: {e.stderr}")
        except Exception as e:
            self.status_label.config(text="Error inesperado", foreground="red")
            messagebox.showerror("Error", f"Error inesperado: {e}")
        finally:
            self.analyze_button.config(state="normal")  # Rehabilitar el botón

    def extract_formats(self):
        self.video_formats = []
        self.audio_formats = []

        for line in self.formats_info.splitlines():
            if "video only" in line:
                parts = line.split()
                format_id = parts[0]
                extension = parts[1]
                resolution = parts[2] if len(parts) > 2 else "Desconocido"
                fps = parts[3] if len(parts) > 3 else "Desconocido"
                filesize = parts[4] if len(parts) > 4 else "Desconocido"
                more_info = " ".join(parts[5:]) if len(parts) > 5 else "Desconocido"
                self.video_formats.append({
                    "id": format_id,
                    "extension": extension,
                    "resolution": resolution,
                    "fps": fps,
                    "filesize": filesize,
                    "more_info": more_info,
                    "full_line": line
                })
            elif "audio only" in line:
                parts = line.split()
                format_id = parts[0]
                extension = parts[1]
                filesize = parts[2] if len(parts) > 2 else "Desconocido"
                more_info = " ".join(parts[3:]) if len(parts) > 3 else "Desconocido"
                self.audio_formats.append({
                    "id": format_id,
                    "extension": extension,
                    "filesize": filesize,
                    "more_info": more_info,
                    "full_line": line
                })

        # Actualizar la lista de calidad de video
        self.update_video_qualities()

        # Actualizar la lista de pistas de audio
        self.update_audio_tracks()

    def update_video_qualities(self):
        # Actualizar el Combobox con las calidades de video
        self.video_quality_combobox['values'] = [
            f"{fmt['resolution']} | {fmt['fps']} | {fmt['extension']} | {fmt['filesize']} | {fmt['more_info']}"
            for fmt in self.video_formats
        ]
        if self.video_formats:
            self.video_quality_combobox.current(0)

    def update_audio_tracks(self):
        # Limpiar y actualizar el Listbox de pistas de audio
        self.audio_tracks_listbox.delete(0, tk.END)
        for fmt in self.audio_formats:
            self.audio_tracks_listbox.insert(tk.END, f"{fmt['extension']} | {fmt['filesize']} | {fmt['more_info']}")

    def update_download_type(self, event=None):
        # Habilitar o deshabilitar la selección de calidad de video según el tipo de descarga
        if self.download_type_var.get() == "Solo Audio":
            self.video_quality_combobox.config(state="disabled")
        else:
            self.video_quality_combobox.config(state="readonly")

    def start_download_thread(self):
        # Deshabilitar el botón de descarga
        self.download_button.config(state="disabled")
        # Iniciar la descarga en un hilo separado para no bloquear la interfaz
        download_thread = threading.Thread(target=self.download)
        download_thread.start()

    def download(self):
        url = self.url_var.get()
        download_type = self.download_type_var.get()
        selected_audio_indices = self.audio_tracks_listbox.curselection()

        if not url:
            messagebox.showerror("Error", "Por favor, ingresa un enlace valido")
            self.download_button.config(state="normal")  # Rehabilitar el botón
            return

        # Verificar si yt-dlp.exe existe
        yt_dlp_path = get_resource_path("yt-dlp.exe")
        if not os.path.exists(yt_dlp_path):
            messagebox.showerror("Error", "yt-dlp.exe no encontrado.")
            self.download_button.config(state="normal")  # Rehabilitar el botón
            return

        # Verificar si ffmpeg.exe existe
        ffmpeg_path = get_ffmpeg_path()
        if not os.path.exists(ffmpeg_path):
            messagebox.showerror("Error", "ffmpeg.exe no encontrado.")
            self.download_button.config(state="normal")  # Rehabilitar el botón
            return

        # Preparar el comando según el tipo de descarga
        if download_type == "Video":
            video_quality = self.video_quality_var.get()
            if not video_quality:
                messagebox.showerror("Error", "Por favor, selecciona una calidad de video")
                self.download_button.config(state="normal")  # Rehabilitar el botón
                return
            video_format_id = self.video_formats[self.video_quality_combobox.current()]["id"]

            # Preparar los formatos de audio seleccionados (si los hay)
            audio_formats = "+".join([self.audio_formats[idx]["id"] for idx in selected_audio_indices]) if selected_audio_indices else ""
            format_selection = f"{video_format_id}+{audio_formats}" if audio_formats else video_format_id
        else:
            # Formato de descarga: solo audio
            if not selected_audio_indices:
                messagebox.showerror("Error", "Por favor, selecciona al menos una pista de audio")
                self.download_button.config(state="normal")  # Rehabilitar el botón
                return
            format_selection = "+".join([self.audio_formats[idx]["id"] for idx in selected_audio_indices])

        # Mostrar mensaje de "Descargando..."
        self.status_label.config(text="Descargando...", foreground="blue")
        self.progress_bar["value"] = 0  # Reiniciar la barra de progreso
        self.progress_label.config(text="")  # Reiniciar el porcentaje
        self.root.update()  # Actualizar la interfaz

        # Preparar el comando de yt-dlp con la opción de progreso
        command = [
            yt_dlp_path,
            "-f", format_selection,
            "--audio-multistream",
            "--all-subs",
            "--embed-subs",
            "-o", "%(title)s.%(ext)s",
            "--newline",  # Para obtener el progreso en tiempo real
            "--ffmpeg-location", os.path.dirname(ffmpeg_path),  # Especifica la carpeta de FFmpeg
            url
        ]

        try:
            # Ejecutar el comando y capturar la salida en tiempo real
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            # Leer la salida en tiempo real para actualizar la barra de progreso
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    # Extraer el porcentaje de la línea
                    percentage = float(line.split("%")[0].split()[-1])
                    self.progress_bar["value"] = percentage
                    self.progress_label.config(text=f"{percentage:.1f}%")  # Actualizar el porcentaje
                    self.root.update()  # Actualizar la interfaz

            process.wait()  # Esperar a que termine el proceso

            if process.returncode == 0:
                self.status_label.config(text="Descarga completada", foreground="green")
                messagebox.showinfo("Éxito", "Descarga completada correctamente")
            else:
                self.status_label.config(text="Error al descargar", foreground="red")
                messagebox.showerror("Error", f"Error al descargar: {process.stderr.read()}")
        except Exception as e:
            self.status_label.config(text="Error al descargar", foreground="red")
            messagebox.showerror("Error", f"Error al descargar: {e}")
        finally:
            # Reiniciar la barra de progreso y ocultar el porcentaje
            self.progress_bar["value"] = 0
            self.progress_label.config(text="")
            self.download_button.config(state="normal")  # Rehabilitar el botón
            self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDownloaderApp(root)
    root.mainloop()