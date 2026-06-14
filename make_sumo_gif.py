"""Side-by-side SUMO comparison GIF (fixed vs adaptive signal), headless + synthetic.
Each side shows the junction (dots = vehicles, red=stopped/green=moving) plus a
'total waiting' bar that grows in real time, so the adaptive light's advantage
is obvious at a glance. Traffic is scaled up so the difference is visible."""
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
ZOOM = 230
shutil.rmtree(FRAMES, ignore_errors=True)
os.makedirs(FRAMES)


def run(net):
    traci.start([SUMO, "-c", "sumo/zddz_current.sumocfg", "--net-file", net,
                 "--scale", str(SCALE), "--start", "--quit-on-end", "true"])
    # real node positions (netconvert recenters coords, so fetch them)
    nodes = {j: traci.junction.getPosition(j) for j in ["C", "N", "S", "E", "W"]}
    data = []
    for _ in range(N):
        traci.simulationStep()
        data.append([traci.vehicle.getPosition(v) + (traci.vehicle.getSpeed(v),)
                     for v in traci.vehicle.getIDList()])
    traci.close()
    return data, nodes


fixed, NODES = run("sumo/zddz.net.xml")
smart, _ = run("sumo/zddz_act.net.xml")
CX, CY = NODES["C"]
print("simulated both; rendering...")

# cumulative "waiting" (vehicle-seconds with speed < 0.1) per step
def cum(data):
    out, total = [], 0
    for frame in data:
        total += sum(1 for (_x, _y, s) in frame if s < 0.1)
        out.append(total)
    return out


cumL, cumR = cum(fixed), cum(smart)
MAXW = max(cumL[-1], cumR[-1]) or 1


def junction(ax, frame, title):
    ax.set_facecolor("#0d0d0d")
    for outer in ["N", "S", "E", "W"]:                        # draw real road geometry
        ox, oy = NODES[outer]
        ax.plot([ox, CX], [oy, CY], color="#333", lw=14, solid_capstyle="round", zorder=1)
    if frame:
        xs, ys, cs = zip(*frame)
        ax.scatter(xs, ys, c=cs, cmap="RdYlGn", vmin=0, vmax=13.9, s=70,
                   edgecolors="none", zorder=3)
    ax.set_xlim(CX - ZOOM, CX + ZOOM); ax.set_ylim(CY - ZOOM, CY + ZOOM)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, color="#eeeeee", fontsize=13, pad=4)


def bar(ax, value, color):
    ax.set_facecolor("#0d0d0d")
    ax.barh(0, MAXW, color="#222", height=0.6)               # track
    ax.barh(0, value, color=color, height=0.6)               # fill
    ax.set_xlim(0, MAXW); ax.set_ylim(-1, 1); ax.axis("off")
    ax.text(MAXW * 0.5, 0, f"{value:,} car-seconds waited", ha="center", va="center",
            color="#ffffff", fontsize=10, zorder=5)


for step in range(N):
    fig = plt.figure(figsize=(9, 5.2), dpi=100)
    fig.patch.set_facecolor("#0d0d0d")
    gs = fig.add_gridspec(2, 2, height_ratios=[7, 1], hspace=0.15, wspace=0.06,
                          left=0.02, right=0.98, top=0.9, bottom=0.06)
    junction(fig.add_subplot(gs[0, 0]), fixed[step], "Current: fixed-time light")
    junction(fig.add_subplot(gs[0, 1]), smart[step], "Smart: adaptive light")
    bar(fig.add_subplot(gs[1, 0]), cumL[step], "#ff4136")
    bar(fig.add_subplot(gs[1, 1]), cumR[step], "#2ecc40")
    fig.suptitle("Same traffic, two signals  ·  red = stopped, green = moving",
                 color="#bbbbbb", fontsize=11, y=0.97)
    fig.savefig(f"{FRAMES}/f{step:04d}.png", facecolor=fig.get_facecolor())
    plt.close(fig)

print(f"wrote {N} frames; final waiting fixed={cumL[-1]:,} smart={cumR[-1]:,}")
