import streamlit as st
import pandas as pd
from sqlalchemy import func
from models import MasterChainage, DismantleLog, InstallLog


def data_integrity_audit(db):

    st.divider()
    st.markdown("## 🔎 Data Integrity Audit")

    total_dismantled = db.query(func.sum(DismantleLog.qty)).scalar() or 0
    total_installed = db.query(func.sum(InstallLog.qty)).scalar() or 0

    if total_installed > total_dismantled:
        st.error(
            f"⚠ DATA INTEGRITY ALERT: Installed ({total_installed}) "
            f"exceeds Dismantled ({total_dismantled})"
        )
    else:
        st.success("✔ Project-Level Integrity OK")

    # --------------------------
    # Chainage + Fixture Audit
    # --------------------------
    records = db.query(
        MasterChainage.chainage_code,
        MasterChainage.old_watt
    ).distinct().all()

    mismatch_rows = []

    for chainage, watt in records:

        dismantled = db.query(func.sum(DismantleLog.qty)).filter(
            DismantleLog.chainage_code == chainage,
            DismantleLog.old_watt == watt
        ).scalar() or 0

        installed = db.query(func.sum(InstallLog.qty)).filter(
            InstallLog.chainage_code == chainage,
            InstallLog.old_watt == watt
        ).scalar() or 0

        if installed > dismantled:
            mismatch_rows.append({
                "Chainage": chainage,
                "Old Watt": watt,
                "Dismantled": dismantled,
                "Installed": installed,
                "Excess Installed": installed - dismantled
            })

    if mismatch_rows:
        st.warning("⚠ Chainage-Level Violations Found")
        df = pd.DataFrame(mismatch_rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.success("✔ All Chainage-Level Records Valid")