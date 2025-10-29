from chief.brain.prompt_presets import (
    CREW_CHIEF_PROMPT,
    INSTRUCTOR_PROMPT,
    PromptMode,
    get_prompt,
)


def test_prompt_lookup_returns_expected_strings() -> None:
    assert get_prompt(PromptMode.CREW_CHIEF) == CREW_CHIEF_PROMPT
    assert get_prompt(PromptMode.INSTRUCTOR) == INSTRUCTOR_PROMPT


def test_instructor_prompt_extends_crew_prompt() -> None:
    assert INSTRUCTOR_PROMPT.startswith(CREW_CHIEF_PROMPT)
    assert "Instructor mode" in INSTRUCTOR_PROMPT
