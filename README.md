# Vermi-IoT Sentinel

Sistema de monitoramento de emissões de CH₄ e N₂O em vermicompostagem, baseado no artigo de Yang et al. (2017).

## Funcionalidades
- Leitura de sensores (simulada ou via TCP)
- Cálculo de fluxos horários e diários
- Balanço de massa e estimativa de emissões totais (kg CO₂-eq)
- Visualização em tempo real e histórica

## Como executar

### Opção 1: Apenas o app (simulação interna)
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute: `streamlit run app.py`
4. No app, mantenha a opção "Simulado" nas configurações.

### Opção 2: App + Sensor virtual TCP (para testar comunicação)
1. Em um terminal, execute o sensor virtual: `python sensor_virtual.py`
2. Em outro terminal, execute o app: `streamlit run app.py`
3. No app, vá em Configurações e selecione "TCP/IP", host `localhost` e porta `5000`.
4. Na aba Monitoramento, clique em "Atualizar Leitura" para receber dados.

## Deploy no Streamlit Cloud
O app pode ser implantado diretamente no Streamlit Cloud. A opção TCP/IP não funcionará (a menos que você tenha um servidor externo), mas a simulação interna funcionará perfeitamente.

## Estrutura dos arquivos
- `app.py`: Código principal do Streamlit
- `sensor_virtual.py`: Script opcional para simular um sensor TCP
- `requirements.txt`: Dependências Python
- `README.md`: Este arquivo

## Referência
Yang, F., Li, G., Shi, H., & Wang, Y. (2017). Effects of phosphogypsum and superphosphate on compost maturity and gaseous emissions during kitchen waste composting. *Waste Management*, 64, 119–126.
