"""Prompt context blocks. Student and retrieved text is always delimited data."""

STUDENT_CONTEXT_TEMPLATE = """STUDENT CONTEXT
- Level: {current_level} (score {level_score:.2f})
- Current difficulty: {difficulty} of 5
- Hint level: {hint_level} of 3
- Calibration: {calibration}
- Recurring misconceptions: {recurring_misconceptions}
- Preferences: {learning_preferences}"""

SUBJECT_CONTEXT_TEMPLATE = """SUBJECT CONTEXT
- Subject: {subject_name} - {subject_description}
- Core question of the session: {core_question}
- Target concepts: {target_concepts}"""

MEMORY_TEMPLATE = """CONVERSATION SUMMARY
{memory_summary}"""

NO_REFERENCE_MATERIAL = (
    "No reference material found. Do not state specific facts that you cannot verify. "
    "Ask conceptual questions."
)

REFERENCE_MATERIAL_TEMPLATE = """<reference_material>
{reference_material}
</reference_material>"""
