import socket
import time
import random
import numpy as np

# Configurações de Rede
HOST = 'localhost'
PORT = 5000

def gerar_dados_artigo(segundo):
    """Simula a curva de Yang et al. (2017) baseada no tempo"""
    dia = segundo / 10  # Acelera o tempo para teste (10s = 1 dia)
    
    # CH4 decai com o tempo
    ch4 = 150 * np.exp(-0.1 * dia) + random.uniform(2, 8)
    # N2O tem picos no meio do processo
    n2o = 6 * np.abs(np.sin(dia / 5)) + random.uniform(0.1, 0.5)
    
    return round(ch4, 2), round(n2o, 2)

def iniciar_sensor():
    # Cria o socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"📡 Sensor Virtual Ativo em {HOST}:{PORT}")
        print("Aguardando conexão do Dashboard...")
        
        tempo_inicio = time.time()
        
        while True:
            conn, addr = s.accept()
            with conn:
                # Gera os dados
                tempo_decorrido = time.time() - tempo_inicio
                ch4, n2o = gerar_dados_artigo(tempo_decorrido)
                
                # Formata como string "CH4,N2O"
                mensagem = f"{ch4},{n2o}"
                conn.sendall(mensagem.encode())
                print(f"📤 Dados enviados para {addr}: {mensagem}")

if __name__ == "__main__":
    iniciar_sensor()
