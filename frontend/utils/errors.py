from typing import Callable, Literal

import streamlit as st
from loguru import logger

DisplayLevel = Literal["error", "warning", "info"]


def show_technical_issue(
    *,
    display_message: str | None = None,
    log_message: str | None = None,
    exc: Exception | None = None,
    level: DisplayLevel = "error",
) -> None:
    """Display a generic technical issue message while logging detailed context."""
    user_copy = display_message or "We ran into a technical issue. Please try again later."
    display: Callable[[str], None] = getattr(st, level, st.error)
    display(user_copy)

    log_text = log_message or user_copy
    log = logger.opt(exception=exc) if exc else logger

    if level == "warning":
        log.warning(log_text)
    elif level == "info":
        log.info(log_text)
    else:
        log.error(log_text)
