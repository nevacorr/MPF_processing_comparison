import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = "your_bias_data.xlsx"      # ← update this
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/TablesForPlottingBias.xlsx"       # ← update this
OUTPUT_DIR = Path(".")

DATA_TYPE    = "MPF"                    # "MPF" or "Volume"
MEASURE_TYPE = "relative"               # "absolute" or "relative" — ignored if DATA_TYPE = "Volume"

if DATA_TYPE == "Volume":
    SHEET_NAME    = "Volume-Mean Relative Difference"
    MEASURE_LABEL = "Volume Mean Relative Difference (%)"
    FILE_LABEL    = "volume_mean_relative_difference"
elif MEASURE_TYPE == "absolute":
    SHEET_NAME    = "MPF-Mean Absolute Difference"
    MEASURE_LABEL = "MPF Mean Absolute Difference (%)"
    FILE_LABEL    = "mpf_mean_absolute_difference"
else:
    SHEET_NAME    = "MPF-Mean Relative Difference"
    MEASURE_LABEL = "MPF Mean Relative Difference (%)"
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
scale_cols = [v for k, v in COL.items() if k.startswith("bias_") or k.startswith("bias_lo_") or k.startswith("bias_hi_")]

df[scale_cols] = df[scale_cols] * 100
# ─────────────────────────────────────────────────────────────────────────────
# 2. Average Left and Right hemispheres for each Subregion × Region and convert to percent by multiplying by 100
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
    "MPFreg − MPF"   : (COL["bias_1"], COL["bias_lo_1"], COL["bias_hi_1"], COL["pval_1"]),
    "MPRAGE − MPF"   : (COL["bias_2"], COL["bias_lo_2"], COL["bias_hi_2"], COL["pval_2"]),
    "MPRAGE − MPFreg": (COL["bias_3"], COL["bias_lo_3"], COL["bias_hi_3"], COL["pval_3"]),
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
df_sub[scale_cols] = df_sub[scale_cols] * 100

avg_sub = (
    df_sub.groupby([COL["subregion"], COL["region"]])[bias_cols]
    .mean()
    .reset_index()
)

# ─────────────────────────────────────────────────────────────────────────────
# 5b. Summary statistics — hemisphere-averaged significant bias values
# ─────────────────────────────────────────────────────────────────────────────
def compute_bias_stats(df_in, region_label, bias_col, pval_col):
    sig = df_in[df_in[pval_col] < ALPHA_THRESHOLD]
    pos = sig[sig[bias_col] > 0][bias_col]
    neg = sig[sig[bias_col] < 0][bias_col]
    return {
        "Region"   : region_label,
        "Pos_N"    : len(pos),
        "Pos_Mean" : round(pos.mean(), 4) if len(pos) > 0 else np.nan,
        "Pos_Min"  : round(pos.min(),  4) if len(pos) > 0 else np.nan,
        "Pos_Max"  : round(pos.max(),  4) if len(pos) > 0 else np.nan,
        "Neg_N"    : len(neg),
        "Neg_Mean" : round(neg.mean(), 4) if len(neg) > 0 else np.nan,
        "Neg_Min"  : round(neg.min(),  4) if len(neg) > 0 else np.nan,
        "Neg_Max"  : round(neg.max(),  4) if len(neg) > 0 else np.nan,
    }

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
        ax.set_yticklabels([r.lower() for r in sub_region_order], fontsize=FONT["ytick"])
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
# 9. Combined figure — cortical (GM/WM) on top, subcortical below,
#    all three comparisons side by side
# ─────────────────────────────────────────────────────────────────────────────
comp_items = list(COMPARISONS.items())
n_panels   = len(comp_items)

# Row heights proportional to the number of regions in each row, so marker
# spacing looks visually consistent between the cortical and subcortical rows.
height_ratios = [N_REGIONS, n_sub_regions]
fig_width     = 8 * n_panels
row_unit      = 0.38                                  # inches per region row
fig_height    = max(8, N_REGIONS * row_unit) + max(6, n_sub_regions * row_unit)

fig, axes = plt.subplots(
    2, n_panels,
    figsize=(fig_width, fig_height),
    gridspec_kw={"height_ratios": height_ratios, "hspace": 0.15},
    sharey=False,
)

# Guarantee axes is always 2D (n_panels could be 1)
axes = np.atleast_2d(axes)
if axes.shape[0] != 2:
    axes = axes.T

# Panel-label font size (fixed, independent of FONT dict — meant to stand out)
PANEL_LABEL_FONT = FONT["title"] + 8

for idx, (comp_name, (bias_col, lo_col, hi_col, pval_col)) in enumerate(comp_items):
    ax_top    = axes[0, idx]
    ax_bottom = axes[1, idx]
    show_yticks = (idx == 0)

    # ── Top row: cortical GM/WM ──
    draw_panel(ax_top, avg, bias_col, lo_col, hi_col, pval_col, show_yticks=show_yticks)
    ax_top.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)
    ax_top.set_xlabel("")                 # no x label on top row — shared axis below
    if show_yticks:
        ax_top.set_ylabel("Region", fontsize=FONT["ylabel"])

    # ── Bottom row: subcortical ──
    draw_subcortical_panel(ax_bottom, avg_sub, bias_col, lo_col, hi_col, pval_col,
                           SUB_REGION_ORDER, show_yticks=show_yticks)
    ax_bottom.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)
    ax_bottom.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    if show_yticks:
        ax_bottom.set_ylabel("Region", fontsize=FONT["ylabel"])

# ── Row labels "A" / "B" — outside the plot area, above and left of the
#    y-axis region labels. Negative x / >1 y in axes-fraction coordinates
#    place the text outside the panel; tune -0.25/1.08 if labels overlap
#    the region names (longer names need a more negative x).
axes[0, 0].text(
    -0.45, 1.0, "A",
    transform=axes[0, 0].transAxes,
    fontsize=PANEL_LABEL_FONT, fontweight="bold",
    ha="left", va="bottom", zorder=10, clip_on=False,
)
axes[1, 0].text(
    -0.45, 1.0, "B",
    transform=axes[1, 0].transAxes,
    fontsize=PANEL_LABEL_FONT, fontweight="bold",
    ha="left", va="bottom", zorder=10, clip_on=False,
)

# ── Shared legend (cortical + subcortical) — placed just under the title ──
gm_patch     = mpatches.Patch(color=GM_COLOR, label=f"Gray Matter (p < {ALPHA_THRESHOLD})")
wm_patch     = mpatches.Patch(color=WM_COLOR, label=f"White Matter (p < {ALPHA_THRESHOLD})")
sub_patch    = mpatches.Patch(color=SUBCORTICAL_COLOR, label=f"Subcortical (p < {ALPHA_THRESHOLD})")
ns_patch     = mpatches.Patch(color=NS_COLOR,  label="Not significant")
ref_line     = plt.Line2D([0], [0], color="gray", linestyle="--",
                          lw=1.2, label="Difference = 0")

fig.legend(
    handles=[gm_patch, wm_patch, sub_patch, ns_patch, ref_line],
    loc="upper center",
    ncol=5,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(0.45, 0.94),
)

fig.suptitle(
    f"{MEASURE_LABEL} — All Comparisons - {SHEET_NAME}\nDK Atlas + Subcortical, Hemispheres Averaged",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=1.06,
)

plt.tight_layout(rect=[0, 0, 1, 0.94])
combined_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_combined_{SHEET_NAME}.png"
fig.savefig(combined_out, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {combined_out}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. Print and save summary statistics
# ─────────────────────────────────────────────────────────────────────────────
summary_rows = []

for comp_name, (bias_col, lo_col, hi_col, pval_col) in COMPARISONS.items():

    # GM
    gm_data = avg[avg[COL["region"]] == "GM"]
    row = compute_bias_stats(gm_data, f"{comp_name} — GM", bias_col, pval_col)
    row["Comparison"] = comp_name
    summary_rows.append(row)

    # WM
    wm_data = avg[avg[COL["region"]] == "WM"]
    row = compute_bias_stats(wm_data, f"{comp_name} — WM", bias_col, pval_col)
    row["Comparison"] = comp_name
    summary_rows.append(row)

    # Subcortical
    row = compute_bias_stats(avg_sub, f"{comp_name} — Subcortical", bias_col, pval_col)
    row["Comparison"] = comp_name
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)[[
    "Comparison", "Region",
    "Pos_N", "Pos_Mean", "Pos_Min", "Pos_Max",
    "Neg_N", "Neg_Mean", "Neg_Min", "Neg_Max",
]]

print("\n── Bias Summary Statistics ──")
print(summary_df.to_string(index=False))

stats_out = OUTPUT_DIR / f"{FILE_LABEL}_bias_summary_stats_{SHEET_NAME}.csv"
summary_df.to_csv(stats_out, index=False)
print(f"\nSaved: {stats_out}")