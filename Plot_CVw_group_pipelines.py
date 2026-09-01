"""
CVw Forest Plot — RMS repeatability across imaging workflows.

"""

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = Path(
    "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/"
    "final paper data/TablesForPlottingBiasWithAvg.xlsx"
)
OUTPUT_DIR = Path(
    "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/"
    "final paper figures"
)

DATA_TYPE = "Volume"  # "MPF" or "Volume"

if DATA_TYPE.casefold() == "volume":
    DATA_TYPE = "Volume"
    SHEET_NAME = "Volume-Repeatability CVw"
    MEASURE_LABEL = "Volume CVw (%)"
    FILE_LABEL = "volume_CVw"
elif DATA_TYPE.casefold() == "mpf":
    DATA_TYPE = "MPF"
    SHEET_NAME = "MPF-Repeatability CVw"
    MEASURE_LABEL = "MPF CVw (%)"
    FILE_LABEL = "mpf_CVw"
else:
    raise ValueError('DATA_TYPE must be either "MPF" or "Volume".')

# ── Column name map ───────────────────────────────────────────────────────────
COL = {
    "region": "Region",
    "subregion": "Subregion",
    "side": "Side",
    "cvw_1": "CVw (RMS) MPF",
    "cvw_lo_1": "Lower_CI MPF",
    "cvw_hi_1": "Upper_CI MPF",
    "cvw_2": "CVw (RMS) MPFreg",
    "cvw_lo_2": "Lower_CI MPFreg",
    "cvw_hi_2": "Upper_CI MPFreg",
    "cvw_3": "CVw (RMS) MPRAGE",
    "cvw_lo_3": "Lower_CI MPRAGE",
    "cvw_hi_3": "Upper_CI MPRAGE",
    "pval_mpf_mpfreg": "AdjP_CVw(RMS)_MPFvMPFreg",
    "pval_mpf_mprage": "AdjP_CVw(RMS)_MPFvMPRAGE",
    "pval_mpfreg_mprage": "AdjP_CVw(RMS)_MPFregvMPRAGE",
}

REFERENCE_LINE = 0.0
MARKER_SIZE = 6
LINEWIDTH = 1.4
ALPHA_THRESHOLD = 0.05
SORT_BY = "gm_cvw"  # "gm_cvw", "gm_abs_cvw", or "alphabetical"

METHOD_COLORS = {
    "MPF": "#4C72B0",
    "MPFreg": "#DD8452",
    "MPRAGE": "#55A868",
}
METHOD_MARKERS = {"MPF": "o", "MPFreg": "s", "MPRAGE": "D"}

ROW_HEIGHT = 0.8
DODGE_STEP = ROW_HEIGHT / 4
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

FONT = {
    "title": 15,
    "xlabel": 17,
    "ylabel": 17,
    "xtick": 17,
    "ytick": 17,
    "ytick_long": 17,
    "legend": 17,
    "panel_letter": 18,
}

# All y-tick labels use the same size. These values leave enough room for
# long labels while keeping the three plot columns relatively close together.
COLUMN_SPACE = 0.62
VERTICAL_PANEL_SPACE = 0.24
FIGURE_WIDTH_PER_COLUMN = 9.0
Y_LABEL_PAD_POINTS = 12
PANEL_LETTER_Y_PAD = 0.006

WORKFLOWS = {
    "MPF": (COL["cvw_1"], COL["cvw_lo_1"], COL["cvw_hi_1"]),
    "MPFreg": (COL["cvw_2"], COL["cvw_lo_2"], COL["cvw_hi_2"]),
    "MPRAGE": (COL["cvw_3"], COL["cvw_lo_3"], COL["cvw_hi_3"]),
}

NUMERIC_COLS = [
    COL["cvw_1"], COL["cvw_lo_1"], COL["cvw_hi_1"],
    COL["cvw_2"], COL["cvw_lo_2"], COL["cvw_hi_2"],
    COL["cvw_3"], COL["cvw_lo_3"], COL["cvw_hi_3"],
    COL["pval_mpf_mpfreg"], COL["pval_mpf_mprage"],
    COL["pval_mpfreg_mprage"],
]

REQUIRED_COLS = list(dict.fromkeys([
    COL["region"], COL["subregion"], COL["side"], *NUMERIC_COLS
]))


def clean_text(series):
    """Normalize spreadsheet text, including nonbreaking and repeated spaces."""
    return (
        series.fillna("")
        .astype(str)
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def canonical_region(series):
    """Map common tissue-label variants to the three internal panel names."""
    normalized = (
        clean_text(series)
        .str.casefold()
        .str.replace(r"[^a-z0-9]+", " ", regex=True)
        .str.strip()
    )

    aliases = {
        "gm": "GM",
        "gray": "GM",
        "grey": "GM",
        "gray matter": "GM",
        "grey matter": "GM",
        "cortical gray matter": "GM",
        "cortical grey matter": "GM",
        "wm": "WM",
        "white": "WM",
        "white matter": "WM",
        "subcortical": "Subcortical",
        "sub cortical": "Subcortical",
        "subcortex": "Subcortical",
    }
    return normalized.map(aliases).fillna("")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load and prepare data
# ─────────────────────────────────────────────────────────────────────────────
if not EXCEL_PATH.exists():
    raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
df_raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df_raw.columns = clean_text(pd.Series(df_raw.columns)).tolist()

missing_cols = [col for col in REQUIRED_COLS if col not in df_raw.columns]
if missing_cols:
    raise KeyError(
        f'Missing required columns in sheet "{SHEET_NAME}": {missing_cols}\n'
        f"Available columns: {df_raw.columns.tolist()}"
    )

side_clean = clean_text(df_raw[COL["side"]]).str.casefold()
df = df_raw[side_clean.eq("average")].copy()

if df.empty:
    observed_sides = sorted(clean_text(df_raw[COL["side"]]).drop_duplicates().tolist())
    raise ValueError(
        f'No rows with {COL["side"]} == "Average" were found in '
        f'"{SHEET_NAME}". Observed Side values: {observed_sides}'
    )

for col in NUMERIC_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Save original labels for diagnostics, then canonicalize panel labels.
df["_original_region"] = clean_text(df[COL["region"]])
df[COL["region"]] = canonical_region(df[COL["region"]])
df[COL["subregion"]] = (
    clean_text(df[COL["subregion"]])
    .str.replace(r"(?i)_(gm|wm)$", "", regex=True)
    .str.strip()
)

unrecognized = sorted(
    df.loc[df[COL["region"]].eq(""), "_original_region"].drop_duplicates().tolist()
)
if unrecognized:
    print(f"Warning: ignored unrecognized Region labels: {unrecognized}")

df = df[
    df[COL["region"]].isin(["GM", "WM", "Subcortical"])
    & df[COL["subregion"]].ne("")
].copy()

gm_data = df[df[COL["region"]].eq("GM")].copy()
wm_data = df[df[COL["region"]].eq("WM")].copy()
sub_data = df[df[COL["region"]].eq("Subcortical")].copy()

print(f'Loaded sheet: "{SHEET_NAME}"')
print(f"Average rows retained: {len(df)}")
print(
    "Panel row counts — "
    f"GM: {len(gm_data)}, WM: {len(wm_data)}, Subcortical: {len(sub_data)}"
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Region ordering and GM/WM subpanel division
# ─────────────────────────────────────────────────────────────────────────────
cvw_point_cols = [cols[0] for cols in WORKFLOWS.values()]

# Labels accepted in the compact upper GM/WM panel. Matching ignores spaces,
# underscores, hyphens, capitalization, and an optional terminal "lobe".
SUMMARY_REGION_KEYS = {
    "cerebrum": 0,
    "frontal": 1,
    "parietal": 2,
    "occipital": 3,
    "temporal": 4,
}


def normalized_region_key(value):
    """Return a compact key used to recognize cerebrum and lobe labels."""
    key = "".join(ch for ch in str(value).casefold() if ch.isalnum())
    if key.endswith("lobe"):
        key = key[:-4]
    return key


def split_summary_and_parcels(tissue_df):
    """Split one cortical tissue dataframe into summary and parcel rows."""
    if tissue_df.empty:
        return tissue_df.copy(), tissue_df.copy()

    is_summary = tissue_df[COL["subregion"]].map(
        lambda value: normalized_region_key(value) in SUMMARY_REGION_KEYS
    )
    return tissue_df[is_summary].copy(), tissue_df[~is_summary].copy()


def compute_region_order(tissue_df):
    """Return unique region labels in the requested plot order."""
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
        d["_sort"] = d[COL["subregion"]].str.casefold()
        ascending = True
    else:
        raise ValueError(f"Unknown SORT_BY value: {SORT_BY!r}")

    ordered = d.sort_values("_sort", ascending=ascending, na_position="last")
    return ordered[COL["subregion"]].drop_duplicates().tolist()


def compute_summary_order(tissue_df):
    """Order cerebrum first, followed by frontal through temporal lobes."""
    labels = tissue_df[COL["subregion"]].drop_duplicates().tolist()
    return sorted(
        labels,
        key=lambda label: (
            SUMMARY_REGION_KEYS.get(normalized_region_key(label), 999),
            str(label).casefold(),
        ),
    )


def align_wm_order(gm_order, wm_df):
    """Use matching GM parcel order first, then append WM-only labels."""
    wm_labels = wm_df[COL["subregion"]].drop_duplicates().tolist()
    aligned = [label for label in gm_order if label in wm_labels]
    aligned.extend(label for label in wm_labels if label not in aligned)
    return aligned


gm_summary_data, gm_parcel_data = split_summary_and_parcels(gm_data)
wm_summary_data, wm_parcel_data = split_summary_and_parcels(wm_data)

GM_SUMMARY_ORDER = compute_summary_order(gm_summary_data)
GM_PARCEL_ORDER = compute_region_order(gm_parcel_data)

WM_SUMMARY_ORDER = compute_summary_order(wm_summary_data)
WM_PARCEL_ORDER = align_wm_order(GM_PARCEL_ORDER, wm_parcel_data)
SUB_REGION_ORDER = compute_region_order(sub_data)

if not gm_data.empty and not GM_SUMMARY_ORDER:
    print(
        "Warning: no GM cerebrum/lobe rows were recognized. "
        "Expected labels such as Cerebrum, Frontal, Parietal, Occipital, "
        "or Temporal."
    )
if not wm_data.empty and not WM_SUMMARY_ORDER:
    print(
        "Warning: no WM cerebrum/lobe rows were recognized. "
        "Expected labels such as Cerebrum, Frontal, Parietal, Occipital, "
        "or Temporal."
    )

print(
    "Subpanel row counts — "
    f"GM summary: {len(GM_SUMMARY_ORDER)}, GM parcels: {len(GM_PARCEL_ORDER)}, "
    f"WM summary: {len(WM_SUMMARY_ORDER)}, WM parcels: {len(WM_PARCEL_ORDER)}"
)

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
def draw_grouped_panel(
    ax,
    tissue_df,
    region_order,
    lowercase_labels=False,
    ytick_fontsize=None,
):
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
    ax.tick_params(
        axis="y",
        labelsize=ytick_fontsize or FONT["ytick"],
        pad=4,
    )
    ax.set_ylim(-0.5, n_regions - 0.5)

    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Figure-level label helpers and shared legend
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


def tick_label_left_x(fig, ax):
    """Return the left edge of the visible y-tick labels in figure units."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [
        label.get_window_extent(renderer=renderer)
        for label in ax.get_yticklabels()
        if label.get_visible() and label.get_text()
    ]
    if not boxes:
        return ax.get_position().x0
    return min(fig.transFigure.inverted().transform(box.get_points())[0, 0] for box in boxes)


def get_tick_label_column_center_x(fig, ax):
    """Return the horizontal center of an axis's y-tick-label column."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [
        label.get_window_extent(renderer=renderer)
        for label in ax.get_yticklabels()
        if label.get_visible() and label.get_text()
    ]
    if not boxes:
        return ax.get_position().x0

    left = min(
        fig.transFigure.inverted().transform(box.get_points())[0, 0]
        for box in boxes
    )
    right = max(
        fig.transFigure.inverted().transform(box.get_points())[1, 0]
        for box in boxes
    )
    return (left + right) / 2


def add_aligned_row_ylabels(fig, upper_ax, lower_ax):
    """Add two Region labels at exactly the same figure-level x coordinate."""
    fig.canvas.draw()
    fig_width_inches = fig.get_size_inches()[0]
    pad_fraction = (Y_LABEL_PAD_POINTS / 72) / fig_width_inches
    shared_x = min(
        tick_label_left_x(fig, upper_ax),
        tick_label_left_x(fig, lower_ax),
    ) - pad_fraction

    for ax in (upper_ax, lower_ax):
        bbox = ax.get_position()
        fig.text(
            shared_x,
            (bbox.y0 + bbox.y1) / 2,
            "Region",
            rotation=90,
            va="center",
            ha="right",
            fontsize=FONT["ylabel"],
        )
    return shared_x


def add_panel_letter(fig, ax, letter, x_coordinate):
    """Place a panel letter above a y-label or y-tick-label column."""
    bbox = ax.get_position()
    fig.text(
        x_coordinate,
        bbox.y1 + PANEL_LETTER_Y_PAD,
        letter,
        fontsize=FONT["panel_letter"],
        fontweight="bold",
        ha="center",
        va="bottom",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Combined figure
# ─────────────────────────────────────────────────────────────────────────────
INCLUDE_WM_PANEL = DATA_TYPE != "Volume"

cortical_panel_defs = [
    (gm_data, GM_SUMMARY_ORDER, GM_PARCEL_ORDER, "Gray Matter")
]
if INCLUDE_WM_PANEL:
    cortical_panel_defs.append(
        (wm_data, WM_SUMMARY_ORDER, WM_PARCEL_ORDER, "White Matter")
    )

if not SUB_REGION_ORDER:
    raise ValueError("No non-empty Subcortical panel is available to plot.")
if not any(summary or parcels for _, summary, parcels, _ in cortical_panel_defs):
    raise ValueError("No non-empty GM or WM subpanels are available to plot.")

summary_row_count = max(
    [len(summary) for _, summary, _, _ in cortical_panel_defs] + [1]
)
parcel_row_count = max(
    [len(parcels) for _, _, parcels, _ in cortical_panel_defs]
    + [len(SUB_REGION_ORDER), 1]
)
panel_height_ratios = [max(summary_row_count, 1), max(parcel_row_count, 1)]

n_main_cols = len(cortical_panel_defs) + 1
fig_width = FIGURE_WIDTH_PER_COLUMN * n_main_cols
fig_height = max(10, (summary_row_count + parcel_row_count) * 0.42)

fig = plt.figure(figsize=(fig_width, fig_height))
outer_grid = fig.add_gridspec(
    1,
    n_main_cols,
    wspace=COLUMN_SPACE,
)

first_column_axes = None

for col_idx, (tissue_df, summary_order, parcel_order, tissue_name) in enumerate(
    cortical_panel_defs
):
    inner_grid = outer_grid[0, col_idx].subgridspec(
        2,
        1,
        height_ratios=panel_height_ratios,
        hspace=VERTICAL_PANEL_SPACE,
    )
    ax_summary = fig.add_subplot(inner_grid[0, 0])
    ax_parcels = fig.add_subplot(inner_grid[1, 0])

    draw_grouped_panel(
        ax_summary,
        tissue_df,
        summary_order,
        ytick_fontsize=FONT["ytick"],
    )
    draw_grouped_panel(
        ax_parcels,
        tissue_df,
        parcel_order,
        ytick_fontsize=FONT["ytick_long"],
    )

    # Repeat the tissue title and measurement label on both panels. The
    # larger inter-row gap and compact title/label padding prevent the upper
    # x-axis label from overlapping the lower panel title.
    for ax in (ax_summary, ax_parcels):
        ax.set_title(
            tissue_name,
            fontsize=FONT["title"],
            fontweight="bold",
            pad=6,
        )
        ax.set_xlabel(
            MEASURE_LABEL,
            fontsize=FONT["xlabel"],
            labelpad=3,
        )

    if col_idx == 0:
        # The shared Region labels and row letters are added at figure level
        # after the layout is finalized.
        first_column_axes = (ax_summary, ax_parcels)

# Center the single subcortical plot vertically in the rightmost column for
# both MPF and Volume rather than aligning it with either cortical row.
total_height_units = sum(panel_height_ratios)
sub_height_units = min(len(SUB_REGION_ORDER), total_height_units)
spacer_units = max((total_height_units - sub_height_units) / 2, 0.01)

sub_grid = outer_grid[0, -1].subgridspec(
    3,
    1,
    height_ratios=[spacer_units, sub_height_units, spacer_units],
    hspace=0,
)
ax_sub = fig.add_subplot(sub_grid[1, 0])

draw_grouped_panel(
    ax_sub,
    sub_data,
    SUB_REGION_ORDER,
    lowercase_labels=True,
    ytick_fontsize=FONT["ytick_long"],
)
ax_sub.set_title(
    "Subcortical",
    fontsize=FONT["title"],
    fontweight="bold",
    pad=10,
)
ax_sub.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])

# Finalize the axes positions before placing figure-level labels and measuring
# tick-label extents.
fig.subplots_adjust(top=0.90, bottom=0.08)

if first_column_axes is not None:
    region_label_x = add_aligned_row_ylabels(fig, *first_column_axes)
    add_panel_letter(fig, first_column_axes[0], "A", region_label_x)
    add_panel_letter(fig, first_column_axes[1], "B", region_label_x)

# Center C above the subcortical tick-label column rather than placing it
# immediately to the left of the plotting axis.
subcortical_tick_column_x = get_tick_label_column_center_x(fig, ax_sub)
add_panel_letter(fig, ax_sub, "C", subcortical_tick_column_x)

# Center the workflow legend at the top of the rightmost column. Because
# panel C is vertically centered, the legend occupies the open space above it.
right_column_bbox = outer_grid[0, -1].get_position(fig)
fig.legend(
    handles=method_legend_handles(),
    loc="upper center",
    bbox_to_anchor=(
        (right_column_bbox.x0 + right_column_bbox.x1) / 2,
        right_column_bbox.y1,
    ),
    bbox_transform=fig.transFigure,
    ncol=len(WORKFLOWS),
    fontsize=FONT["legend"],
    frameon=False,
)

fig.suptitle(
    f"{DATA_TYPE} CVw by Workflow ({SHEET_NAME})",
    fontsize=FONT["title"] + 2,
    fontweight="bold",
    y=0.995,
)

fig.text(
    0.01,
    0.015,
    (
        f"*  MPF vs MPFreg, adj.p < {ALPHA_THRESHOLD}     "
        f"†  MPF vs MPRAGE, adj.p < {ALPHA_THRESHOLD}     "
        f"‡  MPFreg vs MPRAGE, adj.p < {ALPHA_THRESHOLD}"
    ),
    fontsize=FONT["legend"] - 1,
    va="bottom",
)

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
