import socket
import time
import numpy as np
from datetime import datetime

HOST = '0.0.0.0'  # Aceita conexões de qualquer IP
PORT = 5000
INTERVAL = 60  # segundos entre leituras (ajustável)

# Parâmetros da simulação baseada no artigo (Figura 2)
def gerar_leitura(t):
    dias = t / 86400  # t em segundos
    # CH4: começa ~150 mg/m³, decai exponencialmente
    ch4 = 150 * np.exp(-0.1 * dias) + 5 + np.random.normal(0, 3)
    # N2O: pico em torno de 10-20 dias
    n2o = 6 * np.sin(dias / 10) + 2 + np.random.normal(0, 0.2)
    return max(0, ch4), max(0, n2o)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Sensor virtual aguardando conexões em {HOST}:{PORT}")
        conn, addr = s.accept()
        with conn:
            print(f"Conectado por {addr}")
            inicio = time.time()
            while True:
                t = time.time() - inicio
                ch4, n2o = gerar_leitura(t)
                linha = f"{ch4:.2f},{n2o:.2f}\n"
                conn.sendall(linha.encode())
                print(f"Enviado: {linha.strip()}")
                time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
