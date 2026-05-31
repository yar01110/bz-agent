"""Render the EC2 t3.small saturation curve (throughput + p95 latency vs concurrency)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

conc = [25, 50, 100, 150, 200, 300, 400]
tput = [322, 187, 115, 97, 88, 78, 90]
p95 = [230, 730, 2603, 5048, 6984, 14699, 15035]  # ms

fig, ax1 = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor("white")

c1 = "#2563eb"
ax1.set_xlabel("Concurrent connections", fontsize=11)
ax1.set_ylabel("Throughput (req/s)", color=c1, fontsize=11)
ax1.plot(conc, tput, "-o", color=c1, lw=2.5, label="Throughput")
ax1.tick_params(axis="y", labelcolor=c1)
ax1.axvline(25, color="#10b981", ls="--", lw=1.2, alpha=0.7)
ax1.annotate("peak throughput\n(~25 conc, 322 req/s)", xy=(25, 322), xytext=(70, 300),
             fontsize=9, color="#10b981")

c2 = "#ef4444"
ax2 = ax1.twinx()
ax2.set_ylabel("p95 latency (ms)", color=c2, fontsize=11)
ax2.plot(conc, p95, "-s", color=c2, lw=2.5, label="p95 latency")
ax2.tick_params(axis="y", labelcolor=c2)
ax2.axvspan(150, 200, color="#f59e0b", alpha=0.15)
ax2.annotate("latency spike\n(150–200)", xy=(175, 6000), xytext=(210, 4000),
             fontsize=9, color="#b45309")

plt.title("EC2 t3.small saturation curve — /health endpoint", fontsize=13, fontweight="bold")
fig.tight_layout()
plt.savefig("loadchart.png", dpi=160, bbox_inches="tight", facecolor="white")
print("saved loadchart.png")
