import streamlit as st
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

from database import SessionLocal, engine
from auth import (
    validate_password_strength,
    verify_password,
    get_user_by_employee_id,
    set_user_password
)
from models import (
    User,
    Fixture,
    MasterChainage,
    DismantleLog,
    InstallLog,
    Base
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="SRTPL LED Retrofit", layout="wide")

# -------------------------------------------------
# DATABASE INIT (SAFE)
# -------------------------------------------------
@st.cache_resource
def get_session():
    return SessionLocal()

db: Session = get_session()

# -------------------------------------------------
# SESSION INIT
# -------------------------------------------------
def init_session():
    defaults = {
        "logged_in": False,
        "user": None,
        "active_tab": "Dashboard"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

def logout():
    st.session_state.clear()
    st.rerun()

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
def login_page():
    st.markdown("## 🔐 SRTPL LED Retrofit System")

    emp_id = st.text_input("Employee ID", key="login_emp").strip().upper()
    if not emp_id:
        return

    user = get_user_by_employee_id(db, emp_id)

    if not user:
        st.error("Invalid Employee ID")
        return

    if not user.password_hash:
        new_pass = st.text_input("Create Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Set Password"):
            if new_pass != confirm:
                st.error("Passwords do not match")
                return
            if not validate_password_strength(new_pass):
                st.error("Weak password")
                return

            set_user_password(db, user, new_pass)
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
    else:
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if verify_password(password, user.password_hash):
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Incorrect Password")

# -------------------------------------------------
# DASHBOARD (UPDATED – TEAM + CHAINAGE FIXTURE)
# -------------------------------------------------
def dashboard_page():

    st.markdown("## 📊 Project Dashboard")

    # -----------------------------
    # GLOBAL TOTALS
    # -----------------------------
    total_target = db.query(func.sum(MasterChainage.target_qty)).scalar() or 0
    total_dismantled = db.query(func.sum(DismantleLog.qty)).scalar() or 0
    total_installed = db.query(func.sum(InstallLog.qty)).scalar() or 0

    effective_install = min(total_installed, total_target)
    remaining_balance = max(total_target - effective_install, 0)

    col1, col2 = st.columns(2)
    col1.metric("Total Target", total_target)
    col2.metric("Remaining Balance", remaining_balance)

    col3, col4 = st.columns(2)
    col3.metric("Total Dismantled", total_dismantled)
    col4.metric("Total Installed", effective_install)

    st.divider()

    # -----------------------------
    # TEAM-WISE DETAILS
    # -----------------------------
    st.markdown("### 👷 Team Performance")

    teams = db.query(MasterChainage.vendor_assigned).distinct().all()
    teams = [t[0] for t in teams]

    for team in teams:

        team_target = db.query(func.sum(MasterChainage.target_qty)).filter(
            MasterChainage.vendor_assigned == team
        ).scalar() or 0

        team_dismantled = db.query(func.sum(DismantleLog.qty)).filter(
            DismantleLog.team == team
        ).scalar() or 0

        team_installed = db.query(func.sum(InstallLog.qty)).filter(
            InstallLog.team == team
        ).scalar() or 0

        effective_team_install = min(team_installed, team_target)
        team_balance = max(team_target - effective_team_install, 0)

        st.markdown(f"#### Team {team}")

        c1, c2 = st.columns(2)
        c1.metric("Target", team_target)
        c2.metric("Balance", team_balance)

        c3, c4 = st.columns(2)
        c3.metric("Installed", effective_team_install)
        c4.metric("Dismantled", team_dismantled)

        progress = (
            effective_team_install / team_target
            if team_target else 0
        )
        progress = max(0, min(progress, 1))

        st.progress(progress, text=f"Completion: {progress*100:.1f}%")

        st.divider()

    # -----------------------------
    # CHAINAGE + FIXTURE PROGRESS
    # -----------------------------
    st.markdown("### 📍 Chainage / Fixture Progress")

    chainage_list = db.query(MasterChainage.chainage_code).distinct().all()
    chainage_list = [c[0] for c in chainage_list]

    if not chainage_list:
        st.info("No chainage data available.")
        return

    selected_chainage = st.selectbox(
        "Select Chainage",
        chainage_list,
        key="dashboard_chainage"
    )

    fixture_records = db.query(MasterChainage).filter(
        MasterChainage.chainage_code == selected_chainage
    ).all()

    for record in fixture_records:

        installed = db.query(func.sum(InstallLog.qty)).filter(
            InstallLog.chainage_code == selected_chainage,
            InstallLog.old_watt == record.old_watt
        ).scalar() or 0

        dismantled = db.query(func.sum(DismantleLog.qty)).filter(
            DismantleLog.chainage_code == selected_chainage,
            DismantleLog.old_watt == record.old_watt
        ).scalar() or 0

        effective_installed = min(installed, record.target_qty)
        balance = max(record.target_qty - effective_installed, 0)

        progress = (
            effective_installed / record.target_qty
            if record.target_qty else 0
        )
        progress = max(0, min(progress, 1))

        st.markdown(f"**Fixture {record.old_watt}W**")

        f1, f2 = st.columns(2)
        f1.metric("Target", record.target_qty)
        f2.metric("Balance", balance)

        f3, f4 = st.columns(2)
        f3.metric("Installed", effective_installed)
        f4.metric("Dismantled", dismantled)

        st.progress(
            progress,
            text=f"Completion: {progress*100:.1f}%"
        )

        st.divider()

# -------------------------------------------------
# ENTRY (UPDATED WITH LIVE TARGET + BALANCE DISPLAY)
# -------------------------------------------------
def entry_page():

    user = st.session_state.user

    st.markdown("## 🛠 Work Entry")

    entry_date = st.date_input("Entry Date", value=date.today())

    teams = db.query(MasterChainage.vendor_assigned).distinct().all()
    team_list = [t[0] for t in teams]

    selected_team = st.selectbox("Select Team", team_list, key="entry_team")

    chainage_records = db.query(MasterChainage).filter(
        MasterChainage.vendor_assigned == selected_team
    ).all()

    if not chainage_records:
        st.warning("No chainage assigned.")
        return

    chainage_list = sorted(set(c.chainage_code for c in chainage_records))
    selected_chainage = st.selectbox("Select Chainage", chainage_list, key="entry_chainage")

    fixture_records = [
        c for c in chainage_records
        if c.chainage_code == selected_chainage
    ]

    fixture_list = [f.old_watt for f in fixture_records]
    selected_fixture = st.selectbox("Select Fixture", fixture_list, key="entry_fixture")

    # ---------------------------------
    # TARGET FETCH
    # ---------------------------------
    target_qty = next(
        (c.target_qty for c in fixture_records if c.old_watt == selected_fixture),
        0
    )

    total_dismantled = db.query(func.sum(DismantleLog.qty)).filter(
        DismantleLog.chainage_code == selected_chainage,
        DismantleLog.old_watt == selected_fixture
    ).scalar() or 0

    total_installed = db.query(func.sum(InstallLog.qty)).filter(
        InstallLog.chainage_code == selected_chainage,
        InstallLog.old_watt == selected_fixture
    ).scalar() or 0

    st.markdown("### 📊 Current Status")

    col1, col2 = st.columns(2)
    col1.metric("Target Qty", target_qty)
    col2.metric("Total Dismantled", total_dismantled)

    col3, col4 = st.columns(2)
    col3.metric("Total Installed", total_installed)
    col4.metric("Remaining Target", max(target_qty - total_installed, 0))

    st.divider()

    # ---------------------------------
    # ACTIVITY SELECTION
    # ---------------------------------
    activity = st.radio("Activity", ["Dismantle", "Install"], key="entry_activity")

    qty = st.number_input("Quantity", min_value=1, key="entry_qty")

    # ---------------------------------
    # LIVE BALANCE PREVIEW
    # ---------------------------------
    if activity == "Dismantle":
        available_balance = target_qty - total_dismantled
        post_balance = available_balance - qty

        st.info(f"Available for Dismantle: {available_balance}")
        st.info(f"Balance After Entry: {post_balance}")

    else:
        available_balance = total_dismantled - total_installed
        post_balance = available_balance - qty

        st.info(f"Available for Install: {available_balance}")
        st.info(f"Balance After Entry: {post_balance}")

    st.divider()

    # ---------------------------------
    # SUBMIT
    # ---------------------------------
    if st.button("Submit"):

        if activity == "Dismantle":
            if total_dismantled + qty > target_qty:
                st.error("Cannot dismantle more than target quantity.")
                return

            db.add(DismantleLog(
                entry_date=entry_date,
                chainage_code=selected_chainage,
                old_watt=selected_fixture,
                qty=qty,
                team=selected_team,
                entered_by=user.id
            ))

        else:
            if total_installed + qty > total_dismantled:
                st.error("Install cannot exceed dismantled quantity.")
                return

            db.add(InstallLog(
                entry_date=entry_date,
                chainage_code=selected_chainage,
                old_watt=selected_fixture,
                new_watt=selected_fixture,
                qty=qty,
                team=selected_team,
                entered_by=user.id
            ))

        db.commit()
        st.success("Entry Saved Successfully")
        st.rerun()

# -------------------------------------------------
# USER REPORT
# -------------------------------------------------
def report_page():

    st.markdown("## 📄 My Entry Report")

    user = st.session_state.user

    data = db.query(InstallLog).filter(
        InstallLog.entered_by == user.id
    ).all()

    df = pd.DataFrame([{
        "Date": r.entry_date,
        "Chainage": r.chainage_code,
        "Fixture": r.old_watt,
        "Qty": r.qty,
        "Team": r.team
    } for r in data])

    if df.empty:
        st.info("No entries found.")
        return

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download My Report",
        df.to_csv(index=False),
        file_name="my_report.csv"
    )

# -------------------------------------------------
# ADMIN PAGE
# -------------------------------------------------
def admin_page():

    st.markdown("## 🛡 Admin Control Panel")

    install_data = db.query(InstallLog).all()
    dismantle_data = db.query(DismantleLog).all()

    install_df = pd.DataFrame([vars(r) for r in install_data])
    dismantle_df = pd.DataFrame([vars(r) for r in dismantle_data])

    final_df = pd.concat([install_df, dismantle_df], ignore_index=True)

    st.dataframe(final_df, use_container_width=True)

    st.download_button(
        "Download Full Project Report",
        final_df.to_csv(index=False),
        file_name="full_project_report.csv"
    )

# -------------------------------------------------
# MAIN ROUTER
# -------------------------------------------------
def main_app():

    user = st.session_state.user

    st.sidebar.markdown(f"### 👤 {user.full_name}")
    st.sidebar.markdown(f"Role: {user.role}")

    if st.sidebar.button("Logout"):
        logout()

    tabs = ["Dashboard", "Entry", "Report"]

    if user.role == "admin":
        tabs.append("Admin")

    tab = st.radio("Navigation", tabs, horizontal=True)

    if tab == "Dashboard":
        dashboard_page()
    elif tab == "Entry":
        entry_page()
    elif tab == "Report":
        report_page()
    elif tab == "Admin" and user.role == "admin":
        admin_page()

# -------------------------------------------------
# APP ENTRY
# -------------------------------------------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
