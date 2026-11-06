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
- Target concepts: {target_concepts}
- Isolation: this session may only teach {subject_name}. Relevant follow-ups, greetings,
  clarifications and short replies are in bounds. A question that belongs to a different
  subject is out of bounds.
- Teaching: there is no fixed topic list. Guide the student through whatever in-subject
  topic they raise, using Socratic questions rather than a complete answer."""

MEMORY_TEMPLATE = """CONVERSATION SUMMARY
{memory_summary}"""

NO_REFERENCE_MATERIAL = (
    "No course outline or reference document is attached. Teach the session subject "
    "dynamically with guiding questions. Do not give a complete answer."
)

REFERENCE_MATERIAL_TEMPLATE = """<reference_material>
{reference_material}
</reference_material>"""
