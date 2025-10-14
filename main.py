import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from dotenv import load_dotenv

# === Gemini imports ===
import google.generativeai as genai

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === TOGGLE THIS FLAG ===
if_offline = True  # True = use Gemini (local/offline_mode section), False = use OpenAI API

# Load env variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# OpenAI fallback (if desired)
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Request body schema
class StoryRequest(BaseModel):
    experience_level: str
    genre: str
    characters: str
    interests: str
    user_brainstorm: str

PROMPT_TEMPLATE = """You are an expert story development consultant and creative writing coach, while also being an AI that only outputs valid JSON objects that are formatted

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

    # === Gemini Mode ===
    if if_offline:
        try:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(user_prompt)
            response_text = response.text.strip()

            import re, json

            # --- CLEANING STEP ---
            # Remove code fences, markdown, or any pre/post text
            cleaned = response_text
            cleaned = re.sub(r"```(?:json)?|```", "", cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r"^[^{]*", "", cleaned, flags=re.DOTALL)  # remove text before first {
            cleaned = re.sub(r"[^}]*$", "", cleaned, flags=re.DOTALL)  # remove text after last }

            print("\n=== Gemini Raw Output ===")
            print(response_text)
            print("\n=== Cleaned Text ===")
            print(cleaned)

            # --- PARSE STEP ---
            try:
                json_data = json.loads(cleaned)

                # Ensure top-level structure
                if "stories" not in json_data or not isinstance(json_data["stories"], list):
                    print("⚠️ Gemini JSON missing 'stories' key or invalid format.")
                    return {
                        "stories": [],
                        "error": "Gemini response missing 'stories' array.",
                        "raw": response_text
                    }

                return json_data

            except json.JSONDecodeError as e:
                print("⚠️ Gemini JSON decode error:", e)
                print("⚠️ Cleaned text:\n", cleaned)
                return {
                    "stories": [],
                    "error": f"Gemini returned invalid JSON: {str(e)}",
                    "raw": response_text
                }

        except Exception as e:
            print("❌ Gemini API Error:", e)
            return {
                "stories": [],
                "error": f"Gemini API error: {e}"
            }

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
