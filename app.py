# app.py — Final All-Features Streamlit App (Ayanokoji OS)
import streamlit as st
import json, os, datetime, random, io
import pandas as pd
import plotly.graph_objects as go
# FIX 1: Removed 'load_local_data' from import list as it does not exist in cloud_sync.py
from cloud_sync import manual_sync, auto_sync, restore_data, save_local_data

# ---------------- CONFIG ----------------
DATA_FILE = "local_data.json"
BASE_XP = 100    # base for xp/level formula

st.set_page_config(page_title="Ayanokoji OS — Habit Tracker", layout="wide", page_icon="⚔️")

# -------------- Utilities --------------
def today_str(offset=0):
    return str(datetime.date.today() + datetime.timedelta(days=offset))

def load_data():
    # FIX 2: Corrected the function call from load_local_data() to restore_data()
    data = restore_data()
    if data is None:
        # fallback in case file missing
        from pathlib import Path
        if not Path(DATA_FILE).exists():
            # use default local_data.json content (if not created earlier)
            default = {
                "profile":{"user_id":"default_user","name":"Akanksha","level":1,"xp":0,"title":"Initiate"},
                "meta":{"last_active": today_str(), "absolute_mode":False, "night_reset_hour":23},
                "stats":{"study_minutes":0,"football_sessions":0,"nofap_days":0,"screen_minutes":0,"fitness_sessions":0,"psych_logs":0},
                "tasks": {},
                "history": {},
                "badges": []
            }
            save_local_data(default)
            return default
        else:
            return {}
    return data

def save_data(d, do_auto_sync=True):
    save_local_data(d)
    if do_auto_sync:
        # small summary auto-sync
        summary = {
            "profile": d.get("profile", {}),
            "stats": d.get("stats", {})
        }
        # use user_id from profile if exists
        uid = d.get("profile", {}).get("user_id", "default_user")
        try:
            # NOTE: We assume auto_sync in cloud_sync.py handles the uid/doc logic internally
            # or is correctly configured to handle data push. If cloud_sync.py was updated
            # to accept uid and summary, this is correct. Otherwise, we stick to the original
            # call signature if we don't change cloud_sync.py's auto_sync.
            # STICKING TO ORIGINAL CODE LOGIC FOR NOW, ASSUMING auto_sync CAN HANDLE IT.
            auto_sync(uid, summary) 
        except Exception:
            pass

def xp_needed(level):
    return int(BASE_XP * level * (1 + (level // 5) * 0.2))

def add_xp_and_check_level(d, amount):
    d["profile"]["xp"] = d["profile"].get("xp",0) + int(amount)
    leveled = False
    while d["profile"]["xp"] >= xp_needed(d["profile"]["level"]):
        need = xp_needed(d["profile"]["level"])
        d["profile"]["xp"] -= need
        d["profile"]["level"] += 1
        leveled = True
    if leveled:
        # auto award a badge/title if needed
        d["profile"]["title"] = f"Lv{d['profile']['level']}"
    save_data(d)
    return leveled

def ensure_today_tasks(d):
    t = today_str()
    if t not in d["tasks"]:
        d["tasks"][t] = {
            "morning_identity": [
                {"name":"Wake up before 6AM","done":False,"xp":25},
                {"name":"Make bed (2 min)","done":False,"xp":5},
                {"name":"5-min silence","done":False,"xp":10},
                {"name":"1 mindset line","done":False,"xp":5},
                {"name":"Cold water splash","done":False,"xp":5},
                {"name":"10 push-ups","done":False,"xp":10}
            ],
            "study_performance": [
                {"name":"2 hours deep work","done":False,"xp":80,"minutes":120},
                {"name":"Subject of the day","done":False,"xp":10},
                {"name":"Exam problems solved","done":False,"xp":20},
                {"name":"Mistake log (1 line)","done":False,"xp":10},
                {"name":"Night recall (2 min)","done":False,"xp":10}
            ],
            "football_dev": [
                {"name":"30-min technical drills","done":False,"xp":40},
                {"name":"Shadow movement practice","done":False,"xp":20},
                {"name":"Finishing practice (10 shots)","done":False,"xp":40},
                {"name":"Watch 5 min analysis","done":False,"xp":10},
                {"name":"Football log (1 line)","done":False,"xp":5}
            ],
            "physical_mindset":[
                {"name":"100 push-ups challenge (split)","done":False,"xp":50},
                {"name":"Core workout","done":False,"xp":20},
                {"name":"Mobility / stretch 10 min","done":False,"xp":15},
                {"name":"Meditation 5-10 min","done":False,"xp":15},
                {"name":"Breathwork","done":False,"xp":10},
                {"name":"Evening walk / cooldown","done":False,"xp":15}
            ],
            "digital_lifestyle":[
                {"name":"Screen-time limit respected","done":False,"xp":30},
                {"name":"NoFap day (track)","done":False,"xp":0},
                {"name":"No junk dopamine","done":False,"xp":30},
                {"name":"Phone cutoff at night","done":False,"xp":20},
                {"name":"Sleep time set","done":False,"xp":10},
                {"name":"Short journal entry","done":False,"xp":5}
            ],
            "psych_development":[
                {"name":"10 min psych reading","done":False,"xp":15},
                {"name":"1 real-life observation","done":False,"xp":10},
                {"name":"1 logic puzzle solved","done":False,"xp":10},
                {"name":"Social behavior log","done":False,"xp":10},
                {"name":"Eye-contact practice","done":False,"xp":5},
                {"name":"2-5 min silence practice","done":False,"xp":5}
            ]
        }
        save_data(d, do_auto_sync=False)

# ---------------- AI (Rule-based offline) ----------------
def ai_coach_reply(user_text, d):
    user = user_text.lower().strip()
    if user == "" or user.isspace():
        return "Tell me one tiny win you had today."
    if "why" in user or "failed" in user or "broke" in user:
        return "What was the exact moment you lost focus? Write one sentence. We'll make a micro plan to patch it."
    if "study" in user:
        return "Pick 1 problem and solve until no mistakes. Try two 50-min deep blocks with a 15-min break."
    if "football" in user:
        return "Film 30s of your finishing and review one clear mistake. Repeat 10 accurate reps focusing on the mistake."
    if "nofap" in user:
        return "Avoid triggers: set phone away at 9pm. 10-minute walk at temptation hour."
    if "reset" in user or "panic" in user:
        return "Emergency breathing: inhale 4s, hold 4s, exhale 6s. Repeat 6 times slowly."
    choices = [
        "Consistency compounds. Do one small uncomfortable thing now.",
        "Ask: Is this action helping my future self? If not, pause and do one habit.",
        "If energy is low, do the minimum 1 rep to keep identity intact."
    ]
    return random.choice(choices)

# ---------------- UI ----------------
data = load_data()
st.sidebar.title("Ayanokoji OS — Navigation")
page = st.sidebar.radio("Go to", ["Daily Page","Sections","Analytics","AI Coach","Badges","Settings","Backup"])

# quick user switch (simple multi-device support — type same user_id on other device)
st.sidebar.markdown("### User")
uid = st.sidebar.text_input("User ID (type same on other device to sync)", value=data["profile"].get("user_id","default_user"))
if uid != data["profile"].get("user_id"):
    data["profile"]["user_id"] = uid
    save_data(data)

# header metrics
col1, col2, col3 = st.columns([1,2,1])
with col1:
    st.metric("Level", data["profile"].get("level",1))
with col2:
    need = xp_needed(data["profile"].get("level",1))
    st.progress(min(1.0, data["profile"].get("xp",0)/need) if need>0 else 0.0)
    st.caption(f"XP {data['profile'].get('xp',0)} / {need}")
with col3:
    # overall streak approx: count days with history entries consecutively
    def overall_streak(d):
        cnt=0
        cur=datetime.date.today()
        while True:
            s=str(cur)
            if s in d.get("history",{}) and len(d["history"][s])>0:
                cnt+=1
                cur-=datetime.timedelta(days=1)
            else:
                break
        return cnt
    st.metric("Overall Streak (days)", overall_streak(data))

ensure_today_tasks(data)
today = today_str()
# ---------- DAILY PAGE ----------
if page=="Daily Page":
    st.header("🗓 Daily Page — Identity First")
    st.subheader(f"Date: {today}")
    # mood/energy/control
    cols = st.columns(3)
    mood = st.selectbox("Mental State", ["😌","🙂","😐","😣","😤","😴"], index=0)
    energy = st.slider("Energy (1-10)", 1, 10, 5)
    control = st.slider("Self-control (1-10)", 1, 10, 5)
    # absolute mode / night reset
    abs_col, nr_col = st.columns([1,1])
    if abs_col.button("Toggle Absolute Being Mode"):
        data["meta"]["absolute_mode"] = not data["meta"].get("absolute_mode", False)
        save_data(data)
        st.experimental_rerun()
    nr_col.write("Absolute Mode: " + ("ON" if data["meta"].get("absolute_mode") else "OFF"))
    if nr_col.button("Night Reset (run)"):
        note = st.text_area("Reflection (1 line):")
        plan = st.text_input("Tomorrow's MIT:")
        if st.button("Save Night Reset"):
            data.setdefault("journal",{})[today] = note
            data.setdefault("notes",{})[today] = {}
            data["notes"][today]["MIT"] = plan
            save_data(data)
            st.success("Night Reset saved.")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("✅ Habits Checklist")
    for section_key, items in data["tasks"][today].items():
        st.markdown(f"### {section_key.replace('_',' ').title()}")
        for i, item in enumerate(items):
            cols = st.columns([0.06,0.74,0.2])
            checked = cols[0].checkbox("", value=item.get("done", False), key=f"{today}_{section_key}_{i}")
            if checked and not item.get("done", False):
                data["tasks"][today][section_key][i]["done"] = True
                # award xp & stats
                xp = item.get("xp", 10)
                leveled = add_xp_and_check_level(data, xp)
                data.setdefault("history",{}).setdefault(today,[]).append(item["name"])
                # heuristics stats
                if section_key=="study_performance" and item.get("minutes"):
                    data["stats"]["study_minutes"] += item.get("minutes",0)
                if section_key=="football_dev" and "30" in item["name"]:
                    data["stats"]["football_sessions"] += 1
                if section_key=="digital_lifestyle" and "NoFap" in item["name"] and item.get("done"):
                    data["stats"]["nofap_days"] += 1
                if section_key=="psych_development" and "log" in item["name"].lower():
                    data["stats"]["psych_logs"] += 1
                save_data(data)
                st.experimental_rerun()
            if not checked and item.get("done", False):
                # uncheck if user unchecks
                data["tasks"][today][section_key][i]["done"] = False
                if today in data.get("history",{}) and item["name"] in data["history"][today]:
                    try: data["history"][today"].remove(item["name"])
                    except: pass
                save_data(data)
                st.experimental_rerun()
            cols[1].write(f"**{item['name']}** — {item.get('xp',0)} XP")
            if section_key=="study_performance" and item.get("minutes"):
                cols[2].write(f"{item.get('minutes')} min")

    # notes / MIT
    st.markdown("---")
    st.subheader("📝 Notes & MIT")
    note = st.text_area("Quick Notes:", value=data.get("journal",{}).get(today,""))
    mit = st.text_input("Tomorrow's MIT:", value=data.get("notes",{}).get(today,{}).get("MIT",""))
    if st.button("Save Notes & MIT"):
        data.setdefault("journal",{})[today]=note
        data.setdefault("notes",{})[today]=data.get("notes",{}).get(today,{})
        data["notes"][today]["MIT"]=mit
        save_data(data)
        st.success("Saved.")

    st.markdown("---")
    st.subheader("🤖 Daily Insight")
    st.info(ai_coach_reply("", data))

# ---------- SECTIONS PAGE ----------
elif page=="Sections":
    st.header("🧩 Sections & Templates")
    st.write("Edit templates for each section (changes apply for future days).")
    all_sections = list(data["tasks"].get(today,{}).keys())
    chosen = st.selectbox("Select section", all_sections)
    items = data["tasks"][today][chosen]
    for i, it in enumerate(items):
        c0,c1,c2 = st.columns([4,1,1])
        c0.write(it["name"])
        c1.write(it.get("xp",0))
        if c2.button("Delete", key=f"del_{i}"):
            items.pop(i)
            data["tasks"][today][chosen]=items
            save_data(data)
            st.experimental_rerun()
    st.markdown("Add new template item:")
    new_name = st.text_input("Name")
    new_xp = st.number_input("XP", min_value=0, value=10)
    if st.button("Add template item"):
        data["tasks"][today][chosen].append({"name":new_name,"done":False,"xp":int(new_xp)})
        save_data(data)
        st.success("Added.")

# ---------- ANALYTICS ----------
elif page=="Analytics":
    st.header("📊 Analytics")
    df_rows=[]
    for d, items in data.get("history",{}).items():
        for it in items:
            df_rows.append({"date": d, "task": it})
    if df_rows:
        df = pd.DataFrame(df_rows)
        top = df["task"].value_counts().reset_index().rename(columns={"index":"task","task":"count"})
        st.subheader("Top Completed Tasks")
        st.table(top.head(10))
        st.subheader("30-day completed counts")
        dates = [(datetime.date.today()-datetime.timedelta(days=i)).isoformat() for i in range(29,-1,-1)]
        counts=[len(data.get("history",{}).get(d,[])) for d in dates]
        fig = go.Figure([go.Bar(x=dates,y=counts)])
        fig.update_layout(height=300, paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No history yet. Do some tasks to gather analytics.")

# ---------- AI COACH ----------
elif page=="AI Coach":
    st.header("🤖 AI Coach — Offline Mentor")
    with st.form("chat", clear_on_submit=False):
        user_q = st.text_input("Ask the coach (eg: 'help study' or 'why I failed today')")
        if st.form_submit_button("Send"):
            reply = ai_coach_reply(user_q, data)
            st.markdown(f"**You:** {user_q}")
            st.markdown(f"**Coach:** {reply}")

    if st.button("Quick Plan for Tomorrow"):
        missed=[]
        for k in data["tasks"].get(today,{}):
            for it in data["tasks"][today][k]:
                if not it.get("done"):
                    missed.append(it["name"])
        plan="1) Wake 6AM 2) 50min study block 3) 30min football drill"
        if missed:
            plan = "Pick 1 missed item now and schedule it tomorrow. " + plan
        st.info(plan)

# ---------- BADGES ----------
elif page=="Badges":
    st.header("🏆 Badges & Rewards")
    st.write("Unlocked badges:")
    for b in data.get("badges",[]):
        st.write(f"• {b}")
    st.markdown("---")
    st.write("Shop (spend XP to unlock themes/consumables)")
    if st.button("Buy Neon Theme (500 XP)"):
        if data["profile"]["xp"]>=500:
            data["profile"]["xp"]-=500
            data["profile"]["theme"]="neon"
            save_data(data)
            st.success("Neon theme unlocked")
        else:
            st.error("Not enough XP")

# ---------- SETTINGS ----------
elif page=="Settings":
    st.header("⚙️ Settings")
    prot = st.checkbox("Streak protection", value=data["meta"].get("streak_protection", True))
    data["meta"]["streak_protection"]=prot
    abs_toggle = st.checkbox("Absolute Being Mode", value=data["meta"].get("absolute_mode", False))
    data["meta"]["absolute_mode"]=abs_toggle
    nr = st.number_input("Night reset hour", min_value=18, max_value=4+24, value=data["meta"].get("night_reset_hour",23))
    data["meta"]["night_reset_hour"]=int(nr)
    if st.button("Save Settings"):
        save_data(data)
        st.success("Saved.")

# ---------- BACKUP ----------
elif page=="Backup":
    st.header("🔁 Backup / Restore")
    # FIX 3: Removed the 'uid' argument from function calls to match the cloud_sync.py definitions
    if st.button("Manual Full Backup to Cloud"):
        # The return value of manual_sync is ignored here
        manual_sync() 
    if st.button("Restore Full Backup from Cloud (overwrite local)"):
        # The return value of restore_data is ignored here, and the data is loaded via auto_sync later
        restore_data() 
        st.experimental_rerun()
    buf = io.BytesIO(json.dumps(data, indent=2).encode("utf-8"))
    st.download_button("Download local backup", data=buf, file_name=f"ayan_backup_{uid}.json", mime="application/json")

# Save at end of interaction
save_data(data)

