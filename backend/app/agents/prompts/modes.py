"""Instruction text for the tutor's mutually exclusive dialogue modes."""

ASK_INSTRUCTION = "Ask one guiding question at difficulty {difficulty}. Build on the student's last answer."

HINT_INSTRUCTIONS = {
    1: "Give a nudge: point to the relevant concept. Do not give details. Then ask one question.",
    2: "Give a targeted hint: a smaller sub-question or a concrete case to examine. Then ask one question.",
    3: (
        "Give a scaffold: a partial first step or an analogy. Do not give the final result. "
        "Then ask the student to take the next step."
    ),
}

MODE_INSTRUCTIONS = {
    "worked_analogy": (
        "Solve a DIFFERENT but similar example in full, in 5 short steps. Then ask the student to "
        "apply the same steps to the original question. Do not solve the original question."
    ),
    "close": (
        "The student reached the correct reasoning. Confirm it in 2 sentences. Name the key idea "
        "in the student's words. Tell the student that they can end the session to see a summary."
    ),
}
