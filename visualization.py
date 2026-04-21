import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, FancyArrowPatch
import seaborn as sns
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────
# 1. LOAD & PREPARE DATA  (same as your code)
# ─────────────────────────────────────────
with open('9736.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.json_normalize(data)

columns_needed = [
    'id', 'index', 'period', 'minute', 'second',
    'type.name', 'team.name', 'player.name',
    'position.name', 'location', 'duration'
]
df = df[columns_needed]
df.columns = ['id', 'index', 'period', 'minute', 'second',
              'event_type', 'team', 'player', 'position', 'location', 'duration']

df['player']   = df['player'].fillna('Unknown')
df['position'] = df['position'].fillna('Unknown')
df['duration'] = df['duration'].fillna(0)
df['x'] = df['location'].apply(lambda v: v[0] if isinstance(v, list) else None)
df['y'] = df['location'].apply(lambda v: v[1] if isinstance(v, list) else None)
df = df.drop(columns=['location']).drop_duplicates()
df['total_seconds'] = df['minute'] * 60 + df['second']

# ─────────────────────────────────────────
# 2. FILTER MESSI EVENTS
# ─────────────────────────────────────────
messi = df[df['player'].str.contains('Messi', case=False, na=False)].copy()

messi_passes_raw = [e for e in data
                    if e.get('player', {}).get('id') == 5503
                    and e.get('type', {}).get('name') == 'Pass'
                    and e.get('location')
                    and e.get('pass', {}).get('end_location')]

# Build tidy pass DataFrame
pass_rows = []
for e in messi_passes_raw:
    p = e['pass']
    outcome = p.get('outcome', {}).get('name', 'Complete') if 'outcome' in p else 'Complete'
    pass_rows.append({
        'x':  e['location'][0], 'y':  e['location'][1],
        'ex': p['end_location'][0], 'ey': p['end_location'][1],
        'outcome': outcome
    })
passes_df = pd.DataFrame(pass_rows)


# ─────────────────────────────────────────
# 3. PITCH DRAWING HELPER
#    StatsBomb coords: x 0-120, y 0-80
# ─────────────────────────────────────────
PITCH_COLOR  = '#1a7a3c'
LINE_COLOR   = 'white'
LINE_ALPHA   = 0.85
LINE_WIDTH   = 1.6

def draw_pitch(ax, pitch_color=PITCH_COLOR, line_color=LINE_COLOR,
               line_alpha=LINE_ALPHA, lw=LINE_WIDTH):
    """Draw a full StatsBomb pitch on the given axes."""
    ax.set_facecolor(pitch_color)
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 80)
    ax.set_aspect('equal')
    ax.axis('off')

    kw = dict(color=line_color, linewidth=lw, alpha=line_alpha, zorder=2)

    # Outer boundary
    ax.plot([0,120,120,0,0], [0,0,80,80,0], **kw)
    # Halfway line
    ax.plot([60,60], [0,80], **kw)
    # Centre circle
    ax.add_patch(plt.Circle((60,40), 10, fill=False, **kw))
    ax.plot(60, 40, 'o', color=line_color, ms=2, alpha=line_alpha, zorder=2)

    # Left penalty area
    ax.plot([0,18,18,0], [18,18,62,62], **kw)
    ax.plot([0,6,6,0],   [30,30,50,50], **kw)
    ax.add_patch(Arc((12,40), 20, 20, angle=0,
                     theta1=-53.13, theta2=53.13,
                     color=line_color, lw=lw, alpha=line_alpha, zorder=2))

    # Right penalty area
    ax.plot([120,102,102,120], [18,18,62,62], **kw)
    ax.plot([120,114,114,120], [30,30,50,50], **kw)
    ax.add_patch(Arc((108,40), 20, 20, angle=0,
                     theta1=126.87, theta2=233.13,
                     color=line_color, lw=lw, alpha=line_alpha, zorder=2))

    # Penalty spots
    ax.plot(12,  40, 'o', color=line_color, ms=2.5, alpha=line_alpha, zorder=2)
    ax.plot(108, 40, 'o', color=line_color, ms=2.5, alpha=line_alpha, zorder=2)

    # Goals (behind goal lines)
    ax.plot([0,  -2, -2, 0],  [36,36,44,44], **kw)
    ax.plot([120,122,122,120],[36,36,44,44], **kw)


# ─────────────────────────────────────────
# 4. HEATMAP  (replicates the visualisation)
# ─────────────────────────────────────────
fig_heat, ax_heat = plt.subplots(figsize=(13, 8.5))
fig_heat.patch.set_facecolor('#111111')

draw_pitch(ax_heat)

# Grass stripe effect
for i in range(12):
    ax_heat.add_patch(patches.Rectangle(
        (i*10, 0), 10, 80,
        linewidth=0, edgecolor='none',
        facecolor='white', alpha=0.03 if i % 2 == 0 else 0,
        zorder=1))

# KDE heatmap
heat_data = messi[messi['x'].notna() & messi['y'].notna()]
sns.kdeplot(
    x=heat_data['x'],
    y=heat_data['y'],
    ax=ax_heat,
    fill=True,
    levels=150,
    thresh=0.01,
    cmap='RdYlGn_r',
    bw_adjust=0.28,
    alpha=0.88,
    zorder=3
)

# Zone labels
ax_heat.text(108, 76, 'ATT', color='white', fontsize=9,
             alpha=0.55, ha='center', fontweight='bold')
ax_heat.text(12, 76, 'DEF', color='white', fontsize=9,
             alpha=0.55, ha='center', fontweight='bold')

# Title & stats
fig_heat.text(0.5, 0.97,
              'Lionel Messi — Touch Heatmap',
              ha='center', va='top', fontsize=17,
              color='white', fontweight='bold')
fig_heat.text(0.5, 0.93,
              'Barcelona vs Real Madrid  ·  235 total touches',
              ha='center', va='top', fontsize=11, color='#aaaaaa')

# Colorbar legend
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
sm = ScalarMappable(cmap='RdYlGn_r', norm=Normalize(0, 1))
sm.set_array([])
cbar = fig_heat.colorbar(sm, ax=ax_heat, orientation='vertical',
                          fraction=0.025, pad=0.02, shrink=0.6)
cbar.set_label('Activity density', color='white', fontsize=9)
cbar.ax.yaxis.set_tick_params(color='white')
cbar.set_ticks([0.05, 0.5, 0.95])
cbar.set_ticklabels(['Low', 'Medium', 'High'], color='white')
plt.setp(cbar.ax.get_yticklabels(), color='white')

plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.savefig('messi_heatmap.png', dpi=180, bbox_inches='tight',
            facecolor=fig_heat.get_facecolor())
plt.show()
print("✅  Heatmap saved → messi_heatmap.png")


# ─────────────────────────────────────────
# 5. PASS MAP  (replicates the visualisation)
# ─────────────────────────────────────────
COMPLETE_COLOR   = '#5DCAA5'   # teal
INCOMPLETE_COLOR = '#F0997B'   # coral

fig_pass, ax_pass = plt.subplots(figsize=(13, 8.5))
fig_pass.patch.set_facecolor('#111111')

draw_pitch(ax_pass)

# Grass stripes
for i in range(12):
    ax_pass.add_patch(patches.Rectangle(
        (i*10, 0), 10, 80,
        linewidth=0, edgecolor='none',
        facecolor='white', alpha=0.03 if i % 2 == 0 else 0,
        zorder=1))

complete   = passes_df[passes_df['outcome'] == 'Complete']
incomplete = passes_df[passes_df['outcome'] != 'Complete']

def draw_passes(ax, df_sub, color, dashed=False, alpha=0.70, lw=1.4):
    for _, row in df_sub.iterrows():
        dx = row['ex'] - row['x']
        dy = row['ey'] - row['y']
        linestyle = (0, (5, 3)) if dashed else 'solid'
        ax.annotate(
            '',
            xy=(row['ex'], row['ey']),
            xytext=(row['x'], row['y']),
            arrowprops=dict(
                arrowstyle='->', color=color,
                lw=lw, alpha=alpha,
                linestyle=linestyle,
                connectionstyle='arc3,rad=0.05'
            ),
            zorder=4
        )
    # Draw start dots
    ax.scatter(df_sub['x'], df_sub['y'],
               s=18, color=color, alpha=alpha+0.15,
               zorder=5, linewidths=0)

draw_passes(ax_pass, complete,   COMPLETE_COLOR,   dashed=False)
draw_passes(ax_pass, incomplete, INCOMPLETE_COLOR, dashed=True, alpha=0.85, lw=1.6)

# ── Legend ──
legend_elements = [
    plt.Line2D([0], [0], color=COMPLETE_COLOR,   lw=2,
               label=f'Complete ({len(complete)})'),
    plt.Line2D([0], [0], color=INCOMPLETE_COLOR, lw=2,
               linestyle='--', label=f'Incomplete / Offside ({len(incomplete)})'),
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='white', markersize=6,
               label='Pass origin', linewidth=0)
]
leg = ax_pass.legend(
    handles=legend_elements,
    loc='lower left', fontsize=9,
    facecolor='#1a1a1a', edgecolor='none',
    labelcolor='white', framealpha=0.85
)

# Accuracy box (top-right)
acc = round(len(complete) / len(passes_df) * 100, 1)
ax_pass.text(117, 77,
             f'{acc}%\nAccuracy',
             ha='center', va='top', fontsize=11,
             color='white', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.4',
                       facecolor='#1a1a1a', alpha=0.7,
                       edgecolor='none'))

# Title
fig_pass.text(0.5, 0.97,
              'Lionel Messi — Pass Map',
              ha='center', va='top', fontsize=17,
              color='white', fontweight='bold')
fig_pass.text(0.5, 0.93,
              f'Barcelona vs Real Madrid  ·  {len(passes_df)} passes  ·  {acc}% completion',
              ha='center', va='top', fontsize=11, color='#aaaaaa')

plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.savefig('messi_passmap.png', dpi=180, bbox_inches='tight',
            facecolor=fig_pass.get_facecolor())
plt.show()
print("✅  Pass map saved → messi_passmap.png")