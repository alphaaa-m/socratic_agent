"""The final, schema-focused prompt layer."""

OUTPUT_REQUIREMENTS = """Return JSON only, with this schema:
{
  "message": "<reply text for the student, under 120 words, with one guiding question>",
  "message_type": "guidance" | "hint",
  "target_concept": "<short concept name or null>"
}
Use "hint" when MODE is hint or worked_analogy. Otherwise use "guidance"."""
