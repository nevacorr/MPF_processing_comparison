"""
CVw Forest Plot — Desikan-Killiany Atlas, GM & WM
Averaged across hemispheres.

Layout: ONE panel per tissue type (GM, WM, Subcortical).
Within each panel, every region shows all three workflows dodged
vertically, so a reader can directly compare CVw and CIs across
methods for the same region.

Inputs:
    Excel spreadsheet with columns:
        Region          : "GM", "WM", or "Subcortical"
        Subregion       : DK atlas region name
        Side            : "Left" or "Right"

        For each workflow (MPF, MPFreg, MPRAGE):
            CVw                     : CVw
            Lower_CI                : lower CI
            Upper_CI                : upper CI

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from pathlib import Path

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/TablesForPlottingBias.xlsx"
OUTPUT_DIR = Path(".")

DATA_TYPE    = ("Volume")                    # "MPF" or "Volume"
METHOD = "(SDw/Mean)"

if DATA_TYPE == "Volume":
    SHEET_NAME    = "Volume-Repeatability CVw"
    MEASURE_LABEL = "Volume CVw (%)"
    FILE_LABEL    = "volume_CVw"
else:
    SHEET_NAME    = "MPF-Repeatability CVw"
    MEASURE_LABEL = "MPF CVw (%)"
    FILE_LABEL    = "mpf_CVw"

# ── Column name map ───────────────────────────────────────────────────────────

COL = {
    "region"    : "Region",
    "subregion" : "Subregion",
    "side"      : "Side",

    # ── MPF ──────────────────────────────────────────────────────
    "cvw_1"    : f"CVw {METHOD} MPF",
    "cvw_lo_1" : "Lower CI MPF",
    "cvw_hi_1" : "Upper CI MPF",

    # ── MPFreg ───────────────────────────────────────────────────
    "cvw_2"    : f"CVw {METHOD} MPFreg",
    "cvw_lo_2" : "Lower CI MPFreg",
    "cvw_hi_2" : "Upper CI MPFreg",

    # ── MPRAGE ───────────────────────────────────────────────────
    "cvw_3"    : f"CVw {METHOD} MPRAGE",
    "cvw_lo_3" : "Lower CI MPRAGE",
    "cvw_hi_3" : "Upper CI MPRAGE",
}

# ── Plotting options ───────────────────────────────────────────────────────────
REFERENCE_LINE    = 0.0
MARKER_SIZE       = 6
LINEWIDTH         = 1.4

# Method colors — one consistent color per workflow, used across all panels
METHOD_COLORS = {
    "MPF"   : "#4C72B0",   # blue
    "MPFreg": "#DD8452",   # orange
    "MPRAGE": "#55A868",   # green
}
METHOD_MARKERS = {
    "MPF"   : "o",
    "MPFreg": "s",
    "MPRAGE": "D",
}

# Vertical offsets for the three dodged rows within each region
N_METHODS   = 3
ROW_HEIGHT  = 0.8                          # total vertical space per region
DODGE_STEP  = ROW_HEIGHT / (N_METHODS + 1)
# offsets so methods are symmetric around the region's y position, in order
METHOD_OFFSETS = {
    "MPF"   :  DODGE_STEP,
    "MPFreg":  0.0,
    "MPRAGE": -DODGE_STEP,
}

# ── Sort order ────────────────────────────────────────────────────────────────
# "gm_cvw"     : sort by average GM cvw across all workflows
# "gm_abs_cvw" : sort by average absolute GM cvw (magnitude, ignores direction)
# "alphabetical": A–Z by region name
SORT_BY = "gm_cvw"

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

cvw_cols = [v for k, v in COL.items() if k not in ("region", "subregion", "side")]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Average Left and Right hemispheres for each Subregion × Region
# ─────────────────────────────────────────────────────────────────────────────
avg = (
    df.groupby([COL["subregion"], COL["region"]])[cvw_cols]
    .mean()
    .reset_index()
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Workflows dictionary
# ─────────────────────────────────────────────────────────────────────────────
WORKFLOWS = {
    "MPF"   : (COL["cvw_1"], COL["cvw_lo_1"], COL["cvw_hi_1"]),
    "MPFreg": (COL["cvw_2"], COL["cvw_lo_2"], COL["cvw_hi_2"]),
    "MPRAGE": (COL["cvw_3"], COL["cvw_lo_3"], COL["cvw_hi_3"]),
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Region sort order — computed separately for GM and WM
#    (each tissue type gets its own panel, so each gets its own order)
# ─────────────────────────────────────────────────────────────────────────────
cvw_point_cols = [cols[0] for cols in WORKFLOWS.values()]

def compute_region_order(tissue_df):
    d = tissue_df.copy()
    if SORT_BY == "gm_cvw":
        d["_sort"] = d[cvw_point_cols].mean(axis=1)
        ascending = False
    elif SORT_BY == "gm_abs_cvw":
        d["_sort"] = d[cvw_point_cols].abs().mean(axis=1)
        ascending = False
    elif SORT_BY == "alphabetical":
        d["_sort"] = d[COL["subregion"]]
        ascending = False
    else:
        raise ValueError(f"Unknown SORT_BY value: '{SORT_BY}'.")
    order = d.sort_values("_sort", ascending=ascending)[COL["subregion"]].tolist()
    if "cerebrum" in order:
        order.remove("cerebrum")
        order.append("cerebrum")
    return order

gm_avg = avg[avg[COL["region"]] == "GM"].copy()
wm_avg = avg[avg[COL["region"]] == "WM"].copy()

# GM determines the shared order; any WM-only regions get appended at the end
GM_REGION_ORDER = compute_region_order(gm_avg)

wm_only = [r for r in wm_avg[COL["subregion"]].tolist() if r not in GM_REGION_ORDER]
WM_REGION_ORDER = GM_REGION_ORDER + wm_only

# ─────────────────────────────────────────────────────────────────────────────
# 5. Subcortical data — averaged across hemispheres
# ─────────────────────────────────────────────────────────────────────────────
df_sub = df_raw[df_raw[COL["region"]] == "Subcortical"].copy()

avg_sub = (
    df_sub.groupby([COL["subregion"], COL["region"]])[cvw_cols]
    .mean()
    .reset_index()
)
SUB_REGION_ORDER = compute_region_order(avg_sub)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Shared x-axis limits across all panels
# ─────────────────────────────────────────────────────────────────────────────
all_lo_cols = [COL["cvw_lo_1"], COL["cvw_lo_2"], COL["cvw_lo_3"]]
all_hi_cols = [COL["cvw_hi_1"], COL["cvw_hi_2"], COL["cvw_hi_3"]]
global_min  = min(avg[all_lo_cols].min().min(), avg_sub[all_lo_cols].min().min())
global_max  = max(avg[all_hi_cols].max().max(), avg_sub[all_hi_cols].max().max())
padding     = (global_max - global_min) * 0.05
X_LIM       = (global_min - padding, global_max + padding)

# ─────────────────────────────────────────────────────────────────────────────
# 7. Core draw function — single tissue type, all methods dodged per region
# ─────────────────────────────────────────────────────────────────────────────
def draw_grouped_panel(ax, tissue_df, region_order, lowercase_labels=False):
    """
    Draw all three workflows, dodged vertically, for every region in
    region_order, onto a single axis.
    """
    n_regions = len(region_order)
    y_pos = {r: i for i, r in enumerate(region_order)}

    for wf_name, (cvw_col, lo_col, hi_col) in WORKFLOWS.items():
        color  = METHOD_COLORS[wf_name]
        marker = METHOD_MARKERS[wf_name]
        offset = METHOD_OFFSETS[wf_name]

        for _, row in tissue_df.iterrows():
            r = row[COL["subregion"]]
            if r not in y_pos:
                continue
            y   = y_pos[r] + offset
            cvw = row[cvw_col]
            lo  = row[lo_col]
            hi  = row[hi_col]
            ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
            ax.plot(cvw, y, marker=marker, color=color, ms=MARKER_SIZE, zorder=3)

    # ── Reference line ──
    ax.axvline(REFERENCE_LINE, color="gray", linestyle="--", lw=1.2, zorder=1)

    # ── Alternating row shading (one band per region, spanning all 3 methods) ──
    for i in range(n_regions):
        if i % 2 == 0:
            ax.axhspan(i - ROW_HEIGHT / 2, i + ROW_HEIGHT / 2,
                       color="whitesmoke", zorder=0)

    # ── Y-axis ──
    display_labels = [r.lower() for r in region_order] if lowercase_labels else region_order
    ax.set_yticks(range(n_regions))
    ax.set_yticklabels(display_labels)
    ax.tick_params(axis="y", labelsize=FONT["ytick"])
    ax.set_ylim(-0.5, n_regions - 0.5)

    # ── X-axis ──
    ax.set_xlim(X_LIM)
    ax.tick_params(axis="x", labelsize=FONT["xtick"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Shared legend handles (method = color/marker, used across all figures)
# ─────────────────────────────────────────────────────────────────────────────
def method_legend_handles():
    handles = []
    for wf_name in WORKFLOWS:
        handles.append(
            mlines.Line2D([], [], color=METHOD_COLORS[wf_name],
                          marker=METHOD_MARKERS[wf_name], linestyle="-",
                          markersize=MARKER_SIZE, label=wf_name)
        )
    return handles


# ─────────────────────────────────────────────────────────────────────────────
# 9. Combined figure — GM, (WM if applicable), Subcortical
#    Volume: WM subpanel is omitted (1 row x 2 columns)
#    MPF:    all three panels shown (1 row x 3 columns)
# ─────────────────────────────────────────────────────────────────────────────
INCLUDE_WM_PANEL = (DATA_TYPE != "Volume")

if INCLUDE_WM_PANEL:
    panel_defs = [
        (gm_avg,  GM_REGION_ORDER,  "Gray Matter",  "Region",            False),
        (wm_avg,  WM_REGION_ORDER,  "White Matter", "Region",            False),
        (avg_sub, SUB_REGION_ORDER, "Subcortical",  "Subcortical Region", True),
    ]
else:
    panel_defs = [
        (gm_avg,  GM_REGION_ORDER,  "Gray Matter", "Region",            False),
        (avg_sub, SUB_REGION_ORDER, "Subcortical", "Subcortical Region", True),
    ]

n_cols        = len(panel_defs)
max_regions   = max(len(order) for _, order, _, _, _ in panel_defs)
fig_height    = max(8, max_regions * 0.42)
fig_width     = 26 * n_cols / 3   # keep per-panel width consistent with the 3-panel layout

fig, axes = plt.subplots(1, n_cols, figsize=(fig_width, fig_height), sharey=False)
if n_cols == 1:
    axes = [axes]

for i, (ax, (tissue_df, region_order, panel_title, ylabel, lowercase)) in enumerate(zip(axes, panel_defs)):
    draw_grouped_panel(ax, tissue_df, region_order, lowercase_labels=lowercase)
    ax.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    ax.set_title(panel_title, fontsize=FONT["title"], fontweight="bold", pad=10)

    if i == 0:
        ax.set_ylabel(ylabel, fontsize=FONT["ylabel"])

    if i == n_cols - 1:
        ax.legend(handles=method_legend_handles(), loc="upper right",
                  fontsize=FONT["legend"], frameon=False)

fig.suptitle(
    f"{DATA_TYPE} CVw by Workflow ({SHEET_NAME})",
    fontsize=FONT["title"] + 2,
    fontweight="bold",
    y=1.02,
)

plt.tight_layout()
combined_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_combined_grouped_{SHEET_NAME}.png"
fig.savefig(combined_out, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {combined_out}")



# ─────────────────────────────────────────────────────────────────────────────
# 12. Summary statistics
# ─────────────────────────────────────────────────────────────────────────────
def compute_cvw_stats(df_in, region_label, cvw_col):
    vals = df_in[cvw_col]
    return {
        "Region": region_label,
        "N": len(vals),
        "Mean": round(vals.mean(), 4) if len(vals) > 0 else np.nan,
        "SD": round(vals.std(), 4) if len(vals) > 0 else np.nan,
        "Min": round(vals.min(), 4) if len(vals) > 0 else np.nan,
        "Max": round(vals.max(), 4) if len(vals) > 0 else np.nan,
    }

summary_rows = []
for wfname, (cvw_col, lo_col, hi_col) in WORKFLOWS.items():
    row = compute_cvw_stats(gm_avg, f"{wfname} — GM", cvw_col)
    row["Workflow"] = wfname
    summary_rows.append(row)

    row = compute_cvw_stats(wm_avg, f"{wfname} — WM", cvw_col)
    row["Workflow"] = wfname
    summary_rows.append(row)

    row = compute_cvw_stats(avg_sub, f"{wfname} — Subcortical", cvw_col)
    row["Workflow"] = wfname
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)[["Workflow", "Region", "N", "Mean", "SD", "Min", "Max"]]

print("\n── CVw Summary Statistics ──")
print(summary_df.to_string(index=False))

stats_out = OUTPUT_DIR / f"{FILE_LABEL}_summary_stats_{SHEET_NAME}.csv"
summary_df.to_csv(stats_out, index=False)
print(f"\nSaved: {stats_out}")