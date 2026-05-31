"""Generate the BZ-Agent architecture diagram (PNG) for the report."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY = "#0f172a"; BLUE = "#2563eb"; ORANGE = "#f59e0b"
GREEN = "#10b981"; SLATE = "#475569"; LIGHT = "#e2e8f0"

fig, ax = plt.subplots(figsize=(11, 8.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")


def box(x, y, w, h, text, fc, tc="white", fs=11, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2",
                                fc=fc, ec="white", lw=1.5, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=fs, fontweight="bold" if bold else "normal", zorder=3, wrap=True)


def arrow(x1, y1, x2, y2, color=SLATE):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                                 color=color, lw=2, zorder=1, shrinkA=2, shrinkB=2))


fig.patch.set_facecolor("white")

# Title
ax.text(50, 96, "BZ-Agent — Cloud-Native Multi-Agent Architecture", ha="center",
        fontsize=15, fontweight="bold", color=NAVY)
ax.text(50, 92, "Smart-City Mobility & Event Orchestrator for Bolzano (AWS, eu-central-1)",
        ha="center", fontsize=10, color=SLATE)

# Client
box(38, 82, 24, 6, "Client  /  Browser", NAVY, fs=12)

# Two entry points
box(8, 67, 36, 8, "Architecture A (Serverless)\nAPI Gateway  -->  AWS Lambda", BLUE, fs=10.5)
box(56, 67, 36, 8, "Architecture B (Server)\nAmazon EC2  (FastAPI + Docker)", GREEN, fs=10.5)

arrow(46, 82, 30, 75)   # client -> A
arrow(54, 82, 70, 75)   # client -> B

# Orchestrator
box(20, 50, 60, 10, "LangGraph Orchestrator  (same container image)\n"
    "Retriever  -->  Reasoner  -->  Generator", SLATE, fs=11)

arrow(26, 67, 38, 60)   # A -> orchestrator
arrow(74, 67, 62, 60)   # B -> orchestrator

# Backend services
box(6, 30, 26, 9, "Open Data Hub\n(Tourism + Mobility\n+ Weather APIs)", ORANGE, fs=9.5)
box(37, 30, 26, 9, "Amazon Bedrock\nClaude Sonnet 4.5\n(reasoning engine)", "#7c3aed", fs=9.5)
box(68, 30, 26, 9, "Amazon DynamoDB\nSingle-table state\nPK=USER# SK=SESSION#", "#0891b2", fs=9.5)

arrow(40, 50, 22, 39)   # orchestrator -> ODH
arrow(50, 50, 50, 39)   # orchestrator -> Bedrock
arrow(60, 50, 80, 39)   # orchestrator -> DynamoDB

# IAM band
box(20, 16, 60, 6, "IAM least-privilege roles  ·  Bedrock + DynamoDB access  ·  ECR image registry",
    "#334155", fs=9.5)

ax.text(50, 8, "Live data in -> constraint reasoning -> grounded itinerary out",
        ha="center", fontsize=10, style="italic", color=SLATE)

plt.tight_layout()
plt.savefig("architecture.png", dpi=160, bbox_inches="tight", facecolor="white")
print("saved architecture.png")
