import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── File path ─────────────────────────────────────────────────────────────────

EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper data/TablesForPlottingBiasWithAvg.xlsx"
OUTPUT_DIR = Path("/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper figures")

DATA_TYPE    = "Volume"                    # "MPF" or "Volume"
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
ALPHA_THRESHOLD   = 0.05
GM_COLOR          = "#4C72B0"
WM_COLOR          = "#E07B39"
SUBCORTICAL_COLOR = "#1A1A1A"
NS_COLOR          = "#AAAAAA"
MARKER_SIZE       = 6
LINEWIDTH         = 1.4
DODGE             = 0.22

# ── Sort order ────────────────────────────────────────────────────────────────
# "gm_bias"     : sort by average GM bias across all comparisons
# "gm_abs_bias" : sort by average absolute GM bias (magnitude, ignores direction)
# "alphabetical": A–Z by region name
SORT_BY = "gm_bias"

SIDE_VALUE = "Average"

# Lobe-level ROIs shown with cerebrum in panel A
LOBE_LABELS = ["frontal", "parietal", "temporal", "occipital"]

FONT = {
    "title"  : 15,
    "xlabel" : 17,
    "ylabel" : 17,
    "xtick"  : 17,
    "ytick"  : 17,
    "legend" : 17,
}

# Distance between the y-axis spine and region-name tick labels
YTICK_PAD = 8


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load and prepare data
# ─────────────────────────────────────────────────────────────────────────────
df_raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)

df_raw[COL["subregion"]] = df_raw[COL["subregion"]].str.replace(
    r"(?i)cerebrum.*", "cerebrum", regex=True
)
df_raw[COL["subregion"]] = df_raw[COL["subregion"]].str.strip()

df = df_raw[
    df_raw[COL["region"]].isin(["GM", "WM"])
    & (df_raw[COL["side"]] == SIDE_VALUE)
].copy()

bias_cols = [
    value for key, value in COL.items()
    if key not in ("region", "subregion", "side")
]
scale_cols = [
    value for key, value in COL.items()
    if key.startswith("bias_")
    or key.startswith("bias_lo_")
    or key.startswith("bias_hi_")
]

df[scale_cols] = df[scale_cols] * 100


# ─────────────────────────────────────────────────────────────────────────────
# 2. Use the pre-averaged hemisphere rows
# ─────────────────────────────────────────────────────────────────────────────
avg = df[[COL["subregion"], COL["region"]] + bias_cols].copy()

lobe_set = {"cerebrum", *[label.lower() for label in LOBE_LABELS]}
is_lobe = avg[COL["subregion"]].str.lower().isin(lobe_set)

avg_lobe   = avg[is_lobe].copy()
avg_parcel = avg[~is_lobe].copy()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Comparisons
# ─────────────────────────────────────────────────────────────────────────────
COMPARISONS = {
    "MPFreg − MPF"   : (COL["bias_1"], COL["bias_lo_1"], COL["bias_hi_1"], COL["pval_1"]),
    "MPRAGE − MPF"   : (COL["bias_2"], COL["bias_lo_2"], COL["bias_hi_2"], COL["pval_2"]),
    "MPRAGE − MPFreg": (COL["bias_3"], COL["bias_lo_3"], COL["bias_hi_3"], COL["pval_3"]),
}
bias_point_cols = [columns[0] for columns in COMPARISONS.values()]


# ─────────────────────────────────────────────────────────────────────────────
# 4. Compute fixed region orders
# ─────────────────────────────────────────────────────────────────────────────
def compute_region_order(avg_subset, force_top=None):
    gm_subset = avg_subset[avg_subset[COL["region"]] == "GM"].copy()
    wm_subset = avg_subset[avg_subset[COL["region"]] == "WM"].copy()

    if SORT_BY == "gm_bias":
        gm_subset["_sort"] = gm_subset[bias_point_cols].mean(axis=1)
        ascending = True
    elif SORT_BY == "gm_abs_bias":
        gm_subset["_sort"] = gm_subset[bias_point_cols].abs().mean(axis=1)
        ascending = True
    elif SORT_BY == "alphabetical":
        gm_subset["_sort"] = gm_subset[COL["subregion"]]
        ascending = False
    else:
        raise ValueError(
            f"Unknown SORT_BY value: '{SORT_BY}'. "
            "Choose 'gm_bias', 'gm_abs_bias', or 'alphabetical'."
        )

    order = (
        gm_subset.sort_values("_sort", ascending=ascending)[COL["subregion"]]
        .tolist()
    )

    wm_only = [
        region for region in wm_subset[COL["subregion"]].tolist()
        if region not in order
    ]
    order = wm_only + order

    if force_top:
        for label in force_top:
            if label in order:
                order.remove(label)
                order.append(label)

    return order


LOBE_REGION_ORDER   = compute_region_order(avg_lobe, force_top=["cerebrum"])
PARCEL_REGION_ORDER = compute_region_order(avg_parcel)

N_LOBE_REGIONS   = len(LOBE_REGION_ORDER)
N_PARCEL_REGIONS = len(PARCEL_REGION_ORDER)

LOBE_Y_POS   = {region: index for index, region in enumerate(LOBE_REGION_ORDER)}
PARCEL_Y_POS = {region: index for index, region in enumerate(PARCEL_REGION_ORDER)}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Subcortical data
# ─────────────────────────────────────────────────────────────────────────────
df_sub = df_raw[
    (df_raw[COL["region"]] == "Subcortical")
    & (df_raw[COL["side"]] == SIDE_VALUE)
].copy()
df_sub[scale_cols] = df_sub[scale_cols] * 100

avg_sub = df_sub[[COL["subregion"], COL["region"]] + bias_cols].copy()


def compute_bias_stats(df_in, region_label, bias_col, pval_col):
    sig = df_in[df_in[pval_col] < ALPHA_THRESHOLD]
    pos = sig[sig[bias_col] > 0][bias_col]
    neg = sig[sig[bias_col] < 0][bias_col]

    return {
        "Region"   : region_label,
        "Pos_N"    : len(pos),
        "Pos_Mean" : round(pos.mean(), 4) if len(pos) > 0 else np.nan,
        "Pos_Min"  : round(pos.min(), 4) if len(pos) > 0 else np.nan,
        "Pos_Max"  : round(pos.max(), 4) if len(pos) > 0 else np.nan,
        "Neg_N"    : len(neg),
        "Neg_Mean" : round(neg.mean(), 4) if len(neg) > 0 else np.nan,
        "Neg_Min"  : round(neg.min(), 4) if len(neg) > 0 else np.nan,
        "Neg_Max"  : round(neg.max(), 4) if len(neg) > 0 else np.nan,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Draw GM/WM panels
# ─────────────────────────────────────────────────────────────────────────────
def draw_panel(
    ax,
    avg_df,
    bias_col,
    lo_col,
    hi_col,
    pval_col,
    region_order,
    y_pos,
    n_regions,
    show_yticks=True,
):
    gm = avg_df[avg_df[COL["region"]] == "GM"]
    wm = avg_df[avg_df[COL["region"]] == "WM"]

    for _, row in gm.iterrows():
        region = row[COL["subregion"]]
        if region not in y_pos:
            continue

        y = y_pos[region] + DODGE
        color = GM_COLOR if row[pval_col] < ALPHA_THRESHOLD else NS_COLOR
        ax.plot(
            [row[lo_col], row[hi_col]], [y, y],
            color=color, lw=LINEWIDTH, zorder=2,
        )
        ax.plot(row[bias_col], y, "o", color=color, ms=MARKER_SIZE, zorder=3)

    for _, row in wm.iterrows():
        region = row[COL["subregion"]]
        if region not in y_pos:
            continue

        y = y_pos[region] - DODGE
        color = WM_COLOR if row[pval_col] < ALPHA_THRESHOLD else NS_COLOR
        ax.plot(
            [row[lo_col], row[hi_col]], [y, y],
            color=color, lw=LINEWIDTH, zorder=2,
        )
        ax.plot(row[bias_col], y, "s", color=color, ms=MARKER_SIZE, zorder=3)

    ax.axvline(
        REFERENCE_LINE, color="gray", linestyle="--", lw=1.2, zorder=1
    )

    for index in range(n_regions):
        if index % 2 == 0:
            ax.axhspan(index - 0.5, index + 0.5, color="whitesmoke", zorder=0)

    ax.set_yticks(range(n_regions))
    if show_yticks:
        # Use normal Matplotlib font and normal right-aligned tick labels.
        ax.set_yticklabels(region_order, fontsize=FONT["ytick"])
    else:
        ax.set_yticklabels([])

    ax.set_ylim(-0.5, n_regions - 0.5)
    ax.tick_params(axis="y", pad=YTICK_PAD)
    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Draw subcortical panels
# ─────────────────────────────────────────────────────────────────────────────
def draw_subcortical_panel(
    ax,
    sub_df,
    bias_col,
    lo_col,
    hi_col,
    pval_col,
    sub_region_order,
    show_yticks=True,
):
    n_sub = len(sub_region_order)
    y_pos_sub = {
        region: index for index, region in enumerate(sub_region_order)
    }

    for _, row in sub_df.iterrows():
        region = row[COL["subregion"]]
        if region not in y_pos_sub:
            continue

        y = y_pos_sub[region]
        color = (
            SUBCORTICAL_COLOR
            if row[pval_col] < ALPHA_THRESHOLD
            else NS_COLOR
        )
        ax.plot(
            [row[lo_col], row[hi_col]], [y, y],
            color=color, lw=LINEWIDTH, zorder=2,
        )
        ax.plot(row[bias_col], y, "D", color=color, ms=MARKER_SIZE, zorder=3)

    ax.axvline(
        REFERENCE_LINE, color="gray", linestyle="--", lw=1.2, zorder=1
    )

    for index in range(n_sub):
        if index % 2 == 0:
            ax.axhspan(index - 0.5, index + 0.5, color="whitesmoke", zorder=0)

    ax.set_yticks(range(n_sub))
    if show_yticks:
        # Use the same normal font as all other plot text.
        ax.set_yticklabels(
            [region.lower() for region in sub_region_order],
            fontsize=FONT["ytick"],
        )
    else:
        ax.set_yticklabels([])

    ax.set_ylim(-0.5, n_sub - 0.5)
    ax.tick_params(axis="y", pad=YTICK_PAD)
    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Subcortical order and shared x-axis limits
# ─────────────────────────────────────────────────────────────────────────────
avg_sub_sorted = avg_sub.copy()
avg_sub_sorted["_sort"] = avg_sub_sorted[bias_point_cols].mean(axis=1)
SUB_REGION_ORDER = (
    avg_sub_sorted.sort_values("_sort", ascending=True)[COL["subregion"]]
    .tolist()
)
n_sub_regions = len(SUB_REGION_ORDER)

all_lo_cols = [COL["bias_lo_1"], COL["bias_lo_2"], COL["bias_lo_3"]]
all_hi_cols = [COL["bias_hi_1"], COL["bias_hi_2"], COL["bias_hi_3"]]

global_min = min(
    avg[all_lo_cols].min().min(),
    avg_sub[all_lo_cols].min().min(),
)
global_max = max(
    avg[all_hi_cols].max().max(),
    avg_sub[all_hi_cols].max().max(),
)
padding = (global_max - global_min) * 0.05
X_LIM = (global_min - padding, global_max + padding)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Combined figure
# ─────────────────────────────────────────────────────────────────────────────
comp_items = list(COMPARISONS.items())
n_panels = len(comp_items)

height_ratios = [N_LOBE_REGIONS, N_PARCEL_REGIONS, n_sub_regions]
fig_width = 8 * n_panels
row_unit = 0.38
fig_height = (
    max(3, N_LOBE_REGIONS * row_unit)
    + max(8, N_PARCEL_REGIONS * row_unit)
    + max(6, n_sub_regions * row_unit)
)

fig, axes = plt.subplots(
    3,
    n_panels,
    figsize=(fig_width, fig_height),
    gridspec_kw={"height_ratios": height_ratios, "hspace": 0.2},
    sharey=False,
)

axes = np.atleast_2d(axes)
if axes.shape[0] != 3:
    axes = axes.T

PANEL_LABEL_FONT = FONT["title"] + 8

for idx, (comp_name, columns) in enumerate(comp_items):
    bias_col, lo_col, hi_col, pval_col = columns

    ax_lobe   = axes[0, idx]
    ax_parcel = axes[1, idx]
    ax_sub    = axes[2, idx]
    show_yticks = idx == 0

    draw_panel(
        ax_lobe,
        avg_lobe,
        bias_col,
        lo_col,
        hi_col,
        pval_col,
        LOBE_REGION_ORDER,
        LOBE_Y_POS,
        N_LOBE_REGIONS,
        show_yticks=show_yticks,
    )
    ax_lobe.set_title(
        comp_name,
        fontsize=FONT["title"],
        fontweight="bold",
        pad=10,
    )
    ax_lobe.set_xlabel("")
    if show_yticks:
        ax_lobe.set_ylabel("Region", fontsize=FONT["ylabel"])

    draw_panel(
        ax_parcel,
        avg_parcel,
        bias_col,
        lo_col,
        hi_col,
        pval_col,
        PARCEL_REGION_ORDER,
        PARCEL_Y_POS,
        N_PARCEL_REGIONS,
        show_yticks=show_yticks,
    )
    ax_parcel.set_xlabel("")
    if show_yticks:
        ax_parcel.set_ylabel("Region", fontsize=FONT["ylabel"])

    draw_subcortical_panel(
        ax_sub,
        avg_sub,
        bias_col,
        lo_col,
        hi_col,
        pval_col,
        SUB_REGION_ORDER,
        show_yticks=show_yticks,
    )
    ax_sub.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    if show_yticks:
        ax_sub.set_ylabel("Region", fontsize=FONT["ylabel"])

# Align the three y-axis titles without modifying the tick-label font or text.
fig.align_ylabels(axes[:, 0])

for row_idx, label in enumerate(["A", "B", "C"]):
    axes[row_idx, 0].text(
        -0.45,
        1.0,
        label,
        transform=axes[row_idx, 0].transAxes,
        fontsize=PANEL_LABEL_FONT,
        fontweight="bold",
        ha="left",
        va="bottom",
        zorder=10,
        clip_on=False,
    )

# Shared legend
gm_patch = mpatches.Patch(
    color=GM_COLOR,
    label=f"Gray Matter (p < {ALPHA_THRESHOLD})",
)
wm_patch = mpatches.Patch(
    color=WM_COLOR,
    label=f"White Matter (p < {ALPHA_THRESHOLD})",
)
sub_patch = mpatches.Patch(
    color=SUBCORTICAL_COLOR,
    label=f"Subcortical (p < {ALPHA_THRESHOLD})",
)
ns_patch = mpatches.Patch(color=NS_COLOR, label="Not significant")
ref_line = plt.Line2D(
    [0], [0],
    color="gray",
    linestyle="--",
    lw=1.2,
    label="Difference = 0",
)

fig.legend(
    handles=[gm_patch, wm_patch, sub_patch, ns_patch, ref_line],
    loc="upper center",
    ncol=5,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(0.45, 0.94),
)

fig.suptitle(
    f"{MEASURE_LABEL} — All Comparisons - {SHEET_NAME}\n"
    "DK Atlas + Subcortical, Hemispheres Averaged",
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

for comp_name, columns in COMPARISONS.items():
    bias_col, lo_col, hi_col, pval_col = columns

    gm_parcel_data = avg_parcel[avg_parcel[COL["region"]] == "GM"]
    row = compute_bias_stats(
        gm_parcel_data,
        f"{comp_name} — GM",
        bias_col,
        pval_col,
    )
    row["Comparison"] = comp_name
    summary_rows.append(row)

    wm_parcel_data = avg_parcel[avg_parcel[COL["region"]] == "WM"]
    row = compute_bias_stats(
        wm_parcel_data,
        f"{comp_name} — WM",
        bias_col,
        pval_col,
    )
    row["Comparison"] = comp_name
    summary_rows.append(row)

    gm_lobe_data = avg_lobe[avg_lobe[COL["region"]] == "GM"]
    row = compute_bias_stats(
        gm_lobe_data,
        f"{comp_name} — GM (Cerebrum/Lobes)",
        bias_col,
        pval_col,
    )
    row["Comparison"] = comp_name
    summary_rows.append(row)

    wm_lobe_data = avg_lobe[avg_lobe[COL["region"]] == "WM"]
    row = compute_bias_stats(
        wm_lobe_data,
        f"{comp_name} — WM (Cerebrum/Lobes)",
        bias_col,
        pval_col,
    )
    row["Comparison"] = comp_name
    summary_rows.append(row)

    row = compute_bias_stats(
        avg_sub,
        f"{comp_name} — Subcortical",
        bias_col,
        pval_col,
    )
    row["Comparison"] = comp_name
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)[[
    "Comparison",
    "Region",
    "Pos_N",
    "Pos_Mean",
    "Pos_Min",
    "Pos_Max",
    "Neg_N",
    "Neg_Mean",
    "Neg_Min",
    "Neg_Max",
]]

print("\n── Bias Summary Statistics ──")
print(summary_df.to_string(index=False))

stats_out = OUTPUT_DIR / f"{FILE_LABEL}_bias_summary_stats_{SHEET_NAME}.csv"
summary_df.to_csv(stats_out, index=False)
print(f"\nSaved: {stats_out}")
