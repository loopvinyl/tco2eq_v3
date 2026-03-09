# -----------------------------
# Interpretação das perdas (emissões atmosféricas)
# -----------------------------

st.subheader("Percentual de perda convertido em emissões atmosféricas")

st.markdown(
"""
Nos sistemas de compostagem e vermicompostagem, a fração de carbono e nitrogênio
perdida na forma gasosa corresponde às emissões liberadas para a atmosfera.

No caso deste experimento:

- **Carbono perdido via CH4-C** representa o carbono emitido como **metano (CH4)**.
- **Nitrogênio perdido via N2O-N** representa o nitrogênio emitido como **óxido nitroso (N2O)**.

Portanto, os percentuais calculados indicam diretamente a fração do carbono e do nitrogênio
inicial do material que foi transformada em gases de efeito estufa e liberada para a atmosfera.
"""
)

C_loss_final = dados["C_loss_percent"].iloc[-1]
N_loss_final = dados["N_loss_percent"].iloc[-1]

col1, col2 = st.columns(2)

col1.metric(
    "Carbono emitido como CH4 (%)",
    f"{C_loss_final:.3f}"
)

col2.metric(
    "Nitrogênio emitido como N2O (%)",
    f"{N_loss_final:.3f}"
)
