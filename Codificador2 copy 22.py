import numpy as np
import pyaudio
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import re

# Parámetros globales
BITRATE = 100  # bits por segundo
FREQ_0 = 1000  # Frecuencia para bit 0
FREQ_1 = 2500  # Frecuencia para bit 1
DURATION = 1 / BITRATE  # Duración de cada bit en segundos
SAMPLERATE = 44100 # Tasa de muestreo de audio
CHUNK = int(SAMPLERATE * DURATION)


#Genera los puntos de las funciones que se van a asignar a cada bit 
def generate_tone(frequency, duration, sample_rate=SAMPLERATE):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return 0.5 * np.sin(2 * np.pi * frequency * t)
#convierte el texto ingresado en sus valores binarios para luego a cada uno asignar su respectivo segmento de onda
def text_to_signal(text, bit_duration=DURATION, sample_rate=SAMPLERATE):
    binary_string = ''.join(format(ord(char), '08b') for char in text)
    print(binary_string)
    signal = np.array([])

    for bit in binary_string:
        frequency = FREQ_1 if bit == '1' else FREQ_0
        signal = np.concatenate([signal, generate_tone(frequency, bit_duration, sample_rate)])
        print(signal)
    return signal
# va a reproducir los sonidos correspondientes a cada onda por bit codificado para el envio 
def play_signal(signal, sample_rate=SAMPLERATE):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)
    stream.write(signal.astype(np.float32).tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()
#Al recibir el mensaje se decodifica usando la transformada rapida de fourier 
def signal_to_text(signal, bit_duration=DURATION, sample_rate=SAMPLERATE):
    print(signal)
    bits = ''
    samples_per_bit = int(sample_rate * bit_duration)
    
    for i in range(0, len(signal), samples_per_bit):
        segment = signal[i:i + samples_per_bit]
        fft_result = np.fft.fft(segment)
        freqs = np.fft.fftfreq(len(segment), 1 / sample_rate)
        positive_freqs = freqs[:len(freqs)//2]
        positive_fft_result = np.abs(fft_result[:len(fft_result)//2])
        dominant_freq = positive_freqs[np.argmax(positive_fft_result)]
        
        if dominant_freq > (FREQ_0 + FREQ_1) / 2:
            bits += '1'
        else:
            bits += '0'
        #print(bits)
    
    chars = [chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits), 8)]

    print(chars)
    return ''.join(chars)
#va a "abrir" el microfono para grabar la onda enviada para su decodificacion 
def record_signal(duration, sample_rate=SAMPLERATE):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, input=True, frames_per_buffer=1024)

    frames = []
    for _ in range(int(sample_rate / 1024 * duration)):
        data = stream.read(1024)
        frames.append(np.frombuffer(data, dtype=np.float32))

    stream.stop_stream()
    stream.close()
    p.terminate()

    return np.concatenate(frames)

# GUI 
def send_message():
    message = entry_message.get()
    if message:
        signal = text_to_signal(message)
        threading.Thread(target=play_signal, args=(signal,)).start()
        log_message("Enviado: " + message)
    else:
        messagebox.showwarning("Alerta", "Ingrese un mensaje para poder enviar.")

def receive_message():
    try:
        duration = int(entry_duration.get())
    except ValueError:
        messagebox.showerror("Error", "Ingrese una duracion correcta.")
        return

    threading.Thread(target=record_and_display_message, args=(duration,)).start()

def record_and_display_message(duration):
    signal = record_signal(duration)
    message = signal_to_text(signal)
    log_message("Recivido: " + message)

def log_message(message):
    text_log.config(state=tk.NORMAL)
    text_log.insert(tk.END, message + "\n")
    text_log.config(state=tk.DISABLED)


root = tk.Tk()
root.title("Codificacion de mensaje mediante audio")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label_message = tk.Label(frame, text="Mensaje a enviar:")
label_message.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)

entry_message = tk.Entry(frame, width=50)
entry_message.grid(row=0, column=1, padx=5, pady=5)

button_send = tk.Button(frame, text="Enviar", command=send_message)
button_send.grid(row=0, column=2, padx=5, pady=5)

label_duration = tk.Label(frame, text="Duracion de repecion del mensaje (segundos):")
label_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)

entry_duration = tk.Entry(frame, width=10)
entry_duration.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

button_receive = tk.Button(frame, text="Recibir", command=receive_message)
button_receive.grid(row=1, column=2, padx=5, pady=5)

text_log = scrolledtext.ScrolledText(frame, width=60, height=20, state=tk.DISABLED)
text_log.grid(row=2, column=0, columnspan=3, padx=5, pady=10)

root.mainloop()
