"""Render a side-by-side SUMO comparison GIF (fixed vs smart signal), headless.
Vehicles coloured by speed: red = stopped (queue), green = moving. Synthetic — no footage.
Traffic is scaled up so the difference between the two signals is visible."""
import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import traci

SUMO = r"C:\Users\erden\New folder\traffic-sim\.venv\Lib\site-packages\sumo\bin\sumo.exe"
FRAMES = "sumo/frames"
SCALE = 2.0
N = 220
shutil.rmtree(FRAMES, ignore_errors=True)
os.makedirs(FRAMES)


def run(net):
    traci.start([SUMO, "-c", "sumo/zddz_current.sumocfg", "--net-file", net,
                 "--scale", str(SCALE), "--start", "--quit-on-end", "true"])
    data = []
    for _ in range(N):
        traci.simulationStep()
        data.append([traci.vehicle.getPosition(v) + (traci.vehicle.getSpeed(v),)
                     for v in traci.vehicle.getIDList()])
    traci.close()
    return data


fixed = run("sumo/zddz.net.xml")
smart = run("sumo/zddz_act.net.xml")
print("simulated both; rendering...")


def panel(ax, frame, title, waited):
    ax.set_facecolor("#0d0d0d")
    ax.plot([0, 0], [-300, 300], color="#333", lw=12, solid_capstyle="round", zorder=1)
    ax.plot([-300, 300], [0, 0], color="#333", lw=12, solid_capstyle="round", zorder=1)
    if frame:
        xs, ys, cs = zip(*frame)
        ax.scatter(xs, ys, c=cs, cmap="RdYlGn", vmin=0, vmax=13.9, s=55,
                   edgecolors="none", zorder=3)
    ax.set_xlim(-310, 310); ax.set_ylim(-310, 310)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, color="#dddddd", fontsize=12, pad=6)
    ax.text(0, -285, f"total waiting: {waited:,} car-seconds", ha="center",
            color="#ff7066", fontsize=11, zorder=4)


def stopped(frame):
    return sum(1 for (_x, _y, s) in frame if s < 0.1)


cumL = cumR = 0
for step in range(N):
    cumL += stopped(fixed[step])
    cumR += stopped(smart[step])
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9, 5.0), dpi=100)
    fig.patch.set_facecolor("#0d0d0d")
    panel(axL, fixed[step], "Current: fixed-time light", cumL)
    panel(axR, smart[step], "Smart: adaptive light", cumR)
    fig.suptitle("Same traffic, two signals — red = stopped, green = moving",
                 color="#bbbbbb", fontsize=11, y=0.97)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(f"{FRAMES}/f{step:04d}.png", facecolor=fig.get_facecolor())
    plt.close(fig)

print(f"wrote {N} frames")
