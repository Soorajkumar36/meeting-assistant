SPEAKER_SUMMARY_PROMPT = """
You are a meeting assistant.

Below is everything spoken by a single participant in a meeting.

Tasks:
1. Summarize what this speaker discussed.
2. List any action items they committed to.
3. List any decisions they influenced.

Text:
{text}
"""

MEETING_SUMMARY_PROMPT = """
You are a meeting assistant.

Summarize the following meeting transcript.

Provide:
- Short overview
- Key topics
- Action items

Transcript:
{text}
"""
