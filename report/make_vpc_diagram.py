"""Generate the BZ-Agent custom VPC diagram (PNG)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY = "#0f172a"; BLUE = "#2563eb"; GREEN = "#10b981"
ORANGE = "#f59e0b"; CYAN = "#0891b2"; SLATE = "#475569"; PURPLE = "#7c3aed"

fig, ax = plt.subplots(figsize=(11, 8))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, text, fc, tc="white", fs=10, bold=True, ec="white", lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.5",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=fs, fontweight="bold" if bold else "normal", zorder=3)


def dashed(x, y, w, h, text, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1",
                                fc="none", ec=ec, lw=2, ls="--", zorder=1))
    ax.text(x + 1.5, y + h - 2.4, text, ha="left", va="center", color=ec,
            fontsize=9.5, fontweight="bold", zorder=3)


def arrow(x1, y1, x2, y2, color=SLATE, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=16,
                                 color=color, lw=2, zorder=1, shrinkA=3, shrinkB=3))


ax.text(50, 96, "BZ-Agent — Custom VPC (eu-central-1)", ha="center",
        fontsize=15, fontweight="bold", color=NAVY)

# Internet (external services)
box(8, 86, 84, 6, "Internet   —   Browser  ·  Open Data Hub APIs  ·  Amazon Bedrock", SLATE, fs=10)

# Internet Gateway
box(38, 75, 24, 6, "Internet Gateway\n(bz-agent-igw)", BLUE, fs=9.5)
arrow(50, 86, 50, 81)  # internet <-> IGW
arrow(50, 81, 50, 86, color=SLATE)

# VPC outer box
dashed(6, 14, 88, 56, "VPC  10.0.0.0/16   (vpc-04fbfc7f0acc95a49)", NAVY)

# Route table
box(38, 62, 24, 6, "Route table\n0.0.0.0/0 → IGW", PURPLE, fs=9)
arrow(50, 75, 50, 68)

# Public subnet
dashed(12, 30, 50, 28, "Public subnet  10.0.1.0/24", GREEN)
# EC2 inside subnet
box(20, 40, 34, 9, "EC2 instance  :8080\n(BZ-Agent server + agents)", GREEN, fs=9.5)
# Security group ring note
box(20, 33, 34, 4.5, "Security Group: inbound TCP 8080 only", "#065f46", fs=8.5)
arrow(50, 62, 40, 49)  # route table -> ec2 (egress path)

# DynamoDB gateway endpoint
box(66, 40, 24, 9, "DynamoDB\nGateway Endpoint\n(private, free)", CYAN, fs=8.5)
arrow(54, 44, 66, 44)  # ec2 -> endpoint

# DynamoDB (AWS service, outside VPC but private)
box(66, 22, 24, 7, "Amazon DynamoDB\nbz-agent-state", "#155e75", fs=9)
arrow(78, 40, 78, 29)  # endpoint -> dynamodb

# Legend / flow note
ax.text(50, 9, "Browser & ODH/Bedrock traffic → Internet Gateway   |   DynamoDB traffic → private endpoint (never leaves AWS)",
        ha="center", fontsize=9, style="italic", color=SLATE)

plt.tight_layout()
plt.savefig("vpc_diagram.png", dpi=160, bbox_inches="tight", facecolor="white")
print("saved vpc_diagram.png")
