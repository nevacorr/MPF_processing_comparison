"""
ICC Forest Plot — Desikan-Killiany Atlas, GM & WM
Averaged across hemispheres, sorted by GM ICC (descending).

Inputs:
    Excel spreadsheet with columns:
        Region          : "GM", "WM", or "Subcortical"
        Subregion       : DK atlas region name
        Side            : "Left" or "Right"

        For each comparison (MPF_v_MPFreg, MPF_v_MPRAGE, MPFreg_v_MPRAGE):
            ICC_C_<comparison>      : ICC consistency
            ICC_C_lower_<comparison>: lower CI (consistency)
            ICC_C_upper_<comparison>: upper CI (consistency)
            ICC_A_<comparison>      : ICC absolute
            ICC_A_lower_<comparison>: lower CI (absolute)
            ICC_A_upper_<comparison>: upper CI (absolute)

    ── Update the COLUMN NAME MAP below to match your actual headers ──
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/TablesForPlottingICC.xlsx"       # ← update this
OUTPUT_DIR = Path(".")

# ── Column name map ───────────────────────────────────────────────────────────
# Update the VALUES (right side) to match your exact Excel headers.
# Keys are used internally — do not change them.

COL = {
    "region"    : "Region",
    "subregion" : "Subregion",
    "side"      : "Side",

    # ── MPF vs MPFreg ──────────────────────────────────────────────────────
    "icc_c_1"   : "ICC Consistency MPFvMPFreg",
    "icc_c_lo_1": "Lower CI Consistency MPFvMPFreg",
    "icc_c_hi_1": "Upper CI Consistency MPFvMPFreg",
    "icc_a_1"   : "ICC Absolute MPFvMPFreg",
    "icc_a_lo_1": "Lower CI Absolute MPFvMPFreg",
    "icc_a_hi_1": "Upper CI Absolute MPFvMPFreg",

    # ── MPF vs MPRAGE ──────────────────────────────────────────────────────
    "icc_c_2"   : "ICC Consistency MPFvMPRAGE",
    "icc_c_lo_2": "Lower CI Consistency MPFvMPRAGE",
    "icc_c_hi_2": "Upper CI Consistency MPFvMPRAGE",
    "icc_a_2"   : "ICC Absolute MPFvMPRAGE",
    "icc_a_lo_2": "Lower CI Absolute MPFvMPRAGE",
    "icc_a_hi_2": "Upper CI Absolute MPFvMPRAGE",

    # ── MPFreg vs MPRAGE ───────────────────────────────────────────────────
    "icc_c_3"   : "ICC Consistency MPFregvMPRAGE",
    "icc_c_lo_3": "Lower CI Consistency MPFregvMPRAGE",
    "icc_c_hi_3": "Upper CI Consistency MPFregvMPRAGE",
    "icc_a_3"   : "ICC Absolute MPFregvMPRAGE",
    "icc_a_lo_3": "Lower CI Absolute MPFregvMPRAGE",
    "icc_a_hi_3": "Upper CI Absolute MPFregvMPRAGE",
}

# ── Plotting options ───────────────────────────────────────────────────────────
ICC_TYPE        = "consistency"   # "consistency" or "absolute"
REFERENCE_LINE  = 0.75
GM_COLOR        = "#E07B39"       # orange
WM_COLOR        = "#4C72B0"       # blue
MARKER_SIZE     = 6
LINEWIDTH       = 1.4
DODGE           = 0.22            # vertical separation between GM and WM markers

# ── Font sizes — adjust all in one place ──────────────────────────────────────
FONT = {
    "title"  : 15,
    "xlabel" : 13,
    "ylabel" : 13,
    "xtick"  : 11,
    "ytick"  : 10,
    "legend" : 10,
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load & prepare data
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_excel(EXCEL_PATH)

# Filter to GM and WM only (exclude Subcortical for DK atlas plot)
df = df[df[COL["region"]].isin(["GM", "WM"])].copy()

# Exclude whole-brain "cerebrum" rows
# Comment out the next line if you WANT to include them
# df = df[~df[COL["subregion"]].str.lower().str.contains("cerebrum", na=False)]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Average Left and Right hemispheres for each Subregion × Region
# ─────────────────────────────────────────────────────────────────────────────
icc_cols = [v for k, v in COL.items() if k not in ("region", "subregion", "side")]
avg = (
    df.groupby([COL["subregion"], COL["region"]])[icc_cols]
    .mean()
    .reset_index()
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Determine which ICC columns to use based on ICC_TYPE
# ─────────────────────────────────────────────────────────────────────────────
PREFIX = "icc_c" if ICC_TYPE == "consistency" else "icc_a"

COMPARISONS = {
    "MPF vs MPFreg"   : (COL[f"{PREFIX}_1"], COL[f"{PREFIX}_lo_1"], COL[f"{PREFIX}_hi_1"]),
    "MPF vs MPRAGE"   : (COL[f"{PREFIX}_2"], COL[f"{PREFIX}_lo_2"], COL[f"{PREFIX}_hi_2"]),
    "MPFreg vs MPRAGE": (COL[f"{PREFIX}_3"], COL[f"{PREFIX}_lo_3"], COL[f"{PREFIX}_hi_3"]),
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Compute ONE fixed region sort order
#    Sorted by average GM ICC across all three comparisons (ascending so
#    highest ICC ends up at the top of the plot).
# ─────────────────────────────────────────────────────────────────────────────
gm_avg = avg[avg[COL["region"]] == "GM"].copy()
wm_avg = avg[avg[COL["region"]] == "WM"].copy()

# Average the ICC point estimates across all three comparisons for GM
gm_icc_cols = [cols[0] for cols in COMPARISONS.values()]   # just the point estimates
gm_avg["_mean_icc"] = gm_avg[gm_icc_cols].mean(axis=1)

# Sort ascending so highest ICC appears at the TOP of the figure
REGION_ORDER = gm_avg.sort_values("_mean_icc", ascending=True)[COL["subregion"]].tolist()

# Append any WM-only regions not represented in GM (rare but possible)
wm_only = [r for r in wm_avg[COL["subregion"]].tolist() if r not in REGION_ORDER]
REGION_ORDER = wm_only + REGION_ORDER   # WM-only regions go to the bottom

# Force cerebrum to the top of the plot
if "cerebrum" in REGION_ORDER:
    REGION_ORDER.remove("cerebrum")
    REGION_ORDER.append("cerebrum")

N_REGIONS  = len(REGION_ORDER)
Y_POS      = {r: i for i, r in enumerate(REGION_ORDER)}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Core draw function — draws one comparison panel onto a given Axes object
# ─────────────────────────────────────────────────────────────────────────────
def draw_panel(ax, avg_df, icc_col, lo_col, hi_col,
               show_yticks=True):
    """
    Draw GM and WM ICC estimates with CIs onto ax.
    Uses the globally fixed REGION_ORDER and Y_POS.

    show_yticks : if True, render region labels on the y-axis (left panel only)
    """
    gm = avg_df[avg_df[COL["region"]] == "GM"]
    wm = avg_df[avg_df[COL["region"]] == "WM"]

    # ── Plot GM ──
    for _, row in gm.iterrows():
        r   = row[COL["subregion"]]
        y   = Y_POS[r] + DODGE
        icc = row[icc_col]
        lo  = row[lo_col]
        hi  = row[hi_col]
        ax.plot([lo, hi], [y, y], color=GM_COLOR, lw=LINEWIDTH, zorder=2)
        ax.plot(icc, y, "o", color=GM_COLOR, ms=MARKER_SIZE, zorder=3)

    # ── Plot WM ──
    for _, row in wm.iterrows():
        r   = row[COL["subregion"]]
        y   = Y_POS[r] - DODGE
        icc = row[icc_col]
        lo  = row[lo_col]
        hi  = row[hi_col]
        ax.plot([lo, hi], [y, y], color=WM_COLOR, lw=LINEWIDTH, zorder=2)
        ax.plot(icc, y, "s", color=WM_COLOR, ms=MARKER_SIZE, zorder=3)

    # ── Reference line ──
    ax.axvline(REFERENCE_LINE, color="gray", linestyle="--", lw=1.2, zorder=1)

    # ── Alternating row shading ──
    for i in range(N_REGIONS):
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="whitesmoke", zorder=0)

    # ── Y-axis ──
    ax.set_yticks(range(N_REGIONS))
    if show_yticks:
        ax.set_yticklabels(REGION_ORDER, fontsize=FONT["ytick"])
    else:
        ax.set_yticklabels([])

    ax.set_ylim(-0.5, N_REGIONS - 0.5)

    # ── X-axis ──
    ax.set_xlim(-0.05, 1.05)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Individual plots (one per comparison)
# ─────────────────────────────────────────────────────────────────────────────
def make_single_plot(avg_df, icc_col, lo_col, hi_col, title, outfile):
    fig, ax = plt.subplots(figsize=(10, max(6, N_REGIONS * 0.38)))
    draw_panel(ax, avg_df, icc_col, lo_col, hi_col, show_yticks=True)

    ax.set_xlabel(f"ICC ({ICC_TYPE.capitalize()})", fontsize=FONT["xlabel"])
    ax.set_ylabel("DK Atlas Region", fontsize=FONT["ylabel"])
    ax.set_title(title, fontsize=FONT["title"], fontweight="bold", pad=10)

    # Legend
    gm_patch = mpatches.Patch(color=GM_COLOR, label="Gray Matter")
    wm_patch = mpatches.Patch(color=WM_COLOR, label="White Matter")
    ref_line  = plt.Line2D([0], [0], color="gray", linestyle="--",
                           lw=1.2, label=f"ICC = {REFERENCE_LINE}")
    ax.legend(handles=[gm_patch, wm_patch, ref_line],
              loc="lower right", fontsize=FONT["legend"], framealpha=0.9)

    plt.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {outfile}")


for comp_name, (icc_col, lo_col, hi_col) in COMPARISONS.items():
    safe_name = comp_name.replace(" ", "_").replace("/", "")
    outfile   = OUTPUT_DIR / f"icc_forest_{safe_name}_{ICC_TYPE}.png"
    title     = (f"ICC ({ICC_TYPE.capitalize()}) — {comp_name}\n"
                 f"DK Atlas Regions, Hemispheres Averaged")
    make_single_plot(avg, icc_col, lo_col, hi_col, title, outfile)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Combined figure — all three comparisons side by side
#
#    • All panels share the SAME fixed region order (average GM ICC)
#    • Y-axis region labels appear on the LEFT panel only
#    • Shared legend below the figure
# ─────────────────────────────────────────────────────────────────────────────
comp_items  = list(COMPARISONS.items())       # [(name, (icc, lo, hi)), ...]
n_panels    = len(comp_items)
fig_height  = max(8, N_REGIONS * 0.38)
fig_width   = 8 * n_panels                   # ~8 inches per panel

fig, axes = plt.subplots(
    1, n_panels,
    figsize=(fig_width, fig_height),
    sharey=False,          # sharey=False so we control labels manually
)

for idx, (comp_name, (icc_col, lo_col, hi_col)) in enumerate(comp_items):
    ax           = axes[idx]
    show_yticks  = (idx == 0)              # labels only on leftmost panel

    draw_panel(ax, avg, icc_col, lo_col, hi_col, show_yticks=show_yticks)

    ax.set_xlabel(f"ICC ({ICC_TYPE.capitalize()})", fontsize=FONT["xlabel"])
    ax.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)

    if show_yticks:
        ax.set_ylabel("DK Atlas Region", fontsize=FONT["ylabel"])

# ── Shared legend below all panels ──
gm_patch = mpatches.Patch(color=GM_COLOR, label="Gray Matter")
wm_patch = mpatches.Patch(color=WM_COLOR, label="White Matter")
ref_line  = plt.Line2D([0], [0], color="gray", linestyle="--",
                       lw=1.2, label=f"ICC = {REFERENCE_LINE}")
fig.legend(
    handles=[gm_patch, wm_patch, ref_line],
    loc="lower center",
    ncol=3,
    fontsize=FONT["legend"],
    framealpha=0.9,
    bbox_to_anchor=(0.5, -0.02),
)

fig.suptitle(
    f"ICC ({ICC_TYPE.capitalize()}) — All Comparisons\nDK Atlas, Hemispheres Averaged",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=1.01,
)

plt.tight_layout()
combined_out = OUTPUT_DIR / f"icc_forest_all_comparisons_{ICC_TYPE}.png"
fig.savefig(combined_out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {combined_out}")