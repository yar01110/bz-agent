"""Chart: single instance vs ALB+ASG fleet (throughput + p50 latency vs concurrency)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

conc = [50, 100, 200, 300]
single_tput = [187, 115, 88, 78]
fleet_tput = [248, 142, 125, 133]
single_p50 = [223, 627, 2213, 5172]
fleet_p50 = [99, 469, 1088, 2188]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
fig.patch.set_facecolor("white")
x = np.arange(len(conc))
w = 0.38

# Throughput grouped bars
ax1.bar(x - w / 2, single_tput, w, label="Single EC2", color="#94a3b8")
ax1.bar(x + w / 2, fleet_tput, w, label="ALB + ASG (2 inst.)", color="#2563eb")
ax1.set_xticks(x); ax1.set_xticklabels(conc)
ax1.set_xlabel("Concurrent connections"); ax1.set_ylabel("Throughput (req/s)")
ax1.set_title("Throughput — higher is better", fontweight="bold", fontsize=11)
ax1.legend(); ax1.grid(axis="y", alpha=0.3)

# p50 latency lines
ax2.plot(conc, single_p50, "-o", color="#94a3b8", lw=2.5, label="Single EC2")
ax2.plot(conc, fleet_p50, "-o", color="#2563eb", lw=2.5, label="ALB + ASG (2 inst.)")
ax2.set_xlabel("Concurrent connections"); ax2.set_ylabel("p50 latency (ms)")
ax2.set_title("Median latency — lower is better", fontweight="bold", fontsize=11)
ax2.legend(); ax2.grid(alpha=0.3)

fig.suptitle("Elasticity: horizontal scaling raises the ceiling (/health)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
plt.savefig("elastic_chart.png", dpi=160, bbox_inches="tight", facecolor="white")
print("saved elastic_chart.png")
