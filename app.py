import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path("workouts.json")

def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def recommend_next_week(weights, reps, target_reps):
    """
    Simple rule:
    - If you hit target reps on ALL working sets: add 2.5%
    - Otherwise: keep the same
    Recommendation is based on the heaviest working set weight.
    """
    working = [(w, r) for w, r in zip(weights, reps) if w > 0]
    if not working:
        return 0.0

    top_weight = max(w for w, _ in working)
    hit_all = all(r >= target_reps for w, r in working)

    if hit_all:
        return round(top_weight * 1.025, 2)
    return round(top_weight, 2)

st.set_page_config(page_title="Workout Tracker", page_icon="💪", layout="centered")
st.title("💪 Workout Tracker")
st.caption("Log sets and get a simple next-week weight recommendation.")

data = load_data()

with st.expander("➕ Log a workout", expanded=True):
    workout_type = st.selectbox("Workout Type", ["Upper", "Lower", "Push", "Pull", "Legs", "Full Body", "Custom"])
    if workout_type == "Custom":
        workout_type = st.text_input("Custom workout type", value="Custom")

    exercise = st.text_input("Exercise (e.g., Bench Press, Squat)", value="")
    target_reps = st.number_input("Target reps per set", min_value=1, max_value=30, value=10)

    num_sets = st.number_input("How many sets?", min_value=1, max_value=10, value=3)

    weights = []
    reps = []

    st.write("### Sets")
    for i in range(int(num_sets)):
        c1, c2 = st.columns(2)
        w = c1.number_input(f"Set {i+1} weight", min_value=0.0, step=2.5, value=0.0, key=f"w{i}")
        r = c2.number_input(f"Set {i+1} reps", min_value=0, max_value=100, value=0, key=f"r{i}")
        weights.append(float(w))
        reps.append(int(r))

    rec = recommend_next_week(weights, reps, int(target_reps))
    st.info(f"Recommended weight next week (based on top working set): **{rec}**")

    if st.button("Save workout"):
        if not exercise.strip():
            st.error("Please enter an exercise name.")
        else:
            data.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "workout_type": workout_type,
                "exercise": exercise.strip(),
                "target_reps": int(target_reps),
                "sets": [{"weight": w, "reps": r} for w, r in zip(weights, reps)],
            })
            save_data(data)
            st.success("Saved!")

st.divider()

st.subheader("📋 Workout History")
if data:
    rows = []
    for entry in data:
        for idx, s in enumerate(entry["sets"], start=1):
            rows.append({
                "Date": entry["date"],
                "Workout": entry["workout_type"],
                "Exercise": entry["exercise"],
                "Set": idx,
                "Weight": s["weight"],
                "Reps": s["reps"],
                "Target Reps": entry["target_reps"],
            })
    df = pd.DataFrame(rows)
    st.dataframe(df.sort_values(["Date", "Exercise", "Set"], ascending=[False, True, True]), use_container_width=True)

    st.subheader("✅ Latest recommendations (per exercise)")
    latest = df.sort_values("Date").groupby("Exercise").tail(1)
    rec_rows = []
    for _, r in latest.iterrows():
        hit = int(r["Reps"]) >= int(r["Target Reps"])
        rec_rows.append({
            "Exercise": r["Exercise"],
            "Last Weight": float(r["Weight"]),
            "Hit Target Reps": bool(hit),
            "Recommended Next Week": round(float(r["Weight"]) * (1.025 if hit else 1.0), 2),
        })
    st.dataframe(pd.DataFrame(rec_rows).sort_values("Exercise"), use_container_width=True)
else:
    st.write("No workouts logged yet. Use the form above to add your first session.")
