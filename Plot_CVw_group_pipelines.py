"""
CVw Forest Plot — RMS repeatability across imaging workflows.

This program reads repeatability results for MPF or Volume from an Excel
worksheet and creates a combined forest plot for Gray Matter, White Matter,
and Subcortical regions.

Only rows where Side is "Average" are used. The Region column assigns each
row to the GM, WM, or Subcortical panel, and the Subregion column supplies
the plotted region name. Subregion names may include tissue suffixes such as
frontal_gm or frontal_wm; the terminal _gm or _wm is removed from the
displayed label because the panel title identifies the tissue type.

For each region, the plot displays RMS CVw estimates and confidence intervals
for the MPF, MPFreg, and MPRAGE workflows. Symbols indicate statistically
significant adjusted pairwise comparisons:
    *  MPF vs MPFreg
    †  MPF vs MPRAGE
    ‡  MPFreg vs MPRAGE

The White Matter panel is omitted for Volume. The program saves the combined
forest plot as a PNG file, prints summary statistics, and saves those
statistics as a CSV file.

Expected spreadsheet columns:
    Region
    Subregion
    Side
    CVw (RMS) MPF
    CVw (RMS) MPFreg
    CVw (RMS) MPRAGE
    Lower_CI MPF / MPFreg / MPRAGE
    Upper_CI MPF / MPFreg / MPRAGE
    AdjP_CVw(RMS)_MPFvMPFreg
    AdjP_CVw(RMS)_MPFvMPRAGE
    AdjP_CVw(RMS)_MPFregvMPRAGE
"""

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper data/TablesForPlottingBiasWithAvg.xlsx"
OUTPUT_DIR = Path("/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/final paper figures")

DATA_TYPE = "MPF"  # "MPF" or "Volume"

if DATA_TYPE == "Volume":
    SHEET_NAME = "Volume-Repeatability CVw"
    MEASURE_LABEL = "Volume CVw (%)"
    FILE_LABEL = "volume_CVw"
else:
    SHEET_NAME = "MPF-Repeatability CVw"
    MEASURE_LABEL = "MPF CVw (%)"
    FILE_LABEL = "mpf_CVw"

# ── Column name map ───────────────────────────────────────────────────────────
COL = {
    "region": "Region",
    "subregion": "Subregion",
    "side": "Side",

    # RMS CVw only
    "cvw_1": "CVw (RMS) MPF",
    "cvw_lo_1": "Lower_CI MPF",
    "cvw_hi_1": "Upper_CI MPF",

    "cvw_2": "CVw (RMS) MPFreg",
    "cvw_lo_2": "Lower_CI MPFreg",
    "cvw_hi_2": "Upper_CI MPFreg",

    "cvw_3": "CVw (RMS) MPRAGE",
    "cvw_lo_3": "Lower_CI MPRAGE",
    "cvw_hi_3": "Upper_CI MPRAGE",

    # Pairwise significance: adjusted p-values for RMS CVw
    "pval_mpf_mpfreg": "AdjP_CVw(RMS)_MPFvMPFreg",
    "pval_mpf_mprage": "AdjP_CVw(RMS)_MPFvMPRAGE",
    "pval_mpfreg_mprage": "AdjP_CVw(RMS)_MPFregvMPRAGE",
}

# ── Plotting options ──────────────────────────────────────────────────────────
REFERENCE_LINE = 0.0
MARKER_SIZE = 6
LINEWIDTH = 1.4
ALPHA_THRESHOLD = 0.05

METHOD_COLORS = {
    "MPF": "#4C72B0",
    "MPFreg": "#DD8452",
    "MPRAGE": "#55A868",
}
METHOD_MARKERS = {
    "MPF": "o",
    "MPFreg": "s",
    "MPRAGE": "D",
}

N_METHODS = 3
ROW_HEIGHT = 0.8
DODGE_STEP = ROW_HEIGHT / (N_METHODS + 1)
METHOD_OFFSETS = {
    "MPF": DODGE_STEP,
    "MPFreg": 0.0,
    "MPRAGE": -DODGE_STEP,
}

PAIR_DEFS = [
    ("MPF", "MPFreg", "pval_mpf_mpfreg", "*"),
    ("MPF", "MPRAGE", "pval_mpf_mprage", "†"),
    ("MPFreg", "MPRAGE", "pval_mpfreg_mprage", "‡"),
]

# "gm_cvw", "gm_abs_cvw", or "alphabetical"
SORT_BY = "gm_cvw"

FONT = {
    "title": 15,
    "xlabel": 17,
    "ylabel": 17,
    "xtick": 17,
    "ytick": 17,
    "legend": 17,
}

WORKFLOWS = {
    "MPF": (COL["cvw_1"], COL["cvw_lo_1"], COL["cvw_hi_1"]),
    "MPFreg": (COL["cvw_2"], COL["cvw_lo_2"], COL["cvw_hi_2"]),
    "MPRAGE": (COL["cvw_3"], COL["cvw_lo_3"], COL["cvw_hi_3"]),
}

NUMERIC_COLS = [
    COL["cvw_1"], COL["cvw_lo_1"], COL["cvw_hi_1"],
    COL["cvw_2"], COL["cvw_lo_2"], COL["cvw_hi_2"],
    COL["cvw_3"], COL["cvw_lo_3"], COL["cvw_hi_3"],
    COL["pval_mpf_mpfreg"],
    COL["pval_mpf_mprage"],
    COL["pval_mpfreg_mprage"],
]


def clean_text(series):
    """Return trimmed strings while preserving missing values as empty strings."""
    return series.fillna("").astype(str).str.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load and prepare data
# ─────────────────────────────────────────────────────────────────────────────
df_raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)

# Use only the spreadsheet's precomputed bilateral Average rows.
df = df_raw[
    clean_text(df_raw[COL["side"]]).str.casefold().eq("average")
].copy()

if df.empty:
    raise ValueError(
        f'No rows with {COL["side"]} == "Average" were found in sheet "{SHEET_NAME}".'
    )

for col in NUMERIC_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Region determines the panel. Subregion supplies the plotted label.
# Remove a terminal _gm or _wm because the panel title identifies the tissue.
df[COL["region"]] = clean_text(df[COL["region"]])
df[COL["subregion"]] = (
    clean_text(df[COL["subregion"]])
    .str.replace(r"(?i)_(gm|wm)$", "", regex=True)
)

df = df[
    df[COL["region"]].isin(["GM", "WM", "Subcortical"])
    & df[COL["subregion"]].ne("")
].copy()

gm_data = df[df[COL["region"]] == "GM"].copy()
wm_data = df[df[COL["region"]] == "WM"].copy()
sub_data = df[df[COL["region"]] == "Subcortical"].copy()

# ─────────────────────────────────────────────────────────────────────────────
# 2. Region ordering
# ─────────────────────────────────────────────────────────────────────────────
cvw_point_cols = [cols[0] for cols in WORKFLOWS.values()]


def compute_region_order(tissue_df):
    """Return region labels in the requested plot order."""
    if tissue_df.empty:
        return []

    d = tissue_df.copy()

    if SORT_BY == "gm_cvw":
        d["_sort"] = d[cvw_point_cols].mean(axis=1)
        ascending = False
    elif SORT_BY == "gm_abs_cvw":
        d["_sort"] = d[cvw_point_cols].abs().mean(axis=1)
        ascending = False
    elif SORT_BY == "alphabetical":
        d["_sort"] = d[COL["subregion"]].str.lower()
        ascending = True
    else:
        raise ValueError(f"Unknown SORT_BY value: {SORT_BY!r}")

    order = (
        d.sort_values("_sort", ascending=ascending, na_position="last")
        [COL["subregion"]]
        .tolist()
    )

    cerebrum_labels = [r for r in order if str(r).casefold() == "cerebrum"]
    order = [r for r in order if str(r).casefold() != "cerebrum"]
    order.extend(cerebrum_labels)
    return order


GM_REGION_ORDER = compute_region_order(gm_data)

# Use the GM ordering for matching WM labels, then append WM-only labels.
wm_labels = wm_data[COL["subregion"]].tolist()
WM_REGION_ORDER = [r for r in GM_REGION_ORDER if r in wm_labels]
WM_REGION_ORDER.extend(r for r in wm_labels if r not in WM_REGION_ORDER)

SUB_REGION_ORDER = compute_region_order(sub_data)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Shared x-axis limits
# ─────────────────────────────────────────────────────────────────────────────
all_lo_cols = [COL["cvw_lo_1"], COL["cvw_lo_2"], COL["cvw_lo_3"]]
all_hi_cols = [COL["cvw_hi_1"], COL["cvw_hi_2"], COL["cvw_hi_3"]]

plot_groups = [gm_data, sub_data]
if DATA_TYPE != "Volume":
    plot_groups.append(wm_data)
plot_groups = [group for group in plot_groups if not group.empty]

if not plot_groups:
    raise ValueError("No recognized GM, WM, or Subcortical Average rows are available to plot.")

global_min = min(group[all_lo_cols].min().min() for group in plot_groups)
global_max = max(group[all_hi_cols].max().max() for group in plot_groups)

if pd.isna(global_min) or pd.isna(global_max):
    raise ValueError("The plotted confidence-interval columns contain no numeric values.")

data_range = global_max - global_min
if data_range == 0:
    data_range = max(abs(global_min), 1.0)

padding = data_range * 0.05
SYMBOL_COL_FRAC = 0.90
X_LIM = (global_min - padding, global_max + data_range * 0.20)
SYMBOL_COL_X = global_min + (X_LIM[1] - global_min) * SYMBOL_COL_FRAC

# ─────────────────────────────────────────────────────────────────────────────
# 4. Core panel-drawing function
# ─────────────────────────────────────────────────────────────────────────────
def draw_grouped_panel(ax, tissue_df, region_order, lowercase_labels=False):
    """Draw all workflows and significance symbols for one tissue panel."""
    n_regions = len(region_order)
    y_pos = {region: i for i, region in enumerate(region_order)}

    for wf_name, (cvw_col, lo_col, hi_col) in WORKFLOWS.items():
        color = METHOD_COLORS[wf_name]
        marker = METHOD_MARKERS[wf_name]
        offset = METHOD_OFFSETS[wf_name]

        for _, row in tissue_df.iterrows():
            region = row[COL["subregion"]]
            if region not in y_pos:
                continue

            cvw = row[cvw_col]
            lo = row[lo_col]
            hi = row[hi_col]
            y = y_pos[region] + offset

            if pd.notna(lo) and pd.notna(hi):
                ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
            if pd.notna(cvw):
                ax.plot(
                    cvw,
                    y,
                    marker=marker,
                    color=color,
                    ms=MARKER_SIZE,
                    linestyle="none",
                    zorder=3,
                )

    ax.axvline(REFERENCE_LINE, color="gray", linestyle="--", lw=1.2, zorder=1)

    for i in range(n_regions):
        if i % 2 == 0:
            ax.axhspan(
                i - ROW_HEIGHT / 2,
                i + ROW_HEIGHT / 2,
                color="whitesmoke",
                zorder=0,
            )

    for _, row in tissue_df.iterrows():
        region = row[COL["subregion"]]
        if region not in y_pos:
            continue

        symbols = []
        for _, _, pval_key, symbol in PAIR_DEFS:
            pval = row[COL[pval_key]]
            if pd.notna(pval) and pval < ALPHA_THRESHOLD:
                symbols.append(symbol)

        if symbols:
            ax.text(
                SYMBOL_COL_X,
                y_pos[region],
                " ".join(symbols),
                fontsize=FONT["ytick"] - 4,
                color="black",
                va="center",
                ha="center",
                fontweight="bold",
                zorder=5,
            )

    display_labels = (
        [str(region).lower() for region in region_order]
        if lowercase_labels
        else region_order
    )
    ax.set_yticks(range(n_regions))
    ax.set_yticklabels(display_labels)
    ax.tick_params(axis="y", labelsize=FONT["ytick"])
    ax.set_ylim(-0.5, n_regions - 0.5)

    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Shared legend
# ─────────────────────────────────────────────────────────────────────────────
def method_legend_handles():
    """Create one legend entry for each workflow."""
    return [
        mlines.Line2D(
            [],
            [],
            color=METHOD_COLORS[wf_name],
            marker=METHOD_MARKERS[wf_name],
            linestyle="-",
            markersize=MARKER_SIZE,
            label=wf_name,
        )
        for wf_name in WORKFLOWS
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 6. Combined figure
# ─────────────────────────────────────────────────────────────────────────────
INCLUDE_WM_PANEL = DATA_TYPE != "Volume"

if INCLUDE_WM_PANEL:
    panel_defs = [
        (gm_data, GM_REGION_ORDER, "Gray Matter", "Region", False),
        (wm_data, WM_REGION_ORDER, "White Matter", "Region", False),
        (sub_data, SUB_REGION_ORDER, "Subcortical", "Subcortical Region", True),
    ]
else:
    panel_defs = [
        (gm_data, GM_REGION_ORDER, "Gray Matter", "Region", False),
        (sub_data, SUB_REGION_ORDER, "Subcortical", "Subcortical Region", True),
    ]

panel_defs = [panel for panel in panel_defs if panel[1]]
if not panel_defs:
    raise ValueError("No non-empty tissue panels are available to plot.")

n_cols = len(panel_defs)
max_regions = max(len(order) for _, order, _, _, _ in panel_defs)
fig_height = max(8, max_regions * 0.42)
fig_width = 26 * n_cols / 3

fig, axes = plt.subplots(1, n_cols, figsize=(fig_width, fig_height), sharey=False)
if n_cols == 1:
    axes = [axes]

for i, (ax, panel) in enumerate(zip(axes, panel_defs)):
    tissue_df, region_order, panel_title, ylabel, lowercase = panel
    draw_grouped_panel(ax, tissue_df, region_order, lowercase_labels=lowercase)
    ax.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    ax.set_title(panel_title, fontsize=FONT["title"], fontweight="bold", pad=10)

    if i == 0:
        ax.set_ylabel(ylabel, fontsize=FONT["ylabel"])

fig.legend(
    handles=method_legend_handles(),
    loc="upper center",
    bbox_to_anchor=(0.5, 0.96),
    ncol=len(WORKFLOWS),
    fontsize=FONT["legend"],
    frameon=False,
)

fig.suptitle(
    f"{DATA_TYPE} CVw by Workflow ({SHEET_NAME})",
    fontsize=FONT["title"] + 2,
    fontweight="bold",
    y=1.08,
)

fig.text(
    0.01,
    -0.01,
    (
        f"*  MPF vs MPFreg, adj.p < {ALPHA_THRESHOLD}     "
        f"†  MPF vs MPRAGE, adj.p < {ALPHA_THRESHOLD}     "
        f"‡  MPFreg vs MPRAGE, adj.p < {ALPHA_THRESHOLD}"
    ),
    fontsize=FONT["legend"] - 1,
    va="top",
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
combined_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_combined_grouped_{SHEET_NAME}.png"
fig.savefig(combined_out, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {combined_out}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Summary statistics
# ─────────────────────────────────────────────────────────────────────────────
def compute_cvw_stats(df_in, region_label, cvw_col):
    """Calculate descriptive statistics for one workflow and tissue group."""
    vals = df_in[cvw_col].dropna()
    return {
        "Region": region_label,
        "N": len(vals),
        "Mean": round(vals.mean(), 4) if not vals.empty else np.nan,
        "SD": round(vals.std(), 4) if not vals.empty else np.nan,
        "Min": round(vals.min(), 4) if not vals.empty else np.nan,
        "Max": round(vals.max(), 4) if not vals.empty else np.nan,
    }


summary_rows = []
summary_groups = [
    ("GM", gm_data),
    ("Subcortical", sub_data),
]
if INCLUDE_WM_PANEL:
    summary_groups.insert(1, ("WM", wm_data))

for wf_name, (cvw_col, _, _) in WORKFLOWS.items():
    for tissue_name, tissue_df in summary_groups:
        row = compute_cvw_stats(
            tissue_df,
            f"{wf_name} — {tissue_name}",
            cvw_col,
        )
        row["Workflow"] = wf_name
        summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)[
    ["Workflow", "Region", "N", "Mean", "SD", "Min", "Max"]
]

print("\n── CVw Summary Statistics ──")
print(summary_df.to_string(index=False))

stats_out = OUTPUT_DIR / f"{FILE_LABEL}_summary_stats_{SHEET_NAME}.csv"
summary_df.to_csv(stats_out, index=False)
print(f"\nSaved: {stats_out}")
