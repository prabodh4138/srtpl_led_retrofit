from auto_correction_layer import auto_correct_installed_excess
from data_audit_layer import data_integrity_audit
import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import SessionLocal
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
# DATABASE INIT
# -------------------------------------------------
db: Session = SessionLocal()
Base.metadata.create_all(bind=db.get_bind())

st.set_page_config(
    page_title="SRTPL LED Retrofit",
    layout="wide",
    initial_sidebar_state="collapsed"
)
from ui_loader import load_css
load_css("assets/mobile.css")

HOURS_PER_DAY = 12
DAYS_PER_YEAR = 365
RATE_PER_UNIT = 8

# -------------------------------------------------
# SESSION
# -------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None

# -------------------------------------------------
# LOGIN
# -------------------------------------------------
def login_page():
    st.markdown("## 🔐 SRTPL LED Retrofit System")

    employee_id = st.text_input("Employee ID").strip().upper()

    if employee_id:
        user = get_user_by_employee_id(db, employee_id)

        if not user:
            st.error("Invalid Employee ID")
            return

        if not user.password_hash:
            st.success(f"Welcome {user.full_name}")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            if st.button("Set Password"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                if not validate_password_strength(new_password):
                    st.error("Password must contain letters, numbers and special character.")
                    return
                set_user_password(db, user, new_password)
                st.success("Password set successfully.")
                return
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
# DASHBOARD FULL RESTORED
# -------------------------------------------------
# (Everything above remains EXACTLY SAME as your uploaded file)

# -------------------------------------------------
# DASHBOARD FULL RESTORED
# -------------------------------------------------
def project_dashboard():

    st.markdown("### 📊 Project Dashboard")

    # DATE FILTER
    colf1, colf2 = st.columns(2)
    from_date = colf1.date_input("From Date", value=date(2025,1,1))
    to_date = colf2.date_input("To Date", value=date.today())

    date_filter_d = and_(DismantleLog.entry_date >= from_date,
                         DismantleLog.entry_date <= to_date)

    date_filter_i = and_(InstallLog.entry_date >= from_date,
                         InstallLog.entry_date <= to_date)
    from executive_layer import ultra_mobile_executive_layer, advanced_export_layer

    # MAIN KPIs
    total_target = db.query(func.sum(MasterChainage.target_qty)).scalar() or 0
    total_dismantled = db.query(func.sum(DismantleLog.qty)).filter(date_filter_d).scalar() or 0
    total_installed = db.query(func.sum(InstallLog.qty)).filter(date_filter_i).scalar() or 0

    effective_installed = min(total_installed, total_dismantled)
    wip = total_dismantled - effective_installed
    completion = (effective_installed / total_target * 100) if total_target else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Target", total_target)
    col2.metric("Dismantled", total_dismantled)
    col3.metric("Installed", effective_installed)
    col4.metric("WIP", wip)
    col5.metric("Completion %", f"{completion:.2f}%")

    # ENERGY
    fixtures = db.query(Fixture).all()
    total_units_saved = 0
    fixture_energy_data = []

    for f in fixtures:
        installed_qty = db.query(func.sum(InstallLog.qty)).filter(
            and_(InstallLog.old_watt == f.old_watt, date_filter_i)
        ).scalar() or 0

        units = (
            installed_qty *
            f.saving_watt *
            HOURS_PER_DAY *
            DAYS_PER_YEAR
        ) / 1000

        total_units_saved += units

        fixture_energy_data.append({
            "Old Watt": f.old_watt,
            "Annual Units Saved": units
        })

    total_rupees = total_units_saved * RATE_PER_UNIT

    st.divider()
    col6, col7 = st.columns(2)
    col6.metric("Annual Energy Saved (kWh)", f"{total_units_saved:,.2f}")
    col7.metric("Annual Saving (₹)", f"{total_rupees:,.2f}")

    # TEAM PERFORMANCE
    st.divider()
    st.subheader("🏆 Team Performance")

    team_data = db.query(
        InstallLog.team,
        func.sum(InstallLog.qty)
    ).filter(date_filter_i).group_by(InstallLog.team).all()

    team_summary = {team: qty for team, qty in team_data}

    col8, col9 = st.columns(2)
    col8.metric("Team A Installed", team_summary.get("A", 0))
    col9.metric("Team B Installed", team_summary.get("B", 0))

    # =====================================================
    # ✅ ADVANCED DROPDOWN CHAINAGE PROGRESS (UPGRADED)
    # =====================================================

    st.divider()
    st.subheader("📍 Chainage & Fixture Progress")

    chainages = db.query(MasterChainage.chainage_code).distinct().all()
    chainage_list = sorted([c[0] for c in chainages])

    if chainage_list:

        selected_chainage = st.selectbox("Select Chainage", chainage_list)

        # CHAINAGE TOTALS
        chain_target = db.query(func.sum(MasterChainage.target_qty)).filter(
            MasterChainage.chainage_code == selected_chainage
        ).scalar() or 0

        chain_dismantled = db.query(func.sum(DismantleLog.qty)).filter(
            and_(DismantleLog.chainage_code == selected_chainage, date_filter_d)
        ).scalar() or 0

        chain_installed = db.query(func.sum(InstallLog.qty)).filter(
            and_(InstallLog.chainage_code == selected_chainage, date_filter_i)
        ).scalar() or 0

        chain_completion = (chain_installed / chain_target * 100) if chain_target else 0

        colc1, colc2, colc3, colc4 = st.columns(4)
        colc1.metric("Chainage Target", chain_target)
        colc2.metric("Chainage Dismantled", chain_dismantled)
        colc3.metric("Chainage Installed", chain_installed)
        colc4.metric("Completion %", f"{chain_completion:.2f}%")

        st.progress(min(chain_completion / 100, 1.0))

        # FIXTURE DROPDOWN
        fixture_records = db.query(MasterChainage.old_watt).filter(
            MasterChainage.chainage_code == selected_chainage
        ).distinct().all()

        fixture_list = sorted([f[0] for f in fixture_records])

        if fixture_list:

            selected_fixture = st.selectbox("Select Fixture (Old Watt)", fixture_list)

            fix_target = db.query(MasterChainage.target_qty).filter(
                MasterChainage.chainage_code == selected_chainage,
                MasterChainage.old_watt == selected_fixture
            ).scalar() or 0

            fix_dismantled = db.query(func.sum(DismantleLog.qty)).filter(
                DismantleLog.chainage_code == selected_chainage,
                DismantleLog.old_watt == selected_fixture
            ).scalar() or 0

            fix_installed = db.query(func.sum(InstallLog.qty)).filter(
                InstallLog.chainage_code == selected_chainage,
                InstallLog.old_watt == selected_fixture
            ).scalar() or 0

            fix_completion = (fix_installed / fix_target * 100) if fix_target else 0

            colf1, colf2, colf3, colf4 = st.columns(4)
            colf1.metric("Fixture Target", fix_target)
            colf2.metric("Fixture Dismantled", fix_dismantled)
            colf3.metric("Fixture Installed", fix_installed)
            colf4.metric("Completion %", f"{fix_completion:.2f}%")

            st.progress(min(fix_completion / 100, 1.0))
            ultra_mobile_executive_layer(db, from_date, to_date)
            advanced_export_layer(db, from_date, to_date)
            data_integrity_audit(db)

# -------------------------------------------------
# STRICT WORK ENTRY
# -------------------------------------------------
def work_entry_page():

    user = st.session_state.user
    st.markdown("### 🛠 Work Entry")

    entry_date = st.date_input("Entry Date", value=date.today())

    if user.role == "vendor":
        team = user.vendor_team
        st.info(f"Team: {team}")
        chainage_records = db.query(MasterChainage).filter(
            MasterChainage.vendor_assigned == team
        ).all()
    else:
        team = st.selectbox("Select Team", ["A", "B"])
        chainage_records = db.query(MasterChainage).filter(
            MasterChainage.vendor_assigned == team
        ).all()

    if not chainage_records:
        st.warning("No chainage assigned.")
        return

    chainage_list = sorted(list(set([c.chainage_code for c in chainage_records])))
    selected_chainage = st.selectbox("Select Chainage", chainage_list)

    fixture_records = db.query(MasterChainage).filter(
        MasterChainage.chainage_code == selected_chainage,
        MasterChainage.vendor_assigned == team
    ).all()

    fixture_list = [f.old_watt for f in fixture_records]
    selected_watt = st.selectbox("Select Old Fixture Watt", fixture_list)

    activity = st.radio("Activity", ["Dismantle", "Install"])
    qty = st.number_input("Quantity", min_value=1)
    manpower = st.number_input("Manpower Deployed", min_value=1)

    target_record = db.query(MasterChainage).filter(
        MasterChainage.chainage_code == selected_chainage,
        MasterChainage.old_watt == selected_watt
    ).first()

    target_qty = target_record.target_qty

    dismantled = db.query(func.sum(DismantleLog.qty)).filter(
        DismantleLog.chainage_code == selected_chainage,
        DismantleLog.old_watt == selected_watt
    ).scalar() or 0

    installed = db.query(func.sum(InstallLog.qty)).filter(
        InstallLog.chainage_code == selected_chainage,
        InstallLog.old_watt == selected_watt
    ).scalar() or 0

    st.info(f"Target: {target_qty}")
    st.info(f"Dismantled: {dismantled}")
    st.info(f"Installed: {installed}")

    if st.button("Submit Entry"):

        if activity == "Dismantle":
            if dismantled + qty > target_qty:
                st.error("Cannot exceed dismantle target.")
                return

            db.add(DismantleLog(
                entry_date=entry_date,
                chainage_code=selected_chainage,
                old_watt=selected_watt,
                qty=qty,
                manpower_deployed=manpower,
                team=team,
                entered_by=user.id
            ))

        else:
            if installed + qty > dismantled:
                st.error("Install cannot exceed dismantled quantity.")
                return

            fixture_map = db.query(Fixture).filter(
                Fixture.old_watt == selected_watt
            ).first()

            db.add(InstallLog(
                entry_date=entry_date,
                chainage_code=selected_chainage,
                old_watt=selected_watt,
                new_watt=fixture_map.new_watt,
                qty=qty,
                manpower_deployed=manpower,
                team=team,
                entered_by=user.id
            ))

        db.commit()
        st.success("Entry Saved")
        st.rerun()

# -------------------------------------------------
# ADMIN PANEL
# -------------------------------------------------
def admin_panel():

    st.markdown("### 🔐 Admin Management Panel")

    # -------------------------------
    # USER CREATION SECTION
    # -------------------------------
    st.subheader("👤 Create New User")

    emp_id = st.text_input("Employee ID").upper()
    name = st.text_input("Full Name")
    role = st.selectbox("Role", ["vendor", "staff"])
    team = st.selectbox("Vendor Team", ["A", "B"]) if role == "vendor" else None

    if st.button("Create User"):
        if db.query(User).filter(User.employee_id == emp_id).first():
            st.error("User already exists.")
        else:
            new_user = User(
                employee_id=emp_id,
                full_name=name,
                role=role,
                vendor_team=team
            )
            db.add(new_user)
            db.commit()
            st.success("User Created Successfully.")

    # -------------------------------
    # DATA INTEGRITY SECTION
    # -------------------------------
    from data_audit_layer import data_integrity_audit
    from auto_correction_layer import auto_correct_installed_excess

    data_integrity_audit(db)

    # -------------------------------
    # AUTO CORRECTION SECTION
    # -------------------------------
    auto_correct_installed_excess(db)

# -------------------------------------------------
# MAIN
# -------------------------------------------------
def dashboard_page():
    user = st.session_state.user

    st.sidebar.markdown(f"**{user.full_name}**")
    st.sidebar.markdown(f"Role: {user.role}")

    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    if user.role == "admin":
        tab1, tab2, tab3 = st.tabs(["Dashboard", "Work Entry", "Admin"])
        with tab1:
            project_dashboard()
        with tab2:
            work_entry_page()
        with tab3:
            admin_panel()
    else:
        tab1, tab2 = st.tabs(["Dashboard", "Work Entry"])
        with tab1:
            project_dashboard()
        with tab2:
            work_entry_page()

if not st.session_state.logged_in:
    login_page()
else:
    dashboard_page()