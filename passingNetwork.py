import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc
import matplotlib.patheffects as pe

# (IMPORTANT) REMOVE this line if present:
# matplotlib.use('Agg')

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
with open('9736.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ─────────────────────────────────────────
# PASS DATA
# ─────────────────────────────────────────
records = []
for e in data:
    if (e.get('type', {}).get('name') == 'Pass'
            and e.get('player')
            and e.get('pass', {}).get('recipient')
            and e.get('location')):

        outcome = e['pass'].get('outcome', {}).get('name', 'Complete') if 'outcome' in e['pass'] else 'Complete'

        if outcome == 'Complete':
            records.append({
                'team': e['team']['name'],
                'passer': e['player']['name'],
                'recipient': e['pass']['recipient']['name'],
            })

df_pass = pd.DataFrame(records)

# ─────────────────────────────────────────
# PLAYER POSITIONS
# ─────────────────────────────────────────
pos_data = {}

for e in data:
    if e.get('player') and e.get('location') and e.get('team'):
        key = (e['team']['name'], e['player']['name'])
        pos_data.setdefault(key, []).append(e['location'])

avg_pos = {
    k: (np.mean([l[0] for l in v]), np.mean([l[1] for l in v]))
    for k, v in pos_data.items() if len(v) >= 5
}

touch_count = {k: len(v) for k, v in pos_data.items()}

# ─────────────────────────────────────────
# SIMPLE NETWORK VISUALIZATION (CLEAN VERSION)
# ─────────────────────────────────────────
def draw_pitch(ax):
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 80)
    ax.set_facecolor('#1a7a3c')
    ax.axis('off')

def draw_network(ax, team_name, color):
    players = [k[1] for k in avg_pos if k[0] == team_name]

    # Draw nodes
    for (team, player), (x, y) in avg_pos.items():
        if team == team_name:
            ax.scatter(x, y, s=200, color=color, edgecolors='white')
            ax.text(x, y, player.split()[-1], color='white', ha='center')

    # Draw edges
    sub = df_pass[df_pass['team'] == team_name]
    edges = sub.groupby(['passer', 'recipient']).size().reset_index(name='count')

    for _, row in edges.iterrows():
        if row['passer'] in players and row['recipient'] in players:
            p1 = (team_name, row['passer'])
            p2 = (team_name, row['recipient'])

            if p1 in avg_pos and p2 in avg_pos:
                x1, y1 = avg_pos[p1]
                x2, y2 = avg_pos[p2]

                ax.plot([x1, x2], [y1, y2],
                        color=color,
                        linewidth=row['count'] * 0.2,
                        alpha=0.5)

# ─────────────────────────────────────────
# PLOT
# ─────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

draw_pitch(axes[0])
draw_pitch(axes[1])

draw_network(axes[0], 'Barcelona', '#A50044')
draw_network(axes[1], 'Real Madrid', '#002B7F')

axes[0].set_title("Barcelona Passing Network", color='white')
axes[1].set_title("Real Madrid Passing Network", color='white')

plt.tight_layout()

# ─────────────────────────────────────────
# SAVE + SHOW
# ─────────────────────────────────────────
plt.savefig("passing_networks.png", dpi=300)

# Safe print (no emoji ❌)
print("Saved -> passing_networks.png")

plt.show()