"""Mock LLM used by the production lab."""

import random
import time


RESPONSES = {
    "default": [
        "This is a mock answer from the production lab agent.",
        "The agent is running fine. Try another question.",
        "Your request was received and processed successfully.",
    ],
    "docker": ["Docker packages an app with its dependencies so it runs the same everywhere."],
    "deploy": ["Deployment is the process of shipping code to a server or cloud platform."],
    "health": ["The agent is healthy and ready to serve traffic."],
}


def ask(question: str, delay: float = 0.1) -> str:
    """Return a deterministic mock answer after a short delay."""
    time.sleep(delay + random.uniform(0, 0.05))
    text = question.lower()
    for keyword, answers in RESPONSES.items():
        if keyword in text:
            return random.choice(answers)
    return random.choice(RESPONSES["default"])


def ask_stream(question: str):
    """Yield a mock streaming response token by token."""
    answer = ask(question)
    for word in answer.split():
        time.sleep(0.05)
        yield word + " "
