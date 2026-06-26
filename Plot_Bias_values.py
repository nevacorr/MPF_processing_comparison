"""
Bias Forest Plot — Desikan-Killiany Atlas, GM & WM
Averaged across hemispheres.

Inputs:
    Excel spreadsheet with columns:
        Region          : "GM", "WM", or "Subcortical"
        Subregion       : DK atlas region name
        Side            : "Left" or "Right"

        For each comparison (MPF-MPFreg, MPF-MPRAGE, MPFreg-MPRAGE):
            Bias_<comparison>       : bias (method A - method B)
            Lower_CI_<comparison>   : lower CI
            Upper_CI_<comparison>   : upper CI

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = "your_bias_data.xlsx"      # ← update this
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/TablesForPlottingBias.xlsx"       # ← update this
OUTPUT_DIR = Path(".")

DATA_TYPE    = "Volume"                    # "MPF" or "Volume"
MEASURE_TYPE = "relative"               # "absolute" or "relative" — ignored if DATA_TYPE = "Volume"

if DATA_TYPE == "Volume":
    SHEET_NAME    = "Volume-Mean Relative Difference"
    MEASURE_LABEL = "Mean Relative Difference (%)"
    FILE_LABEL    = "volume_mean_relative_difference"
elif MEASURE_TYPE == "absolute":
    SHEET_NAME    = "MPF-Mean Absolute Difference"
    MEASURE_LABEL = "Mean Absolute Difference (%)"
    FILE_LABEL    = "mpf_mean_absolute_difference"
else:
    SHEET_NAME    = "MPF-Mean Relative Difference"
    MEASURE_LABEL = "Mean Relative Difference (%)"
    FILE_LABEL    = "mpf_mean_relative_difference"

# ── Column name map ───────────────────────────────────────────────────────────

COL = {
    "region"    : "Region",
    "subregion" : "Subregion",
    "side"      : "Side",

    # ── MPF − MPFreg ──────────────────────────────────────────────────────
    "bias_1"    : "Mean Bias MPFvMPFreg",
    "bias_lo_1" : "Lower CI MPFvMPFreg",
    "bias_hi_1" : "Upper CI MPFvMPFreg",
    "pval_1"    : "Adj. P-value MPFvMPFreg",

    # ── MPF − MPRAGE ──────────────────────────────────────────────────────
    "bias_2"    : "Mean Bias MPFvMPRAGE",
    "bias_lo_2" : "Lower CI MPFvMPRAGE",
    "bias_hi_2" : "Upper CI MPFvMPRAGE",
    "pval_2"    : "Adj. P-value MPFvMPRAGE",

    # ── MPFreg − MPRAGE ───────────────────────────────────────────────────
    "bias_3"    : "Mean Bias MPFregvMPRAGE",
    "bias_lo_3" : "Lower CI MPFregvMPRAGE",
    "bias_hi_3" : "Upper CI MPFregvMPRAGE",
    "pval_3"    : "Adj. P-value MPFregvMPRAGE",
}

# ── Plotting options ───────────────────────────────────────────────────────────
REFERENCE_LINE    = 0.0
ALPHA_THRESHOLD   = 0.05            # p-value cutoff for significance
GM_COLOR          = "#4C72B0"       # blue
WM_COLOR          = "#E07B39"       # orange
SUBCORTICAL_COLOR = "#1A1A1A"       # gray
NS_COLOR          = "#AAAAAA"       # light gray — non-significant (all tissue types)
MARKER_SIZE       = 6
LINEWIDTH         = 1.4
DODGE             = 0.22            # vertical separation between GM and WM markers

# ── Sort order ────────────────────────────────────────────────────────────────
# "gm_bias"     : sort by average GM bias across all comparisons
# "gm_abs_bias" : sort by average absolute GM bias (magnitude, ignores direction)
# "alphabetical": A–Z by region name
SORT_BY = "gm_bias"

# ── Font sizes — adjust all in one place ──────────────────────────────────────
FONT = {
    "title"  : 15,
    "xlabel" : 17,
    "ylabel" : 17,
    "xtick"  : 17,
    "ytick"  : 17,
    "legend" : 17,
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load & prepare data
# ─────────────────────────────────────────────────────────────────────────────
df_raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)

# Standardise cerebrum subregion names → "cerebrum"
df_raw[COL["subregion"]] = df_raw[COL["subregion"]].str.replace(
    r'(?i)cerebrum.*', 'cerebrum', regex=True
)

# ── GM / WM ──
df = df_raw[df_raw[COL["region"]].isin(["GM", "WM"])].copy()

bias_cols = [v for k, v in COL.items() if k not in ("region", "subregion", "side")]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Average Left and Right hemispheres for each Subregion × Region
# ─────────────────────────────────────────────────────────────────────────────
avg = (
    df.groupby([COL["subregion"], COL["region"]])[bias_cols]
    .mean()
    .reset_index()
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Comparisons dictionary
# ─────────────────────────────────────────────────────────────────────────────
COMPARISONS = {
    "MPF − MPFreg"   : (COL["bias_1"], COL["bias_lo_1"], COL["bias_hi_1"], COL["pval_1"]),
    "MPF − MPRAGE"   : (COL["bias_2"], COL["bias_lo_2"], COL["bias_hi_2"], COL["pval_2"]),
    "MPFreg − MPRAGE": (COL["bias_3"], COL["bias_lo_3"], COL["bias_hi_3"], COL["pval_3"]),
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Compute ONE fixed region sort order
# ─────────────────────────────────────────────────────────────────────────────
gm_avg = avg[avg[COL["region"]] == "GM"].copy()
wm_avg = avg[avg[COL["region"]] == "WM"].copy()

bias_point_cols = [cols[0] for cols in COMPARISONS.values()]

if SORT_BY == "gm_bias":
    gm_avg["_sort"] = gm_avg[bias_point_cols].mean(axis=1)
    ascending = True      # most negative bias at bottom, least negative at top
elif SORT_BY == "gm_abs_bias":
    gm_avg["_sort"] = gm_avg[bias_point_cols].abs().mean(axis=1)
    ascending = True      # smallest magnitude at top
elif SORT_BY == "alphabetical":
    gm_avg["_sort"] = gm_avg[COL["subregion"]]
    ascending = False     # A at top
else:
    raise ValueError(f"Unknown SORT_BY value: '{SORT_BY}'. "
                     "Choose 'gm_bias', 'gm_abs_bias', or 'alphabetical'.")

REGION_ORDER = gm_avg.sort_values("_sort", ascending=ascending)[COL["subregion"]].tolist()

# Append any WM-only regions not in GM list
wm_only = [r for r in wm_avg[COL["subregion"]].tolist() if r not in REGION_ORDER]
REGION_ORDER = wm_only + REGION_ORDER

# Force cerebrum to the top
if "cerebrum" in REGION_ORDER:
    REGION_ORDER.remove("cerebrum")
    REGION_ORDER.append("cerebrum")

N_REGIONS = len(REGION_ORDER)
Y_POS     = {r: i for i, r in enumerate(REGION_ORDER)}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Subcortical data — averaged across hemispheres
# ─────────────────────────────────────────────────────────────────────────────
df_sub = df_raw[df_raw[COL["region"]] == "Subcortical"].copy()
avg_sub = (
    df_sub.groupby([COL["subregion"], COL["region"]])[bias_cols]
    .mean()
    .reset_index()
)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Core draw function — GM & WM panel
# ─────────────────────────────────────────────────────────────────────────────
def draw_panel(ax, avg_df, bias_col, lo_col, hi_col, pval_col, show_yticks=True):
    """
    Draw GM and WM bias estimates with CIs onto ax.
    Significant regions (p < ALPHA_THRESHOLD) are colored; others are gray.
    X-axis is auto-scaled to the data.
    """
    gm = avg_df[avg_df[COL["region"]] == "GM"]
    wm = avg_df[avg_df[COL["region"]] == "WM"]

    # ── Plot GM ──
    for _, row in gm.iterrows():
        r    = row[COL["subregion"]]
        y    = Y_POS[r] + DODGE
        bias = row[bias_col]
        lo   = row[lo_col]
        hi   = row[hi_col]
        pval = row[pval_col]
        color = GM_COLOR if pval < ALPHA_THRESHOLD else NS_COLOR
        ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
        ax.plot(bias, y, "o", color=color, ms=MARKER_SIZE, zorder=3)

    # ── Plot WM ──
    for _, row in wm.iterrows():
        r    = row[COL["subregion"]]
        y    = Y_POS[r] - DODGE
        bias = row[bias_col]
        lo   = row[lo_col]
        hi   = row[hi_col]
        pval = row[pval_col]
        color = WM_COLOR if pval < ALPHA_THRESHOLD else NS_COLOR
        ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
        ax.plot(bias, y, "s", color=color, ms=MARKER_SIZE, zorder=3)

    # ── Reference line at 0 ──
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

    # ── X-axis — auto-scaled ──
    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Subcortical draw function
# ─────────────────────────────────────────────────────────────────────────────
def draw_subcortical_panel(ax, sub_df, bias_col, lo_col, hi_col, pval_col,
                           sub_region_order, show_yticks=True):
    """
    Draw subcortical bias estimates — single tissue type.
    Significant regions colored, non-significant gray.
    """
    n_sub     = len(sub_region_order)
    y_pos_sub = {r: i for i, r in enumerate(sub_region_order)}

    for _, row in sub_df.iterrows():
        r    = row[COL["subregion"]]
        if r not in y_pos_sub:
            continue
        y    = y_pos_sub[r]
        bias = row[bias_col]
        lo   = row[lo_col]
        hi   = row[hi_col]
        pval = row[pval_col]
        color = SUBCORTICAL_COLOR if pval < ALPHA_THRESHOLD else NS_COLOR
        ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
        ax.plot(bias, y, "D", color=color, ms=MARKER_SIZE, zorder=3)

    ax.axvline(REFERENCE_LINE, color="gray", linestyle="--", lw=1.2, zorder=1)

    for i in range(n_sub):
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="whitesmoke", zorder=0)

    ax.set_yticks(range(n_sub))
    if show_yticks:
        ax.set_yticklabels(sub_region_order, fontsize=FONT["ytick"])
    else:
        ax.set_yticklabels([])

    ax.set_ylim(-0.5, n_sub - 0.5)
    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Compute subcortical sort order (once, shared across panels)
# ─────────────────────────────────────────────────────────────────────────────
sub_bias_cols = [cols[0] for cols in COMPARISONS.values()]
avg_sub_sorted = avg_sub.copy()
avg_sub_sorted["_sort"] = avg_sub_sorted[sub_bias_cols].mean(axis=1)
SUB_REGION_ORDER = avg_sub_sorted.sort_values("_sort", ascending=True)[COL["subregion"]].tolist()
n_sub_regions    = len(SUB_REGION_ORDER)

# ── Compute shared x limits across all comparisons and tissue types ──
all_lo_cols  = [COL["bias_lo_1"], COL["bias_lo_2"], COL["bias_lo_3"]]
all_hi_cols  = [COL["bias_hi_1"], COL["bias_hi_2"], COL["bias_hi_3"]]
global_min   = min(avg[all_lo_cols].min().min(), avg_sub[all_lo_cols].min().min())
global_max   = max(avg[all_hi_cols].max().max(), avg_sub[all_hi_cols].max().max())
padding      = (global_max - global_min) * 0.05   # 5% padding on each side
X_LIM        = (global_min - padding, global_max + padding)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Combined GM + WM figure — all three comparisons side by side
# ─────────────────────────────────────────────────────────────────────────────
comp_items = list(COMPARISONS.items())
n_panels   = len(comp_items)
fig_height = max(8, N_REGIONS * 0.38)
fig_width  = 8 * n_panels

fig, axes = plt.subplots(
    1, n_panels,
    figsize=(fig_width, fig_height),
    sharey=False,
)

for idx, (comp_name, (bias_col, lo_col, hi_col, pval_col)) in enumerate(comp_items):
    ax          = axes[idx]
    show_yticks = (idx == 0)

    draw_panel(ax, avg, bias_col, lo_col, hi_col, pval_col, show_yticks=show_yticks)

    ax.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    ax.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)

    if show_yticks:
        ax.set_ylabel("DK Atlas Region", fontsize=FONT["ylabel"])

# ── Shared legend ──
gm_patch  = mpatches.Patch(color=GM_COLOR, label=f"Gray Matter (p < {ALPHA_THRESHOLD})")
wm_patch  = mpatches.Patch(color=WM_COLOR, label=f"White Matter (p < {ALPHA_THRESHOLD})")
ns_patch  = mpatches.Patch(color=NS_COLOR,  label="Not significant")
ref_line  = plt.Line2D([0], [0], color="gray", linestyle="--",
                       lw=1.2, label="Difference = 0")

fig.legend(
    handles=[gm_patch, wm_patch, ns_patch, ref_line],
    loc="upper right",
    ncol=4,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(1.0, 0.985),
)

fig.suptitle(
    f"{MEASURE_LABEL} — All Comparisons - {SHEET_NAME}\nDK Atlas, Hemispheres Averaged",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=1.01,
)

plt.tight_layout()
combined_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_all_comparisons_{SHEET_NAME}.png"
fig.savefig(combined_out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {combined_out}")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Subcortical combined figure — all three comparisons side by side
# ─────────────────────────────────────────────────────────────────────────────
fig_height_sub = max(6, n_sub_regions * 0.38)

fig_sub, axes_sub = plt.subplots(
    1, n_panels,
    figsize=(fig_width, fig_height_sub),
    sharey=False,
)

for idx, (comp_name, (bias_col, lo_col, hi_col, pval_col)) in enumerate(comp_items):
    ax          = axes_sub[idx]
    show_yticks = (idx == 0)

    draw_subcortical_panel(ax, avg_sub, bias_col, lo_col, hi_col, pval_col,
                           SUB_REGION_ORDER, show_yticks=show_yticks)

    ax.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    ax.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)

    if show_yticks:
        ax.set_ylabel("Subcortical Region", fontsize=FONT["ylabel"])

# ── Shared legend ──
sub_patch    = mpatches.Patch(color=SUBCORTICAL_COLOR, label=f"Subcortical(p < {ALPHA_THRESHOLD})")
ns_patch_sub  = mpatches.Patch(color=NS_COLOR, label="Not significant")
ref_line_sub = plt.Line2D([0], [0], color="gray", linestyle="--",
                          lw=1.2, label="Difference = 0")

fig_sub.legend(
    handles=[sub_patch, ns_patch_sub, ref_line_sub],
    loc="upper right",
    ncol=3,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(1.0, 0.96),
)

fig_sub.suptitle(
    f"{MEASURE_LABEL} — All Comparisons - {SHEET_NAME}\nSubcortical Regions, Hemispheres Averaged",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=1.01,
)

plt.tight_layout()
subcortical_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_subcortical_{SHEET_NAME}.png"
fig_sub.savefig(subcortical_out, dpi=150, bbox_inches="tight")
plt.close(fig_sub)
print(f"Saved: {subcortical_out}")
