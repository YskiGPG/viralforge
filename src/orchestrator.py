"""orchestrator — the main ViralForge agent loop.

To be built across Weeks 1-2. This is where the Anthropic SDK message loop lives:
it parses user intent, decides which Skills to load (progressive disclosure) and which
Tools to call, runs the loop until the plan is complete, and streams output back.

Adaptive routing lives here too: complex requests go through the full Skills pipeline;
simple follow-ups take a single-Skill fast path.
"""


def run(user_message: str) -> str:
    """Take a natural-language video idea and return a creative plan."""
    raise NotImplementedError("Build in Week 1 (single-flow), expand in Week 2.")
