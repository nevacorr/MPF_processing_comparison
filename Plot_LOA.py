import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper data/TablesForPlottingLOAWithAvg.xlsx"
OUTPUT_DIR = Path("/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper figures")

DATA_TYPE  = "MPF"
SIDE_COLUMN = "Side"
AVERAGE_SIDE_LABEL = "Average"

PANEL_A_SUBREGIONS = ["cerebrum", "frontal", "parietal", "temporal", "occipital"]

GM_COLOR = "#4C72B0"    # blue
WM_COLOR = "#E07B39"    # orange

FONT = {
    "title"  : 15,
    "xlabel" : 17,
    "ylabel" : 17,
    "xtick"  : 17,
    "ytick"  : 11,
    "legend" : 17,
    "panel"  : 17,
}

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

# ── Load and clean data ───────────────────────────────────────────────────
df = pd.read_excel(EXCEL_PATH, sheet_name=f"{DATA_TYPE}abs")
df.columns = df.columns.str.strip()

# Use only the supplied Average rows; Left and Right are excluded.
df = df[df[SIDE_COLUMN] == AVERAGE_SIDE_LABEL].copy()
df = df[df["Region"].isin(["GM", "WM"])].copy()

# Remove the lowercase tissue suffixes from the subregion names.
df["Subregion"] = df["Subregion"].str.replace(
    r"_(gm|wm)$", "", regex=True
)

def make_wide(data, comparison):
    """Calculate LOA width and pivot without averaging rows."""
    values = data[["Region", "Subregion"]].copy()
    values["LOA_width"] = (
        data[comparison["upper"]] - data[comparison["lower"]]
    )

    wide = values.pivot(
        index="Subregion", columns="Region", values="LOA_width"
    ).reset_index()
    wide.columns.name = None
    return wide.dropna(subset=["GM", "WM"]).copy()

# ── Establish consistent ordering from the first comparison ──────────────────
first_wide = make_wide(df, comparisons[0])
first_wide["mean_width"] = first_wide[["GM", "WM"]].mean(axis=1)

panel_a_order = sorted(
    PANEL_A_SUBREGIONS,
    key=lambda name: first_wide.loc[
        first_wide["Subregion"] == name, "mean_width"
    ].iloc[0],
)

# Put cerebrum at the top of panel A. The final item is displayed at the top.
panel_a_order.remove("cerebrum")
panel_a_order.append("cerebrum")

panel_b_order = (
    first_wide.loc[
        ~first_wide["Subregion"].isin(PANEL_A_SUBREGIONS)
    ]
    .sort_values("GM")["Subregion"]
    .tolist()
)

# ── Global x-axis limits from the exact Average values being plotted ──────────
all_widths = []
for comp in comparisons:
    wide = make_wide(df, comp)
    all_widths.extend(wide[["GM", "WM"]].to_numpy().ravel())

all_widths = np.asarray(all_widths, dtype=float)
x_min, x_max = all_widths.min(), all_widths.max()
x_range = x_max - x_min
x_pad = x_range * 0.05 if x_range > 0 else 0.01
x_lim = (x_min - x_pad, x_max + x_pad)

# ── Composite figure: panel A on top and panel B below ────────────────────────
height_ratios = [max(len(panel_a_order), 2), max(len(panel_b_order), 2)]
fig_height = max(10, 0.38 * sum(height_ratios) + 3)
fig, axes = plt.subplots(
    2,
    3,
    figsize=(20, fig_height),
    gridspec_kw={"height_ratios": height_ratios},
    sharex=True,
)

fig.suptitle(
    f"[{DATA_TYPE}] LOA Width — GM vs WM",
    fontsize=FONT["title"],
    fontweight="bold",
    y=0.995,
)

legend_handles = [
    plt.Line2D(
        [0], [0], marker="o", linestyle="none", color=GM_COLOR,
        markersize=8, label="GM"
    ),
    plt.Line2D(
        [0], [0], marker="o", linestyle="none", color=WM_COLOR,
        markersize=8, label="WM"
    ),
]

legend = fig.legend(
    handles=legend_handles,
    loc="center right",
    bbox_to_anchor=(0.985, 0.95),
    bbox_transform=fig.transFigure,
    ncol=2,
    fontsize=FONT["legend"],
    frameon=True,
)

legend.get_frame().set_edgecolor("gray")
legend.get_frame().set_linewidth(0.8)
legend.get_frame().set_facecolor("white")
legend.get_frame().set_alpha(1)

def draw_panel(ax, wide, order, comparison_title=None, show_legend=False):
    wide = wide[wide["Subregion"].isin(order)].copy()
    wide["Subregion"] = pd.Categorical(
        wide["Subregion"], categories=order, ordered=True
    )
    wide = wide.sort_values("Subregion").reset_index(drop=True)
    y = np.arange(len(wide))

    for i, row in wide.iterrows():
        ax.plot(
            [row["GM"], row["WM"]], [i, i],
            color="gray", linewidth=0.8, zorder=1
        )

    ax.scatter(wide["GM"], y, color=GM_COLOR, s=40, zorder=2)
    ax.scatter(wide["WM"], y, color=WM_COLOR, s=40, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [value.replace("_", " ") for value in wide["Subregion"]],
        fontsize=FONT["ytick"],
    )
    ax.set_ylim(-0.5, len(wide) - 0.5)
    ax.set_xlim(x_lim)
    if comparison_title is None:
        ax.set_xlabel("LOA Width", fontsize=FONT["xlabel"])
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.tick_params(axis="x", labelsize=FONT["xtick"], labelbottom=True)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("gray")
        spine.set_linewidth(0.8)

    if comparison_title:
        ax.set_title(
            comparison_title, fontsize=FONT["title"], fontweight="bold"
        )
    if show_legend:
        ax.legend(
            handles=legend_handles,
            loc="lower right",
            fontsize=FONT["legend"],
            framealpha=0.7,
        )

for column, comp in enumerate(comparisons):
    wide = make_wide(df, comp)
    draw_panel(
        axes[0, column],
        wide,
        panel_a_order,
        comparison_title=comp["label"],
        show_legend=False,
    )
    draw_panel(
        axes[1, column],
        wide,
        panel_b_order,
    )

# Add A and B labels to the left of the two panel rows.
axes[0, 0].text(
    -0.28, 1.02, "A", transform=axes[0, 0].transAxes,
    fontsize=FONT["panel"], fontweight="bold", va="bottom"
)
axes[1, 0].text(
    -0.28, 1.02, "B", transform=axes[1, 0].transAxes,
    fontsize=FONT["panel"], fontweight="bold", va="bottom"
)

plt.tight_layout(rect=[0.03, 0.02, 1, 0.95])

# Save only the complete two-panel composite figure.
output_path = OUTPUT_DIR / f"{DATA_TYPE}_loa_GM_vs_WM_composite.png"
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {output_path}")
