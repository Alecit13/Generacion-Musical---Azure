import csv
import matplotlib.pyplot as plt
from datetime import datetime

timestamps, zonas, lambdas = [], [], []

with open('sesion_file.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        timestamps.append(float(row['timestamp']))
        zonas.append(row['zona'])
        lambdas.append(float(row['lambda']))

t0 = timestamps[0]
t = [ts - t0 for ts in timestamps]  # segundos desde el inicio de la sesión

zona_a_num = {'grave': 0, 'medio': 1, 'agudo': 2}
zonas_num = [zona_a_num[z] for z in zonas]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), sharex=True, height_ratios=[2, 1])

ax1.plot(t, lambdas, color='#E30613', linewidth=1.5)
ax1.set_ylabel('λ (fluidez)')
ax1.set_ylim(-0.05, 1.05)
ax1.axhline(0.5, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax1.set_title('Sesión real con Azure Kinect: fluidez y registro a lo largo del tiempo')

ax2.step(t, zonas_num, where='post', color='#1F2933', linewidth=1.5)
ax2.set_yticks([0, 1, 2])
ax2.set_yticklabels(['Grave', 'Medio', 'Agudo'])
ax2.set_ylabel('Registro')
ax2.set_xlabel('Tiempo (s)')

plt.tight_layout()
plt.savefig('grafico_sesion_real.png', dpi=200)
plt.show()