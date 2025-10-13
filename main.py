import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import subprocess
import json

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === TOGGLE THIS FLAG ===
if_offline = True  # True = use Ollama (local), False = use OpenAI API

# Load env variables (if using OpenAI)
if not if_offline:
    from dotenv import load_dotenv
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Request body schema
class StoryRequest(BaseModel):
    experience_level: str
    genre: str
    characters: str
    interests: str
    user_brainstorm: str

PROMPT_TEMPLATE = """You are an expert story development consultant and creative writing coach.

INPUTS (replace these placeholders with the writer's data before calling the model):
- {experience_level}
- {genre}
- {characters}
- {interests}
- {user_brainstorm}

TASK:
Generate exactly 3 distinct story concepts tailored to the writer inputs above.

OUTPUT REQUIREMENTS (CRITICAL, must be followed exactly):
1. Output ONLY a single valid JSON object (double quotes, no trailing commas). Do NOT output any explanatory text, markdown, or commentary — only the JSON object described below.
2. The top-level JSON object must have a single key: "stories", whose value is an array of exactly 3 story objects.
3. Each story object must contain exactly the fields listed in the schema and no additional keys.

SCHEMA (required JSON structure — follow exactly):

{{
  "stories": [
    {{
      "title": "",
      "genre_subgenre": "",
      "premise": "",
      "main_characters": [
        {{
          "name": "",
          "role": "",
          "personality": "",
          "motivation": ""
        }}
      ],
      "central_conflict": "",
      "themes": [],
      "tone_and_style": "",
      "why_it_works_for_this_writer": ""
    }}
  ]
}}

VALIDATION RULES / CONTENT GUIDELINES:
- Return exactly 3 story objects in the "stories" array.
- "premise" must be 3–5 sentences and clearly state setup, stakes, and hook.
- "main_characters" must contain 2 to 4 character objects. Each character must include name, role, personality (short phrase), and motivation (short phrase).
- "themes" must be a list of 2–4 short strings (each a core theme).
- Keep each string concise and directly relevant.
- Do not include examples, placeholders, or instructional text inside the JSON values beyond the story content.
- Use natural-sounding, original, and distinct concepts — the three stories should be well-differentiated.
- Do NOT add any extra JSON keys (e.g., no "id", "notes", or "metadata") — only use the fields in the schema.

NOW produce the JSON output (no commentary, no extra text) — using the provided placeholders as context.
Ensure every story includes a non-empty 'why_it_works_for_this_writer' field.
"""


@app.post("/api/story")
async def generate_story(data: StoryRequest):
    user_prompt = PROMPT_TEMPLATE.format(
        experience_level=data.experience_level,
        genre=data.genre,
        characters=data.characters,
        interests=data.interests,
        user_brainstorm=data.user_brainstorm,
    )

    # === Offline Mode (Ollama) ===
    if if_offline:
        try:
            result = subprocess.run(
                ["ollama", "run", "llama3", user_prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120
            )
            response_text = result.stdout.strip()
            json_data = json.loads(response_text)
            return json_data
        except Exception as e:
            return {"error": f"Ollama error: {e}"}

    # === Online Mode (OpenAI) ===
    else:
        try:
            completion = client.responses.create(
                model="gpt-4o-mini",
                input=user_prompt,
            )
            response_text = completion.output_text.strip()
            json_data = json.loads(response_text)
            return json_data
        except Exception as e:
            return {"error": f"OpenAI API error: {e}"}
