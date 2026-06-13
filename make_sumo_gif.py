"""Render the SUMO simulation headlessly to PNG frames (synthetic, no footage).
Vehicles are coloured by speed: red = stopped, green = moving."""
import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import traci

SUMO = r"C:\Users\erden\New folder\traffic-sim\.venv\Lib\site-packages\sumo\bin\sumo.exe"
FRAMES = "sumo/frames"
shutil.rmtree(FRAMES, ignore_errors=True)
os.makedirs(FRAMES)

traci.start([SUMO, "-c", "sumo/zddz_current.sumocfg", "--start", "--quit-on-end", "true"])

N = 160
for step in range(N):
    traci.simulationStep()
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")
    # the four roads (two avenues crossing)
    ax.plot([0, 0], [-300, 300], color="#3a3a3a", lw=16, solid_capstyle="round", zorder=1)
    ax.plot([-300, 300], [0, 0], color="#3a3a3a", lw=16, solid_capstyle="round", zorder=1)
    xs, ys, cs = [], [], []
    for v in traci.vehicle.getIDList():
        x, y = traci.vehicle.getPosition(v)
        xs.append(x); ys.append(y); cs.append(traci.vehicle.getSpeed(v))
    if xs:
        ax.scatter(xs, ys, c=cs, cmap="RdYlGn", vmin=0, vmax=13.9, s=45,
                   edgecolors="none", zorder=3)
    ax.set_xlim(-310, 310); ax.set_ylim(-310, 310)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"Zuun Dorvon Zam — SUMO model   t = {step}s",
                 color="#cccccc", fontsize=10)
    fig.savefig(f"{FRAMES}/f{step:04d}.png", facecolor=fig.get_facecolor())
    plt.close(fig)

traci.close()
print(f"wrote {N} frames")
