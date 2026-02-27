import streamlit as st
import pandas as pd
from sqlalchemy import func, and_

from models import (
    MasterChainage,
    DismantleLog,
    InstallLog,
    Fixture
)

HOURS_PER_DAY = 12
DAYS_PER_YEAR = 365
RATE_PER_UNIT = 8


# -------------------------------------------------
# ULTRA MOBILE EXECUTIVE MODE (ADDITIVE ONLY)
# -------------------------------------------------
def ultra_mobile_executive_layer(db, from_date, to_date):

    st.divider()
    st.markdown("## 📱 Executive Mobile View")

    date_filter_d = and_(DismantleLog.entry_date >= from_date,
                         DismantleLog.entry_date <= to_date)

    date_filter_i = and_(InstallLog.entry_date >= from_date,
                         InstallLog.entry_date <= to_date)

    total_target = db.query(func.sum(MasterChainage.target_qty)).scalar() or 0
    total_dismantled = db.query(func.sum(DismantleLog.qty)).filter(date_filter_d).scalar() or 0
    total_installed = db.query(func.sum(InstallLog.qty)).filter(date_filter_i).scalar() or 0

    effective_installed = min(total_installed, total_dismantled)
    completion = (effective_installed / total_target * 100) if total_target else 0

    st.markdown(f"""
    <div style="background:#eef2f7;padding:15px;border-radius:12px;margin-bottom:10px">
        <b>Target:</b> {total_target}<br>
        <b>Dismantled:</b> {total_dismantled}<br>
        <b>Installed:</b> {effective_installed}<br>
        <b>Completion:</b> {completion:.2f}%
    </div>
    """, unsafe_allow_html=True)


# -------------------------------------------------
# ADVANCED EXPORT ENGINE (ADDITIVE ONLY)
# -------------------------------------------------
def advanced_export_layer(db, from_date, to_date):

    st.divider()
    st.markdown("## 📤 Advanced Export Center")

    date_filter_d = and_(DismantleLog.entry_date >= from_date,
                         DismantleLog.entry_date <= to_date)

    date_filter_i = and_(InstallLog.entry_date >= from_date,
                         InstallLog.entry_date <= to_date)

    # -------- PROJECT SUMMARY --------
    if st.button("Download Project Summary (CSV)"):

        total_target = db.query(func.sum(MasterChainage.target_qty)).scalar() or 0
        total_dismantled = db.query(func.sum(DismantleLog.qty)).filter(date_filter_d).scalar() or 0
        total_installed = db.query(func.sum(InstallLog.qty)).filter(date_filter_i).scalar() or 0

        completion = (total_installed / total_target * 100) if total_target else 0

        df = pd.DataFrame({
            "Total Target":[total_target],
            "Total Dismantled":[total_dismantled],
            "Total Installed":[total_installed],
            "Completion %":[completion]
        })

        st.download_button(
            "Click to Download",
            df.to_csv(index=False),
            file_name="Project_Summary.csv",
            mime="text/csv"
        )

    # -------- CHAINAGE SUMMARY --------
    if st.button("Download Chainage Summary (CSV)"):

        chainage_data = db.query(
            MasterChainage.chainage_code,
            func.sum(MasterChainage.target_qty)
        ).group_by(MasterChainage.chainage_code).all()

        rows = []

        for chainage, target in chainage_data:
            installed = db.query(func.sum(InstallLog.qty)).filter(
                InstallLog.chainage_code == chainage
            ).scalar() or 0

            percent = (installed / target * 100) if target else 0

            rows.append({
                "Chainage": chainage,
                "Target": target,
                "Installed": installed,
                "Completion %": percent
            })

        df_chain = pd.DataFrame(rows)

        st.download_button(
            "Click to Download",
            df_chain.to_csv(index=False),
            file_name="Chainage_Report.csv",
            mime="text/csv"
        )