import streamlit as st
from sqlalchemy import func, desc
from models import MasterChainage, DismantleLog, InstallLog


def auto_correct_installed_excess(db):

    st.divider()
    st.markdown("## 🛠 Admin Auto-Correction Tool (Chainage-Level)")

    records = db.query(
        MasterChainage.chainage_code,
        MasterChainage.old_watt
    ).distinct().all()

    violations_found = False

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

            violations_found = True
            excess = installed - dismantled

            st.error(
                f"Violation → {chainage} | {watt}W | "
                f"Excess Installed: {excess}"
            )

            if st.button(f"Fix {chainage}-{watt}"):

                remaining_excess = excess

                install_entries = db.query(InstallLog).filter(
                    InstallLog.chainage_code == chainage,
                    InstallLog.old_watt == watt
                ).order_by(
                    desc(InstallLog.entry_date),
                    desc(InstallLog.id)
                ).all()

                for entry in install_entries:

                    if remaining_excess <= 0:
                        break

                    if entry.qty <= remaining_excess:
                        remaining_excess -= entry.qty
                        db.delete(entry)
                    else:
                        entry.qty -= remaining_excess
                        remaining_excess = 0

                db.commit()
                st.success(f"✔ Corrected {chainage} - {watt}W")

    if not violations_found:
        st.success("✔ All Chainage-Level Records Valid. No correction needed.")