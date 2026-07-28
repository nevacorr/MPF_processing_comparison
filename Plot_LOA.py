import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/TablesForPlottingLOA.xlsx"
OUTPUT_DIR = Path(".")
DATA_TYPE  = "MPF"    # "Volume" or "MPF" — also controls which sheet is read
CEREBRUM_LABEL = "cerebrum"  # exact name of the cerebrum subregion in your data

GM_COLOR = "#4C72B0"    # blue
WM_COLOR = "#E07B39"    # orange

FONT = {
    "title"  : 15,
    "xlabel" : 17,
    "ylabel" : 17,
    "xtick"  : 17,
    "ytick"  : 11,
    "legend" : 17,
}

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_excel(EXCEL_PATH, sheet_name=DATA_TYPE)

# ── 2. Tidy column names and normalize Region values ─────────────────────────
df.columns = df.columns.str.strip()
df["Region"] = df["Region"].str.strip().str.upper()

# ── 3. Filter: keep only GM and WM ───────────────────────────────────────────
df = df[df["Region"].isin(["GM", "WM"])].copy()

# ── 4. Clean Subregion: strip embedded tissue suffixes (_gm, _wm) ─────────────
df["Subregion"] = (
    df["Subregion"]
    .str.strip()
    .str.replace(r"_(gm|wm)$", "", case=False, regex=True)
    .str.strip()
)

# ── 5. Define the three comparisons ──────────────────────────────────────────
comparisons = [
    {
        "label": "MPFreg vs MPF",
        "lower": "Lower MPFvMPFreg",
        "upper": "Upper MPFvMPFreg",
    },
    {
        "label": "MPRAGE vs MPF",
        "lower": "Lower MPFvMPRAGE",
        "upper": "Upper MPFvMPRAGE",
    },
    {
        "label": "MPRAGE vs MPFreg",
        "lower": "Lower MPFregvMPRAGE",
        "upper": "Upper MPFregvMPRAGE",
    },
]

# ── 6. Compute a consistent subregion order from the first comparison ─────────
first = comparisons[0]
df["LOA_width"] = df[first["upper"]] - df[first["lower"]]
df_avg_order = (
    df.groupby(["Region", "Subregion"], as_index=False)["LOA_width"].mean()
)
wide_order = df_avg_order.pivot(index="Subregion", columns="Region", values="LOA_width").reset_index()
wide_order.columns.name = None
wide_order = wide_order.dropna(subset=["GM", "WM"])
wide_order_sorted = wide_order.sort_values("GM").reset_index(drop=True)
subregion_order = wide_order_sorted["Subregion"].tolist()

# ── Move Cerebrum to the end so it appears at the top of the y-axis ──────────
if CEREBRUM_LABEL in subregion_order:
    subregion_order.remove(CEREBRUM_LABEL)
    subregion_order.append(CEREBRUM_LABEL)

# ── 7. Compute global x-axis limits from AVERAGED values (same as plotted) ───
all_widths = []
for comp in comparisons:
    df["LOA_width"] = df[comp["upper"]] - df[comp["lower"]]
    df_avg = df.groupby(["Region", "Subregion"], as_index=False)["LOA_width"].mean()
    all_widths.extend(df_avg["LOA_width"].dropna().tolist())
x_min = min(all_widths)
x_max = max(all_widths)
x_pad = (x_max - x_min) * 0.05
x_lim = (x_min - x_pad, x_max + x_pad)

# ── 8. Build figure with one panel per comparison ─────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(20, 8))
fig.suptitle(f"[{DATA_TYPE}]  LOA Width — GM vs WM", fontsize=FONT["title"], fontweight="bold")

legend_handles = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=GM_COLOR, markersize=8, label="GM"),
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=WM_COLOR, markersize=8, label="WM"),
]

for ax, comp in zip(axes, comparisons):
    df["LOA_width"] = df[comp["upper"]] - df[comp["lower"]]

    # Average left and right hemispheres per subregion per tissue type
    df_avg = (
        df.groupby(["Region", "Subregion"], as_index=False)["LOA_width"].mean()
    )

    # Pivot to wide: one row per subregion, columns = GM / WM
    wide = df_avg.pivot(index="Subregion", columns="Region", values="LOA_width").reset_index()
    wide.columns.name = None
    wide = wide.dropna(subset=["GM", "WM"])

    # Apply consistent ordering (Cerebrum at top)
    wide["Subregion"] = pd.Categorical(wide["Subregion"], categories=subregion_order, ordered=True)
    wide = wide.sort_values("Subregion").reset_index(drop=True)

    y = np.arange(len(wide))

    for i, row in wide.iterrows():
        ax.plot([row["GM"], row["WM"]], [i, i], color="gray", linewidth=0.8, zorder=1)

    sc_gm = ax.scatter(wide["GM"], y, color=GM_COLOR, zorder=2, label="GM", s=40)
    sc_wm = ax.scatter(wide["WM"], y, color=WM_COLOR, zorder=2, label="WM", s=40)

    ax.set_yticks(y)
    ax.set_yticklabels(wide["Subregion"], fontsize=FONT["ytick"])
    ax.set_xlabel("LOA Width", fontsize=FONT["xlabel"])
    ax.set_title(comp["label"], fontsize=FONT["title"], fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_xlim(x_lim)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])

    ax.legend(
        handles=legend_handles,
        loc="lower right",
        fontsize=FONT["legend"],
        framealpha=0.7,
    )

plt.tight_layout()
plt.savefig(OUTPUT_DIR / f"{DATA_TYPE}_loa_GM_vs_WM.png", dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {OUTPUT_DIR / f'{DATA_TYPE}_loa_GM_vs_WM.png'}")
