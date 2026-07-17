"""
CVw Forest Plot — Desikan-Killiany Atlas, GM & WM
Averaged across hemispheres.

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
from pathlib import Path

# ── File path ─────────────────────────────────────────────────────────────────
EXCEL_PATH = "/Users/nevao/Documents/MPF_Project/results for reproducibiity paper/TablesForPlottingBias.xlsx"
OUTPUT_DIR = Path(".")

DATA_TYPE    = "MPF"                    # "MPF" or "Volume"
METHOD = "(SDw/Mean)"

if DATA_TYPE == "Volume":
    SHEET_NAME    = "Volume-Repeatability CVw"
    MEASURE_LABEL = "CVw (%)"
    FILE_LABEL    = "volume_CVw"
else:
    SHEET_NAME    = "MPF-Repeatability CVw"
    MEASURE_LABEL = "CVw (%)"
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
GM_COLOR          = "#4C72B0"       # blue
WM_COLOR          = "#E07B39"       # orange
SUBCORTICAL_COLOR = "#1A1A1A"       # gray
MARKER_SIZE       = 6
LINEWIDTH         = 1.4
DODGE             = 0.22            # vertical separation between GM and WM markers

# ── Sort order ────────────────────────────────────────────────────────────────
# "gm_cvw"     : sort by average GM cvw across all comparisons
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
# 4. Compute ONE fixed region sort order
# ─────────────────────────────────────────────────────────────────────────────
gm_avg = avg[avg[COL["region"]] == "GM"].copy()
wm_avg = avg[avg[COL["region"]] == "WM"].copy()

cvw_point_cols = [cols[0] for cols in WORKFLOWS.values()]

if SORT_BY == "gm_cvw":
    gm_avg["_sort"] = gm_avg[cvw_point_cols].mean(axis=1)
    ascending = False      # most negative cvw at bottom, least negative at top
elif SORT_BY == "gm_abs_cvw":
    gm_avg["_sort"] = gm_avg[cvw_point_cols].abs().mean(axis=1)
    ascending = False      # smallest magnitude at top
elif SORT_BY == "alphabetical":
    gm_avg["_sort"] = gm_avg[COL["subregion"]]
    ascending = False     # A at top
else:
    raise ValueError(f"Unknown SORT_BY value: '{SORT_BY}'. "
                     "Choose 'gm_cvw', 'gm_abs_cvw', or 'alphabetical'.")

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
    df_sub.groupby([COL["subregion"], COL["region"]])[cvw_cols]
    .mean()
    .reset_index()
)

# ─────────────────────────────────────────────────────────────────────────────
# 5b. Summary statistics — hemisphere-averaged CVw values
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

# ─────────────────────────────────────────────────────────────────────────────
# 6. Core draw function — GM & WM panel
# ─────────────────────────────────────────────────────────────────────────────
def draw_panel(ax, avg_df, cvw_col, lo_col, hi_col, show_yticks=True):
    """
    Draw GM and WM cvw estimates with CIs onto ax.
    X-axis is auto-scaled to the data.
    """
    gm = avg_df[avg_df[COL["region"]] == "GM"]
    wm = avg_df[avg_df[COL["region"]] == "WM"]

    # ── Plot GM ──
    for _, row in gm.iterrows():
        r    = row[COL["subregion"]]
        y    = Y_POS[r] + DODGE
        cvw = row[cvw_col]
        lo   = row[lo_col]
        hi   = row[hi_col]
        color = GM_COLOR
        ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
        ax.plot(cvw, y, "o", color=color, ms=MARKER_SIZE, zorder=3)

    # ── Plot WM ──
    for _, row in wm.iterrows():
        r    = row[COL["subregion"]]
        y    = Y_POS[r] - DODGE
        cvw = row[cvw_col]
        lo   = row[lo_col]
        hi   = row[hi_col]
        color = WM_COLOR
        ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
        ax.plot(cvw, y, "s", color=color, ms=MARKER_SIZE, zorder=3)

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
def draw_subcortical_panel(ax, sub_df, cvw_col, lo_col, hi_col,
                           sub_region_order, show_yticks=True):
    """
    Draw subcortical cvw estimates — single tissue type.
    Significant regions colored, non-significant gray.
    """
    n_sub     = len(sub_region_order)
    y_pos_sub = {r: i for i, r in enumerate(sub_region_order)}

    for _, row in sub_df.iterrows():
        r    = row[COL["subregion"]]
        if r not in y_pos_sub:
            continue
        y    = y_pos_sub[r]
        cvw = row[cvw_col]
        lo   = row[lo_col]
        hi   = row[hi_col]
        color = SUBCORTICAL_COLOR
        ax.plot([lo, hi], [y, y], color=color, lw=LINEWIDTH, zorder=2)
        ax.plot(cvw, y, "D", color=color, ms=MARKER_SIZE, zorder=3)

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
sub_cvw_cols = [cols[0] for cols in WORKFLOWS.values()]
avg_sub_sorted = avg_sub.copy()
avg_sub_sorted["_sort"] = avg_sub_sorted[sub_cvw_cols].mean(axis=1)
SUB_REGION_ORDER = avg_sub_sorted.sort_values("_sort", ascending=False)[COL["subregion"]].tolist()
n_sub_regions    = len(SUB_REGION_ORDER)

# ── Compute shared x limits across all comparisons and tissue types ──
all_lo_cols  = [COL["cvw_lo_1"], COL["cvw_lo_2"], COL["cvw_lo_3"]]
all_hi_cols  = [COL["cvw_hi_1"], COL["cvw_hi_2"], COL["cvw_hi_3"]]
global_min   = min(avg[all_lo_cols].min().min(), avg_sub[all_lo_cols].min().min())
global_max   = max(avg[all_hi_cols].max().max(), avg_sub[all_hi_cols].max().max())
padding      = (global_max - global_min) * 0.05   # 5% padding on each side
X_LIM        = (global_min - padding, global_max + padding)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Combined GM + WM figure — all three workflows side by side
# ─────────────────────────────────────────────────────────────────────────────
comp_items = list(WORKFLOWS.items())
n_panels   = len(comp_items)
fig_height = max(8, N_REGIONS * 0.38)
fig_width  = 8 * n_panels

fig, axes = plt.subplots(
    1, n_panels,
    figsize=(fig_width, fig_height),
    sharey=False,
)

for idx, (comp_name, (cvw_col, lo_col, hi_col)) in enumerate(comp_items):
    ax          = axes[idx]
    show_yticks = (idx == 0)

    draw_panel(ax, avg, cvw_col, lo_col, hi_col, show_yticks=show_yticks)

    ax.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    ax.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)

    if show_yticks:
        ax.set_ylabel("Region", fontsize=FONT["ylabel"])

# ── Shared legend ──
gm_patch  = mpatches.Patch(color=GM_COLOR, label=f"Gray Matter")
wm_patch  = mpatches.Patch(color=WM_COLOR, label=f"White Matter")
ref_line  = plt.Line2D([0], [0], color="gray", linestyle="--",
                       lw=1.2, label="0")

fig.legend(
    handles=[gm_patch, wm_patch, ref_line],
    loc="upper right",
    ncol=3,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(1.0, 0.985),
)

fig.suptitle(
    f"{MEASURE_LABEL} — All Workflows - {SHEET_NAME}\nDK Atlas, Hemispheres Averaged",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=1.01,
)

plt.tight_layout()
combined_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_all_workflows_{SHEET_NAME}.png"
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

for idx, (comp_name, (cvw_col, lo_col, hi_col)) in enumerate(comp_items):
    ax          = axes_sub[idx]
    show_yticks = (idx == 0)

    draw_subcortical_panel(ax, avg_sub, cvw_col, lo_col, hi_col,
                           SUB_REGION_ORDER, show_yticks=show_yticks)

    ax.set_xlabel(MEASURE_LABEL, fontsize=FONT["xlabel"])
    ax.set_title(comp_name, fontsize=FONT["title"], fontweight="bold", pad=10)

    if show_yticks:
        ax.set_ylabel("Subcortical Region", fontsize=FONT["ylabel"])

# ── Shared legend ──
sub_patch    = mpatches.Patch(color=SUBCORTICAL_COLOR, label=f"Subcortical")
ref_line_sub = plt.Line2D([0], [0], color="gray", linestyle="--",
                          lw=1.2, label="0")

fig_sub.legend(
    handles=[sub_patch, ref_line_sub],
    loc="upper right",
    ncol=3,
    fontsize=FONT["legend"],
    frameon=False,
    bbox_to_anchor=(1.0, 0.96),
)

fig_sub.suptitle(
    f"{MEASURE_LABEL} — All Workflows - {SHEET_NAME}\nSubcortical Regions, Hemispheres Averaged",
    fontsize=FONT["title"] + 1,
    fontweight="bold",
    y=1.01,
)

plt.tight_layout()
subcortical_out = OUTPUT_DIR / f"{FILE_LABEL}_forest_subcortical_{SHEET_NAME}.png"
fig_sub.savefig(subcortical_out, dpi=150, bbox_inches="tight")
plt.close(fig_sub)
print(f"Saved: {subcortical_out}")

# ─────────────────────────────────────────────────────────────────────────────
# 11. Print and save summary statistics
# ─────────────────────────────────────────────────────────────────────────────
summary_rows = []

for wfname, (cvw_col, lo_col, hi_col) in WORKFLOWS.items():

    # GM
    gm_data = avg[avg[COL["region"]] == "GM"]
    row = compute_cvw_stats(gm_data, f"{wfname} — GM", cvw_col)
    row["Workflow"] = wfname
    summary_rows.append(row)

    # WM
    wm_data = avg[avg[COL["region"]] == "WM"]
    row = compute_cvw_stats(wm_data, f"{wfname} — WM", cvw_col)
    row["Workflow"] = wfname
    summary_rows.append(row)

    # Subcortical
    row = compute_cvw_stats(avg_sub, f"{wfname} — Subcortical", cvw_col)
    row["Workflow"] = wfname
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)[[
    "Workflow", "Region", "N", "Mean", "SD", "Min", "Max",
]]

print("\n── CVw Summary Statistics ──")
print(summary_df.to_string(index=False))

stats_out = OUTPUT_DIR / f"{FILE_LABEL}_summary_stats_{SHEET_NAME}.csv"
summary_df.to_csv(stats_out, index=False)
print(f"\nSaved: {stats_out}")