from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from config import DESIGNATIONS
from database import execute, fetch_df
from modules.components import download_excel_button, hero, section, show_kpis
from modules.page_import import import_panel


OPERATIONS_CRITERIA = [
    ("technical_knowledge", "Technical Knowledge"),
    ("position_specific_skills", "Position Specific Skills"),
    ("relevant_experience", "Relevant Experience"),
    ("problem_solving_ability", "Problem Solving Ability"),
    ("teamwork", "Teamwork"),
    ("operations_overall_impression", "Overall Impression"),
]

PC_CRITERIA = [
    ("communication_skills", "Communication Skills"),
    ("confidence_professionalism", "Confidence & Professionalism"),
    ("personality_attitude", "Personality & Attitude"),
    ("personality_assessment", "Overall Personality Assessment"),
]

RECOMMENDATIONS = [
    "Strongly recommended",
    "Recommended",
    "Recommended with reservations",
    "Do not recommend",
]


def _as_date(value: object) -> date:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return date.today()
    return parsed.date()


def _weighted_score(row: pd.Series) -> float:
    ops_scores = [pd.to_numeric(row.get(col), errors="coerce") for col, _ in OPERATIONS_CRITERIA]
    pc_scores = [pd.to_numeric(row.get(col), errors="coerce") for col, _ in PC_CRITERIA]
    ops_avg = pd.Series(ops_scores).fillna(0).mean()
    pc_avg = pd.Series(pc_scores).fillna(0).mean()
    return round((ops_avg * 0.70) + (pc_avg * 0.30), 2)


def _decision_from_recommendations(operations: str, pc: str) -> str:
    recommendations = [operations, pc]
    if "Do not recommend" in recommendations:
        return "Do not recommend"
    if "Recommended with reservations" in recommendations:
        return "Recommended with reservations"
    if recommendations == ["Strongly recommended", "Strongly recommended"]:
        return "Strongly recommended"
    return "Recommended"


def _sync_due_interviews() -> int:
    recruitment = fetch_df(
        """
        SELECT id, candidate, position, interview_date, expected_salary, notice_period
        FROM recruitment
        WHERE interview_date IS NOT NULL AND TRIM(interview_date) <> ''
        """
    )
    if recruitment.empty:
        return 0

    existing = fetch_df("SELECT recruitment_id FROM interview_evaluation WHERE recruitment_id IS NOT NULL")
    existing_ids = set(pd.to_numeric(existing.get("recruitment_id"), errors="coerce").dropna().astype(int)) if not existing.empty else set()

    today = pd.Timestamp.today().normalize()
    added = 0
    for _, row in recruitment.iterrows():
        recruitment_id = int(row["id"])
        interview_date = pd.to_datetime(row["interview_date"], errors="coerce")
        if pd.isna(interview_date) or interview_date.normalize() > today or recruitment_id in existing_ids:
            continue

        execute(
            """
            INSERT INTO interview_evaluation(
                recruitment_id, candidate, position, department, interview_date,
                technical_score, experience_score, communication_score,
                technical_knowledge, position_specific_skills, relevant_experience,
                problem_solving_ability, teamwork, operations_overall_impression,
                communication_skills, confidence_professionalism, personality_attitude,
                personality_assessment, recommended_salary, final_notice_period,
                final_decision
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recruitment_id,
                row["candidate"],
                row["position"],
                "Citi Homes",
                str(_as_date(row["interview_date"])),
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                3,
                float(row.get("expected_salary") or 0),
                row.get("notice_period") or "",
                "Recommended",
            ),
        )
        added += 1
    return added


def _due_recruitment_options(recruitment: pd.DataFrame) -> pd.DataFrame:
    if recruitment.empty:
        return recruitment
    df = recruitment.copy()
    df["parsed_interview_date"] = pd.to_datetime(df["interview_date"], errors="coerce")
    today = pd.Timestamp.today().normalize()
    return df[df["parsed_interview_date"].notna() & (df["parsed_interview_date"].dt.normalize() <= today)]


def _candidate_selector(recruitment: pd.DataFrame) -> pd.Series | None:
    due = _due_recruitment_options(recruitment)
    options = ["Manual Entry"]
    option_rows: dict[str, pd.Series] = {}
    for _, row in due.iterrows():
        label = f"{row['candidate']} - {row['position']} ({_as_date(row['interview_date']).isoformat()})"
        options.append(label)
        option_rows[label] = row

    selected = st.selectbox("Load candidate from recruitment tracker", options)
    if selected == "Manual Entry":
        st.caption("Manual entry is enabled. You can type candidate details directly in the form.")
        return None

    st.caption("Details are loaded from the recruitment tracker. You can still edit before saving.")
    return option_rows[selected]


def _criteria_inputs(criteria: list[tuple[str, str]], prefix: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for index in range(0, len(criteria), 3):
        cols = st.columns(3)
        for col, (field, label) in zip(cols, criteria[index : index + 3]):
            values[field] = col.slider(label, 1, 5, 3, key=f"{prefix}_{field}")
    return values


def _save_evaluation(source: pd.Series | None, values: dict[str, object]) -> None:
    recruitment_id = int(source["id"]) if source is not None and pd.notna(source.get("id")) else None
    final_decision = str(values["final_decision"])
    interviewer_comments = "\n\n".join(
        part
        for part in [
            f"Operations comments: {values['operations_comments']}",
            f"P&C comments: {values['pc_comments']}",
            f"Final remarks: {values['final_remarks']}",
        ]
        if part.strip().split(": ", 1)[-1]
    )

    params = (
        recruitment_id,
        values["candidate"],
        values["position"],
        values["department"],
        values["interviewer_names"],
        str(values["interview_date"]),
        values["technical_knowledge"],
        values["relevant_experience"],
        values["communication_skills"],
        values["technical_knowledge"],
        values["position_specific_skills"],
        values["relevant_experience"],
        values["problem_solving_ability"],
        values["teamwork"],
        values["operations_overall_impression"],
        values["operations_strengths"],
        values["operations_improvements"],
        values["operations_remarks"],
        values["operations_recommendation"],
        values["operations_comments"],
        values["communication_skills"],
        values["confidence_professionalism"],
        values["personality_attitude"],
        values["personality_assessment"],
        values["pc_strengths"],
        values["pc_improvements"],
        values["pc_remarks"],
        values["pc_recommendation"],
        values["pc_comments"],
        values["recommended_salary"],
        values["final_notice_period"],
        values["final_remarks"],
        values["operations_signature"],
        values["pc_signature"],
        final_decision,
        interviewer_comments,
    )

    if recruitment_id is not None:
        existing = fetch_df("SELECT id FROM interview_evaluation WHERE recruitment_id=?", (recruitment_id,))
        if not existing.empty:
            execute(
                """
                UPDATE interview_evaluation SET
                    recruitment_id=?, candidate=?, position=?, department=?, interviewer_names=?,
                    interview_date=?, technical_score=?, experience_score=?, communication_score=?,
                    technical_knowledge=?, position_specific_skills=?, relevant_experience=?,
                    problem_solving_ability=?, teamwork=?, operations_overall_impression=?,
                    operations_strengths=?, operations_improvements=?, operations_remarks=?,
                    operations_recommendation=?, operations_comments=?, communication_skills=?,
                    confidence_professionalism=?, personality_attitude=?, personality_assessment=?,
                    pc_strengths=?, pc_improvements=?, pc_remarks=?, pc_recommendation=?,
                    pc_comments=?, recommended_salary=?, final_notice_period=?, final_remarks=?,
                    operations_signature=?, pc_signature=?, final_decision=?, interviewer_comments=?
                WHERE recruitment_id=?
                """,
                (*params, recruitment_id),
            )
            return

    execute(
        """
        INSERT INTO interview_evaluation(
            recruitment_id, candidate, position, department, interviewer_names,
            interview_date, technical_score, experience_score, communication_score,
            technical_knowledge, position_specific_skills, relevant_experience,
            problem_solving_ability, teamwork, operations_overall_impression,
            operations_strengths, operations_improvements, operations_remarks,
            operations_recommendation, operations_comments, communication_skills,
            confidence_professionalism, personality_attitude, personality_assessment,
            pc_strengths, pc_improvements, pc_remarks, pc_recommendation,
            pc_comments, recommended_salary, final_notice_period, final_remarks,
            operations_signature, pc_signature, final_decision, interviewer_comments
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        params,
    )


def _evaluation_form(recruitment: pd.DataFrame) -> None:
    source = _candidate_selector(recruitment)
    default_candidate = "" if source is None else str(source["candidate"])
    default_position = DESIGNATIONS[0] if source is None else str(source["position"])
    default_date = date.today() if source is None else _as_date(source["interview_date"])
    default_salary = 0.0 if source is None else float(source.get("expected_salary") or 0)
    default_notice = "" if source is None else str(source.get("notice_period") or "")

    with st.expander("Add Interview Evaluation", expanded=True):
        with st.form("interview_form", clear_on_submit=False):
            section("Candidate Details")
            c1, c2, c3 = st.columns(3)
            candidate = c1.text_input("Candidate Name", value=default_candidate)
            position_options = DESIGNATIONS if default_position in DESIGNATIONS else [default_position, *DESIGNATIONS]
            position = c2.selectbox("Position Applied", position_options, index=0)
            department = c3.text_input("Department", value="Citi Homes", disabled=True)
            c4, c5 = st.columns(2)
            interview_date = c4.date_input("Date", value=default_date)
            interviewer_names = c5.text_input("Interviewer Names")

            section("Operations / Technical Evaluation - 70%")
            operations_scores = _criteria_inputs(OPERATIONS_CRITERIA, "ops")
            o1, o2, o3 = st.columns(3)
            operations_strengths = o1.text_area("Operations Strengths")
            operations_improvements = o2.text_area("Operations Areas of Improvement")
            operations_remarks = o3.text_area("Operations Remarks")
            operations_recommendation = st.selectbox("Final Recommendation / Operations", RECOMMENDATIONS)
            operations_comments = st.text_area("Operations Comments, if any")

            section("P&C Evaluation - 30%")
            pc_scores = _criteria_inputs(PC_CRITERIA, "pc")
            p1, p2, p3 = st.columns(3)
            pc_strengths = p1.text_area("P&C Strengths")
            pc_improvements = p2.text_area("P&C Areas of Improvement")
            pc_remarks = p3.text_area("P&C Remarks")
            pc_recommendation = st.selectbox("Final Recommendation / P&C", RECOMMENDATIONS)
            pc_comments = st.text_area("P&C Comments, if any")

            section("Final Details")
            f1, f2, f3 = st.columns(3)
            recommended_salary = f1.number_input("Recommended Salary", min_value=0.0, step=100.0, value=default_salary)
            final_notice_period = f2.text_input("Notice Period", value=default_notice)
            final_decision = f3.selectbox(
                "Final Decision",
                RECOMMENDATIONS,
                index=RECOMMENDATIONS.index(_decision_from_recommendations(operations_recommendation, pc_recommendation)),
            )
            final_remarks = st.text_input("Remarks")
            s1, s2 = st.columns(2)
            operations_signature = s1.text_input("Operations Signature")
            pc_signature = s2.text_input("P&C Signature")

            submit = st.form_submit_button("Save Evaluation", width="stretch")
            if submit:
                if not candidate:
                    st.error("Candidate name is required.")
                    return

                _save_evaluation(
                    source,
                    {
                        "candidate": candidate,
                        "position": position,
                        "department": department,
                        "interviewer_names": interviewer_names,
                        "interview_date": interview_date,
                        **operations_scores,
                        "operations_strengths": operations_strengths,
                        "operations_improvements": operations_improvements,
                        "operations_remarks": operations_remarks,
                        "operations_recommendation": operations_recommendation,
                        "operations_comments": operations_comments,
                        **pc_scores,
                        "pc_strengths": pc_strengths,
                        "pc_improvements": pc_improvements,
                        "pc_remarks": pc_remarks,
                        "pc_recommendation": pc_recommendation,
                        "pc_comments": pc_comments,
                        "final_decision": final_decision,
                        "recommended_salary": recommended_salary,
                        "final_notice_period": final_notice_period,
                        "final_remarks": final_remarks,
                        "operations_signature": operations_signature,
                        "pc_signature": pc_signature,
                    },
                )
                st.success("Interview evaluation saved.")
                st.rerun()


def _summary(df: pd.DataFrame) -> None:
    section("Evaluation Summary")
    if df.empty:
        st.info("No interview evaluation records yet.")
        return

    scored = df.copy()
    scored["weighted_score"] = scored.apply(_weighted_score, axis=1)
    show_kpis(
        [
            ("Evaluations", len(scored), "Saved interview forms"),
            ("Recommended", int(scored["final_decision"].isin(RECOMMENDATIONS[:3]).sum()), "Positive final decisions"),
            ("Average Score", f"{scored['weighted_score'].mean():.2f}/5", "70% operations, 30% P&C"),
        ],
        cols=3,
    )

    display = scored[
        [
            "candidate",
            "position",
            "department",
            "interview_date",
            "operations_recommendation",
            "pc_recommendation",
            "weighted_score",
            "final_decision",
            "recommended_salary",
            "final_notice_period",
        ]
    ].copy()
    display.insert(0, "Sr. No", range(1, len(display) + 1))
    display.columns = [col.replace("_", " ").title() for col in display.columns]
    st.dataframe(display, width="stretch", hide_index=True)


def _scheduled_notes(recruitment: pd.DataFrame) -> None:
    if recruitment.empty:
        return
    upcoming = recruitment.copy()
    upcoming["parsed_interview_date"] = pd.to_datetime(upcoming["interview_date"], errors="coerce")
    today = pd.Timestamp.today().normalize()
    upcoming = upcoming[upcoming["parsed_interview_date"].notna() & (upcoming["parsed_interview_date"].dt.normalize() > today)]
    if upcoming.empty:
        return

    section("Upcoming Interviews")
    preview = upcoming[["candidate", "position", "interview_date", "status"]].copy().head(10)
    preview.columns = ["Candidate", "Position", "Interview Date", "Status"]
    st.caption("Future-dated candidates will be added to Interview Evaluation automatically on their interview date.")
    st.dataframe(preview, width="stretch", hide_index=True)


def _evaluation_table() -> None:
    section("Interview Evaluation Table")
    df = fetch_df("SELECT * FROM interview_evaluation ORDER BY id ASC")
    if df.empty:
        st.info("No interview evaluation records yet.")
        return

    table_df = df.copy()
    table_df["department"] = "Citi Homes"
    for column in ["final_decision", "operations_recommendation", "pc_recommendation"]:
        table_df[column] = table_df[column].where(table_df[column].isin(RECOMMENDATIONS), "Recommended")
    table_df.insert(0, "Sr. No", range(1, len(table_df) + 1))
    priority_columns = [
        "Sr. No",
        "candidate",
        "position",
        "department",
        "interview_date",
        "operations_recommendation",
        "pc_recommendation",
        "final_decision",
        "recommended_salary",
        "final_notice_period",
        "final_remarks",
    ]
    ordered_columns = priority_columns + [col for col in table_df.columns if col not in priority_columns]
    table_df = table_df[ordered_columns]

    edited = st.data_editor(
        table_df,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        disabled=["Sr. No", "id", "department"],
        column_config={
            "id": None,
            "Sr. No": st.column_config.NumberColumn("Sr. No", width="small"),
            "department": st.column_config.TextColumn("Department", disabled=True),
            "final_decision": st.column_config.SelectboxColumn("Final Decision", options=RECOMMENDATIONS, required=True),
            "operations_recommendation": st.column_config.SelectboxColumn(
                "Final Recommendation / Operations",
                options=RECOMMENDATIONS,
            ),
            "pc_recommendation": st.column_config.SelectboxColumn(
                "Final Recommendation / P&C",
                options=RECOMMENDATIONS,
            ),
        },
        key="interview_table",
    )

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("Save Changes", key="save_interview_table", width="stretch"):
            cleaned = edited.copy()
            cleaned["department"] = "Citi Homes"
            cleaned = cleaned.drop(columns=["Sr. No"], errors="ignore")
            for _, row in cleaned.iterrows():
                if pd.isna(row.get("id")):
                    continue
                columns = [col for col in cleaned.columns if col != "id"]
                assignments = ", ".join(f"{col}=?" for col in columns)
                values = [row.get(col) for col in columns]
                execute(
                    f"UPDATE interview_evaluation SET {assignments} WHERE id=?",
                    [*values, int(row["id"])],
                )
            st.success("Changes saved successfully.")
            st.rerun()
    with c2:
        export_df = edited.drop(columns=["id"], errors="ignore")
        download_excel_button(export_df, "interview_evaluation.xlsx", "Export this table")


def show() -> None:
    hero("Interview Evaluation", "Citi Homes interview scoring for Operations / Technical and P&C evaluation.")

    added = _sync_due_interviews()
    if added:
        st.success(f"{added} due interview candidate(s) added from the recruitment tracker.")

    recruitment = fetch_df("SELECT * FROM recruitment ORDER BY id ASC")
    evaluations = fetch_df("SELECT * FROM interview_evaluation ORDER BY id DESC")

    _summary(evaluations)
    _scheduled_notes(recruitment)
    _evaluation_form(recruitment)
    _evaluation_table()
    import_panel("interview_evaluation", "Import Evaluation Data")
