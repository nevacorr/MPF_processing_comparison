"""
ICC Consistency Forest Plot

Uses only rows where Side == "Average"; Left and Right rows are ignored.

Combined figure layout:
    A: cerebrum and lobe-level ROIs
    B: cortical parcel ROIs
    C: subcortical ROIs

Required columns:
    Region
    Subregion
    Side
    ICC Consistency MPFvMPFreg
    Lower CI Consistency MPFvMPFreg
    Upper CI Consistency MPFvMPFreg
    ICC Consistency MPFvMPRAGE
    Lower CI Consistency MPFvMPRAGE
    Upper CI Consistency MPFvMPRAGE
    ICC Consistency MPFregvMPRAGE
    Lower CI Consistency MPFregvMPRAGE
    Upper CI Consistency MPFregvMPRAGE
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── File paths and data settings ──────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper data/TablesForPlottingICCWithAvg.xlsx"
OUTPUT_DIR = Path("/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper figures")
SHEET_NAME = "Volume"  # "Volume" or "MPF"
SIDE_VALUE = "Average"

# ── Column names ──────────────────────────────────────────────────────────────
COL = {
    "region": "Region",
    "subregion": "Subregion",
    "side": "Side",

    "icc_1": "ICC Consistency MPFvMPFreg",
    "icc_lo_1": "Lower CI Consistency MPFvMPFreg",
    "icc_hi_1": "Upper CI Consistency MPFvMPFreg",

    "icc_2": "ICC Consistency MPFvMPRAGE",
    "icc_lo_2": "Lower CI Consistency MPFvMPRAGE",
    "icc_hi_2": "Upper CI Consistency MPFvMPRAGE",

    "icc_3": "ICC Consistency MPFregvMPRAGE",
    "icc_lo_3": "Lower CI Consistency MPFregvMPRAGE",
    "icc_hi_3": "Upper CI Consistency MPFregvMPRAGE",
}

COMPARISONS = {
    "MPFreg vs MPF": (COL["icc_1"], COL["icc_lo_1"], COL["icc_hi_1"]),
    "MPRAGE vs MPF": (COL["icc_2"], COL["icc_lo_2"], COL["icc_hi_2"]),
    "MPRAGE vs MPFreg": (COL["icc_3"], COL["icc_lo_3"], COL["icc_hi_3"]),
}

ICC_COLS = [
    column
    for key, column in COL.items()
    if key not in ("region", "subregion", "side")
]
ICC_POINT_COLS = [columns[0] for columns in COMPARISONS.values()]
ICC_LOWER_COLS = [columns[1] for columns in COMPARISONS.values()]
ICC_UPPER_COLS = [columns[2] for columns in COMPARISONS.values()]

# ── Plotting options ──────────────────────────────────────────────────────────
REFERENCE_LINE = 0.75
GM_COLOR = "#4C72B0"
WM_COLOR = "#E07B39"
SUBCORTICAL_COLOR = "#1A1A1A"
MARKER_SIZE = 6
LINEWIDTH = 1.4
DODGE = 0.22
YTICK_PAD = 8

FONT = {
    "title": 15,
    "xlabel": 17,
    "ylabel": 17,
    "xtick": 17,
    "ytick": 17,
    "legend": 17,
}

# Desired panel-A order, from top to bottom.
LOBE_TOP_TO_BOTTOM = [
    "cerebrum",
    "parietal",
    "frontal",
    "occipital",
    "temporal",
]
LOBE_SET = set(LOBE_TOP_TO_BOTTOM)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load and prepare the pre-averaged data
# ─────────────────────────────────────────────────────────────────────────────
df_raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df_raw.columns = df_raw.columns.str.strip()

df_raw[COL["region"]] = df_raw[COL["region"]].astype("string").str.strip()
df_raw[COL["side"]] = df_raw[COL["side"]].astype("string").str.strip()
df_raw[COL["subregion"]] = (
    df_raw[COL["subregion"]]
    .astype("string")
    .str.strip()
    .str.replace(r"(?i)^cerebrum.*$", "cerebrum", regex=True)
)

# Ignore Left and Right completely.
df_avg = df_raw[df_raw[COL["side"]].eq(SIDE_VALUE)].copy()

# GM/WM data only.
avg = df_avg[df_avg[COL["region"]].isin(["GM", "WM"])][
    [COL["subregion"], COL["region"]] + ICC_COLS
].copy()

# Separate cerebrum/lobe-level ROIs from individual cortical parcels.
is_lobe = avg[COL["subregion"]].str.lower().isin(LOBE_SET)
avg_lobe = avg[is_lobe].copy()
avg_parcel = avg[~is_lobe].copy()

# Subcortical data only.
avg_sub = df_avg[df_avg[COL["region"]].eq("Subcortical")][
    [COL["subregion"], COL["region"]] + ICC_COLS
].copy()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fixed region orders shared across all three comparison columns
# ─────────────────────────────────────────────────────────────────────────────
def compute_gm_wm_order(avg_subset):
    """Sort regions by mean GM consistency ICC, with highest values at top."""
    gm = avg_subset[avg_subset[COL["region"]].eq("GM")].copy()
    wm = avg_subset[avg_subset[COL["region"]].eq("WM")].copy()

    gm["_mean_icc"] = gm[ICC_POINT_COLS].mean(axis=1)
    order = gm.sort_values("_mean_icc", ascending=True)[COL["subregion"]].tolist()

    wm_only = [
        region
        for region in wm[COL["subregion"]].tolist()
        if region not in order
    ]
    return wm_only + order


# Matplotlib displays the final item at the top, so reverse the desired
# top-to-bottom sequence for the internal bottom-to-top y-axis order.
existing_lobes = set(avg_lobe[COL["subregion"]].str.lower())
LOBE_REGION_ORDER = [
    label
    for label in reversed(LOBE_TOP_TO_BOTTOM)
    if label in existing_lobes
]

# Preserve the actual spelling used in the spreadsheet when possible.
lobe_display_lookup = {
    str(label).lower(): str(label)
    for label in avg_lobe[COL["subregion"]].dropna().unique()
}
LOBE_REGION_ORDER = [lobe_display_lookup.get(label, label) for label in LOBE_REGION_ORDER]

PARCEL_REGION_ORDER = compute_gm_wm_order(avg_parcel)

avg_sub_sorted = avg_sub.copy()
avg_sub_sorted["_mean_icc"] = avg_sub_sorted[ICC_POINT_COLS].mean(axis=1)
SUB_REGION_ORDER = avg_sub_sorted.sort_values(
    "_mean_icc", ascending=True
)[COL["subregion"]].tolist()

N_LOBE_REGIONS = len(LOBE_REGION_ORDER)
N_PARCEL_REGIONS = len(PARCEL_REGION_ORDER)
N_SUB_REGIONS = len(SUB_REGION_ORDER)

LOBE_Y_POS = {region: index for index, region in enumerate(LOBE_REGION_ORDER)}
PARCEL_Y_POS = {region: index for index, region in enumerate(PARCEL_REGION_ORDER)}
SUB_Y_POS = {region: index for index, region in enumerate(SUB_REGION_ORDER)}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Shared x-axis limits
# ─────────────────────────────────────────────────────────────────────────────
all_plot_data = pd.concat([avg_lobe, avg_parcel, avg_sub], ignore_index=True)
global_min = min(
    all_plot_data[ICC_LOWER_COLS].min().min(),
    REFERENCE_LINE,
)
global_max = max(
    all_plot_data[ICC_UPPER_COLS].max().max(),
    REFERENCE_LINE,
)

x_range = global_max - global_min
padding = x_range * 0.05 if x_range > 0 else 0.05
X_LIM = (global_min - padding, global_max + padding)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Drawing functions
# ─────────────────────────────────────────────────────────────────────────────
def format_axis(ax, region_order, show_yticks):
    n_regions = len(region_order)

    ax.axvline(
        REFERENCE_LINE,
        color="gray",
        linestyle="--",
        lw=1.2,
        zorder=1,
    )

    for index in range(n_regions):
        if index % 2 == 0:
            ax.axhspan(index - 0.5, index + 0.5, color="whitesmoke", zorder=0)

    ax.set_yticks(range(n_regions))
    if show_yticks:
        ax.set_yticklabels(region_order, fontsize=FONT["ytick"])
    else:
        ax.set_yticklabels([])

    ax.set_ylim(-0.5, n_regions - 0.5)
    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.tick_params(axis="y", pad=YTICK_PAD)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def draw_gm_wm_panel(
    ax,
    data,
    icc_col,
    lo_col,
    hi_col,
    region_order,
    y_pos,
    show_yticks=True,
):
    gm = data[data[COL["region"]].eq("GM")]
    wm = data[data[COL["region"]].eq("WM")]

    for _, row in gm.iterrows():
        region = row[COL["subregion"]]
        if region not in y_pos:
            continue
        y = y_pos[region] + DODGE
        ax.plot(
            [row[lo_col], row[hi_col]],
            [y, y],
            color=GM_COLOR,
            lw=LINEWIDTH,
            zorder=2,
        )
        ax.plot(
            row[icc_col], y, "o",
            color=GM_COLOR,
            ms=MARKER_SIZE,
            zorder=3,
        )

    for _, row in wm.iterrows():
        region = row[COL["subregion"]]
        if region not in y_pos:
            continue
        y = y_pos[region] - DODGE
        ax.plot(
            [row[lo_col], row[hi_col]],
            [y, y],
            color=WM_COLOR,
            lw=LINEWIDTH,
            zorder=2,
        )
        ax.plot(
            row[icc_col], y, "s",
            color=WM_COLOR,
            ms=MARKER_SIZE,
            zorder=3,
        )

    format_axis(ax, region_order, show_yticks)


def draw_subcortical_panel(
    ax,
    data,
    icc_col,
    lo_col,
    hi_col,
    show_yticks=True,
):
    for _, row in data.iterrows():
        region = row[COL["subregion"]]
        if region not in SUB_Y_POS:
            continue
        y = SUB_Y_POS[region]
        ax.plot(
            [row[lo_col], row[hi_col]],
            [y, y],
            color=SUBCORTICAL_COLOR,
            lw=LINEWIDTH,
            zorder=2,
        )
        ax.plot(
            row[icc_col], y, "D",
            color=SUBCORTICAL_COLOR,
            ms=MARKER_SIZE,
            zorder=3,
        )

    labels = [str(region).lower() for region in SUB_REGION_ORDER]
    format_axis(ax, labels, show_yticks)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Optional individual figure for each comparison
# ─────────────────────────────────────────────────────────────────────────────
# def make_single_plot(icc_col, lo_col, hi_col, title, outfile):
#     height_ratios = [N_LOBE_REGIONS, N_PARCEL_REGIONS, N_SUB_REGIONS]
#     row_unit = 0.38
#     fig_height = (
#         max(3, N_LOBE_REGIONS * row_unit)
#         + max(8, N_PARCEL_REGIONS * row_unit)
#         + max(6, N_SUB_REGIONS * row_unit)
#     )
#
#     fig, axes = plt.subplots(
#         3,
#         1,
#         figsize=(10, fig_height),
#         gridspec_kw={"height_ratios": height_ratios, "hspace": 0.2},
#     )
#
#     draw_gm_wm_panel(
#         axes[0], avg_lobe, icc_col, lo_col, hi_col,
#         LOBE_REGION_ORDER, LOBE_Y_POS,
#     )
#     axes[0].set_title(title, fontsize=FONT["title"], fontweight="bold", pad=10)
#     axes[0].tick_params(axis="x", labelbottom=False)
#     axes[0].set_ylabel("Region", fontsize=FONT["ylabel"])
#
#     draw_gm_wm_panel(
#         axes[1], avg_parcel, icc_col, lo_col, hi_col,
#         PARCEL_REGION_ORDER, PARCEL_Y_POS,
#     )
#     axes[1].tick_params(axis="x", labelbottom=False)
#     axes[1].set_ylabel("Region", fontsize=FONT["ylabel"])
#
#     draw_subcortical_panel(axes[2], avg_sub, icc_col, lo_col, hi_col)
#     axes[2].set_xlabel(f"{SHEET_NAME} Consistency ICC", fontsize=FONT["xlabel"])
#     axes[2].set_ylabel("Region", fontsize=FONT["ylabel"])
#
#     gm_patch = mpatches.Patch(color=GM_COLOR, label="Gray Matter")
#     wm_patch = mpatches.Patch(color=WM_COLOR, label="White Matter")
#     sub_patch = mpatches.Patch(color=SUBCORTICAL_COLOR, label="Subcortical")
#     ref_line = plt.Line2D(
#         [0], [0],
#         color="gray",
#         linestyle="--",
#         lw=1.2,
#         label=f"ICC = {REFERENCE_LINE}",
#     )
#
#     fig.legend(
#         handles=[gm_patch, wm_patch, sub_patch, ref_line],
#         loc="upper center",
#         ncol=4,
#         fontsize=FONT["legend"],
#         frameon=False,
#         bbox_to_anchor=(0.5, 0.985),
#     )
#
#     fig.align_ylabels(axes)
#     fig.subplots_adjust(left=0.32, right=0.97, bottom=0.06, top=0.93)
#     fig.savefig(outfile, dpi=150, bbox_inches="tight")
#     plt.close(fig)
#     print(f"Saved: {outfile}")
#
#
# for comparison_name, (icc_col, lo_col, hi_col) in COMPARISONS.items():
#     safe_name = comparison_name.replace(" ", "_").replace("/", "")
#     outfile = OUTPUT_DIR / f"icc_forest_{safe_name}_consistency_{SHEET_NAME}.png"
#     make_single_plot(
#         icc_col,
#         lo_col,
#         hi_col,
#         f"Consistency ICC — {comparison_name}",
#         outfile,
#     )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Combined figure: A = lobes, B = parcels, C = subcortical
# ─────────────────────────────────────────────────────────────────────────────
comparison_items = list(COMPARISONS.items())
n_panels = len(comparison_items)

height_ratios = [N_LOBE_REGIONS, N_PARCEL_REGIONS, N_SUB_REGIONS]
row_unit = 0.38
fig_width = 8 * n_panels
fig_height = (
    max(3, N_LOBE_REGIONS * row_unit)
    + max(8, N_PARCEL_REGIONS * row_unit)
    + max(6, N_SUB_REGIONS * row_unit)
)

fig, axes = plt.subplots(
    3,
    n_panels,
    figsize=(fig_width, fig_height),
    gridspec_kw={"height_ratios": height_ratios, "hspace": 0.2},
    sharey=False,
)

axes = np.asarray(axes)
if axes.ndim == 1:
    axes = axes.reshape(3, 1)

panel_label_font = FONT["title"] + 8

for column_index, (
    comparison_name,
    (icc_col, lo_col, hi_col),
) in enumerate(comparison_items):
    show_yticks = column_index == 0

    ax_lobe = axes[0, column_index]
    ax_parcel = axes[1, column_index]
    ax_sub = axes[2, column_index]

    draw_gm_wm_panel(
        ax_lobe,
        avg_lobe,
        icc_col,
        lo_col,
        hi_col,
        LOBE_REGION_ORDER,
        LOBE_Y_POS,
        show_yticks,
    )
    ax_lobe.set_title(
        comparison_name,
        fontsize=FONT["title"],
        fontweight="bold",
        pad=10,
    )
    ax_lobe.tick_params(axis="x", labelbottom=False)
    if show_yticks:
        ax_lobe.set_ylabel("Region", fontsize=FONT["ylabel"])

    draw_gm_wm_panel(
        ax_parcel,
        avg_parcel,
        icc_col,
        lo_col,
        hi_col,
        PARCEL_REGION_ORDER,
        PARCEL_Y_POS,
        show_yticks,
    )
    ax_parcel.tick_params(axis="x", labelbottom=False)
    if show_yticks:
        ax_parcel.set_ylabel("Region", fontsize=FONT["ylabel"])

    draw_subcortical_panel(
        ax_sub,
        avg_sub,
        icc_col,
        lo_col,
        hi_col,
        show_yticks,
    )
    ax_sub.set_xlabel(
        f"{SHEET_NAME} Consistency ICC",
        fontsize=FONT["xlabel"],
    )
    if show_yticks:
        ax_sub.set_ylabel("Region", fontsize=FONT["ylabel"])

for row_index, panel_label in enumerate(["A", "B", "C"]):
    axes[row_index, 0].text(
        -0.45,
        1.0,
        panel_label,
        transform=axes[row_index, 0].transAxes,
        fontsize=panel_label_font,
        fontweight="bold",
        ha="left",
        va="bottom",
        zorder=10,
        clip_on=False,
    )

gm_patch = mpatches.Patch(color=GM_COLOR, label="Gray Matter")
wm_patch = mpatches.Patch(color=WM_COLOR, label="White Matter")
sub_patch = mpatches.Patch(color=SUBCORTICAL_COLOR, label="Subcortical")
ref_line = plt.Line2D(
    [0], [0],
    color="gray",
    linestyle="--",
    lw=1.2,
    label=f"ICC = {REFERENCE_LINE}",
)

fig.legend(
    handles=[gm_patch, wm_patch, sub_patch, ref_line],
    loc="upper center",
    ncol=4,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(0.5, 0.955),
)

fig.suptitle(
    f"Consistency ICC — All Comparisons — {SHEET_NAME}\n"
    "Cerebrum/Lobes + DK Parcels + Subcortical, Average Rows",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=0.995,
)

fig.align_ylabels(axes[:, 0])
fig.subplots_adjust(left=0.17, right=0.98, bottom=0.04, top=0.91)

combined_out = OUTPUT_DIR / f"icc_forest_combined_consistency_{SHEET_NAME}.png"
fig.savefig(combined_out, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {combined_out}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Print and save summary statistics
# ─────────────────────────────────────────────────────────────────────────────
def compute_icc_stats(data, region_label, icc_col):
    values = data[icc_col].dropna()
    return {
        "Region": region_label,
        "N": len(values),
        "Mean": round(values.mean(), 4) if len(values) else np.nan,
        "Min": round(values.min(), 4) if len(values) else np.nan,
        "Max": round(values.max(), 4) if len(values) else np.nan,
    }


summary_rows = []

for comparison_name, (icc_col, lo_col, hi_col) in COMPARISONS.items():
    gm_parcels = avg_parcel[avg_parcel[COL["region"]].eq("GM")]
    wm_parcels = avg_parcel[avg_parcel[COL["region"]].eq("WM")]
    gm_lobes = avg_lobe[avg_lobe[COL["region"]].eq("GM")]
    wm_lobes = avg_lobe[avg_lobe[COL["region"]].eq("WM")]

    categories = [
        ("GM parcels", gm_parcels),
        ("WM parcels", wm_parcels),
        ("GM cerebrum/lobes", gm_lobes),
        ("WM cerebrum/lobes", wm_lobes),
        ("Subcortical", avg_sub),
    ]

    for category_name, category_data in categories:
        row = compute_icc_stats(
            category_data,
            f"{comparison_name} — {category_name}",
            icc_col,
        )
        row["Comparison"] = comparison_name
        summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)[
    ["Comparison", "Region", "N", "Mean", "Min", "Max"]
]

print("\n── ICC Consistency Summary Statistics ──")
print(summary_df.to_string(index=False))

stats_out = OUTPUT_DIR / f"icc_summary_stats_consistency_{SHEET_NAME}.csv"
summary_df.to_csv(stats_out, index=False)
print(f"\nSaved: {stats_out}")
