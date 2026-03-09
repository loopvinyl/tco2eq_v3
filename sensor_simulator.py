import pandas as pd
import random

dias = list(range(0,55,5))

data = []

for d in dias:

    ch4 = max(0.1, 2.5 - d*0.05 + random.uniform(-0.1,0.1))
    n2o = max(0.1, 0.2 + d*0.02 - d*0.0004 + random.uniform(-0.05,0.05))

    data.append([d,ch4,n2o])

df = pd.DataFrame(data,columns=["dia","CH4","N2O"])

df.to_csv("dados_emissoes.csv",index=False)

print("dados gerados")
