import json
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# -----------------------------
# LOAD DATA
# -----------------------------
with open('9736.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.json_normalize(data)

# -----------------------------
# SELECT REQUIRED COLUMNS
# -----------------------------
df = df[[
    'type.name', 'team.name', 'player.name', 'duration'
]]

df.columns = ['event_type', 'team', 'player', 'duration']

# -----------------------------
# CLEAN DATA
# -----------------------------
df['player'] = df['player'].fillna('Unknown')
df['duration'] = df['duration'].fillna(0)

# -----------------------------
# MATCH STATISTICS
# -----------------------------

print("\n========= MATCH STATISTICS =========\n")

# 1. Total Events
print("📊 Total Events per Team:")
print(df['team'].value_counts())

# 2. Possession (% approximation)
possession = (df['team'].value_counts(normalize=True) * 100)
print("\n⚽ Possession (%):")
print(possession)

# 3. Passes
passes = df[df['event_type'] == 'Pass']
print("\n🔁 Total Passes:")
print(passes['team'].value_counts())

# 4. Shots
shots = df[df['event_type'] == 'Shot']
print("\n🎯 Total Shots:")
print(shots['team'].value_counts())

# 5. Carries
carries = df[df['event_type'] == 'Carry']
print("\n🏃 Carries:")
print(carries['team'].value_counts())

# 6. Duels
duels = df[df['event_type'] == 'Duel']
print("\n🤼 Duels:")
print(duels['team'].value_counts())

# 7. Top Players (Overall)
print("\n⭐ Top 10 Players (Overall Events):")
print(df['player'].value_counts().head(10))

# 8. Top Passers
print("\n🔥 Top 10 Players (Passes):")
print(passes['player'].value_counts().head(10))

# 9. Average Duration per Team
print("\n⏱ Average Event Duration:")
print(df.groupby('team')['duration'].mean())

print("\n========= END =========")