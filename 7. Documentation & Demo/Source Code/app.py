"""
AdForge AI — Generative AI Advertisement Copy Generator
========================================================
Flask backend providing AI-powered ad generation via the Groq API.
Architecture: MVC-style with modular route handlers and service functions.
"""

import os
import re
import bleach
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-prod")

# Groq client initialised once at startup.
# The key is validated at request time so the app still boots in test/dev
# environments where the env var may not yet be set.
_groq_api_key = os.getenv("GROQ_API_KEY")
if not _groq_api_key:
    raise EnvironmentError(
        "GROQ_API_KEY not found. Please add it to your .env file."
    )
client = Groq(api_key=_groq_api_key)

MODEL = "qwen/qwen3-32b"

# ---------------------------------------------------------------------------
# Safety: blocked keywords / categories
# ---------------------------------------------------------------------------

BLOCKED_TERMS = [
    "porn", "adult content", "xxx", "nsfw", "drug dealing", "cocaine",
    "heroin", "weapon", "gun shop", "illegal", "fraud", "scam", "phishing",
    "hate", "violence", "terrorism", "child", "exploit",
]


def is_unsafe_input(text: str) -> bool:
    """Return True if any blocked term appears in the lowercased input."""
    lower = text.lower()
    return any(term in lower for term in BLOCKED_TERMS)


def sanitize(value: str, max_len: int = 500) -> str:
    """Strip HTML tags and enforce a maximum length."""
    cleaned = bleach.clean(str(value), tags=[], strip=True).strip()
    return cleaned[:max_len]


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_ad_prompt(data: dict) -> str:
    """
    Construct a structured marketing prompt that instructs the model to act as
    an expert copywriter and generate platform-specific ad content.
    """
    platforms = data.get("platforms", ["google", "instagram", "facebook"])
    platform_str = ", ".join(p.capitalize() for p in platforms)

    return f"""
<thinking>
You are an elite Digital Marketing Strategist, Senior Copywriter, Brand Consultant, and Growth Marketer.
Reason step-by-step before writing. Apply AIDA, PAS, FAB, BAB, Scarcity, Social Proof, Loss Aversion,
FOMO, Emotional Selling, Authority, and Urgency — but only where they fit naturally.
Never produce generic copy. Every line must be unique, platform-optimised, persuasive, and truthful.
</thinking>

## CAMPAIGN BRIEF

- **Product**: {data['product_name']} ({data['category']})
- **Description**: {data['description']}
- **Target Audience**: {data['target_audience']}
- **Industry**: {data['industry']}
- **USP**: {data['usp']}
- **Campaign Goal**: {data['campaign_goal']}
- **Brand Personality**: {data['brand_personality']}
- **Tone**: {data['tone']}
- **Keywords**: {data['keywords']}
- **CTA**: {data['cta']}
- **Offer / Discount**: {data['offer']}
- **Price**: {data['price']}
- **Launch Type**: {data['launch_type']}
- **Competitor**: {data['competitor']}
- **Additional Notes**: {data['notes']}
- **Selected Platforms**: {platform_str}

---

Generate the following sections using MARKDOWN. Use exact headings as shown.
Only include sections for the platforms that are selected: {platform_str}.

{"### Google Ads" if "google" in platforms else ""}
{"#### Headlines (15 unique headlines, max 30 chars each, keyword-rich, high CTR)" if "google" in platforms else ""}
{"1. ... 2. ... 3. ... 4. ... 5. ... 6. ... 7. ... 8. ... 9. ... 10. ... 11. ... 12. ... 13. ... 14. ... 15. ..." if "google" in platforms else ""}
{"#### Descriptions (4 descriptions, max 90 chars each, strong CTA, keyword-optimised)" if "google" in platforms else ""}

{"### Instagram Ads" if "instagram" in platforms else ""}
{"#### Caption 1 (storytelling hook, emojis, engagement question)" if "instagram" in platforms else ""}
{"#### Caption 2 (value-driven, relatable, brand voice)" if "instagram" in platforms else ""}
{"#### Caption 3 (FOMO or scarcity angle)" if "instagram" in platforms else ""}
{"#### Hashtags (20-25 relevant hashtags)" if "instagram" in platforms else ""}

{"### Facebook Ads" if "facebook" in platforms else ""}
{"#### Primary Text 1 (conversational, social proof, emotional trigger)" if "facebook" in platforms else ""}
{"#### Primary Text 2 (value-driven, problem-solution)" if "facebook" in platforms else ""}
{"#### Primary Text 3 (story-led, aspirational)" if "facebook" in platforms else ""}
{"#### Ad Headline" if "facebook" in platforms else ""}
{"#### Ad Description" if "facebook" in platforms else ""}

### Marketing Slogans
(5 unique slogans, under 10 words each, memorable and brandable)
1.
2.
3.
4.
5.

### Performance Tips
#### A/B Testing Ideas (4 ideas)
#### Marketing Optimisation Tips (3 tips)
#### Best CTA
#### Best Hook
#### Psychological Trigger Used
#### Suggested Audience Segment
"""


def build_refine_prompt(original: str, feedback: str) -> str:
    """Build a prompt for the Advertisement Refinement Engine."""
    return f"""
<thinking>
You are a senior copywriter and conversion rate optimisation expert.
Analyse the original advertisement below and apply the user's feedback with precision.
Reason about what marketing principles to apply before rewriting.
</thinking>

## Original Advertisement
{original}

## User Feedback
{feedback}

Respond in MARKDOWN with these exact sections:

### Improved Version
(Rewritten advertisement applying all feedback)

### Changes Made
(Bullet list of specific changes and why)

### Improvement Score
(Score out of 10 with one-sentence justification)

### Conversion Prediction
(Brief prediction of conversion impact)
"""


def build_tips_prompt(data: dict) -> str:
    """Build a standalone Performance Tips prompt."""
    return f"""
<thinking>
Act as a Growth Marketing Expert. Generate actionable, specific performance tips for this campaign.
</thinking>

## Campaign Context
- Product: {data['product_name']}
- Audience: {data['target_audience']}
- Platform(s): {', '.join(data.get('platforms', ['google']))}
- Goal: {data['campaign_goal']}
- Tone: {data['tone']}

Respond in MARKDOWN:

### A/B Testing Suggestions
(4 specific test ideas with hypothesis)

### CTA Improvements
(3 stronger CTA variants)

### SEO Suggestions
(3 keyword / copy SEO tips)

### Conversion Optimisation Tips
(3 actionable tips)

### Best Posting Times
(Platform-specific recommendations)

### Audience Recommendations
(2-3 refined audience segments to target)
"""


# ---------------------------------------------------------------------------
# Groq API service
# ---------------------------------------------------------------------------

def call_groq(prompt: str, max_tokens: int = 4096) -> str:
    """
    Send a prompt to the Groq API and return the response text.
    Raises an exception on API or network errors.
    """
    if client is None:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file and restart the server."
        )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are AdForge AI — an expert generative advertising engine. "
                    "You create platform-specific, conversion-optimised marketing copy. "
                    "Always respond in well-structured Markdown. "
                    "Never produce generic copy. Be specific, persuasive, and truthful. "
                    "Reject any requests for illegal, harmful, or fraudulent content."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.85,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Input validation helper
# ---------------------------------------------------------------------------

# Required fields for the Ad Generator (description needed for prompt)
AD_REQUIRED_FIELDS = ["product_name", "description", "target_audience", "industry", "usp", "campaign_goal", "tone"]

# Required fields for Performance Tips (no description field in that form)
TIPS_REQUIRED_FIELDS = ["product_name", "target_audience", "industry", "usp", "campaign_goal", "tone"]


def validate_inputs(form: dict, fields: list = None) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    if fields is None:
        fields = AD_REQUIRED_FIELDS
    errors = []
    for field in fields:
        if not form.get(field, "").strip():
            errors.append(f"'{field.replace('_', ' ').title()}' is required.")
    platforms = form.getlist("platforms") if hasattr(form, "getlist") else form.get("platforms", [])
    if not platforms:
        errors.append("Select at least one advertising platform.")
    return errors


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Render the main application page."""
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate_ads():
    """
    Primary endpoint: accepts campaign data and returns AI-generated ad copy.
    Validates input, checks for unsafe content, builds prompt, calls Groq.
    """
    form = request.form

    # --- Validation ---
    errors = validate_inputs(form)
    if errors:
        return jsonify({"success": False, "error": " | ".join(errors)}), 400

    # --- Safety check ---
    combined_text = " ".join([
        form.get("product_name", ""),
        form.get("description", ""),
        form.get("notes", ""),
    ])
    if is_unsafe_input(combined_text):
        return jsonify({
            "success": False,
            "error": (
                "AdForge AI cannot generate content for products or services that may be "
                "harmful, illegal, or violate ethical guidelines. Please review your inputs."
            ),
        }), 422

    # --- Build sanitised data dict ---
    platforms = form.getlist("platforms")
    data = {
        "product_name":    sanitize(form.get("product_name", ""), 100),
        "category":        sanitize(form.get("category", ""), 100),
        "description":     sanitize(form.get("description", ""), 500),
        "target_audience": sanitize(form.get("target_audience", ""), 200),
        "industry":        sanitize(form.get("industry", ""), 100),
        "usp":             sanitize(form.get("usp", ""), 300),
        "campaign_goal":   sanitize(form.get("campaign_goal", ""), 150),
        "brand_personality": sanitize(form.get("brand_personality", ""), 150),
        "tone":            sanitize(form.get("tone", "Professional"), 50),
        "keywords":        sanitize(form.get("keywords", ""), 200),
        "cta":             sanitize(form.get("cta", ""), 100),
        "offer":           sanitize(form.get("offer", ""), 150),
        "price":           sanitize(form.get("price", ""), 50),
        "launch_type":     sanitize(form.get("launch_type", ""), 100),
        "competitor":      sanitize(form.get("competitor", ""), 100),
        "notes":           sanitize(form.get("notes", ""), 300),
        "platforms":       [p for p in platforms if p in ["google", "instagram", "facebook"]],
    }

    try:
        prompt = build_ad_prompt(data)
        result = call_groq(prompt)
        return jsonify({"success": True, "content": result})
    except Exception as exc:
        app.logger.error("Groq API error: %s", exc)
        return jsonify({"success": False, "error": f"AI service error: {str(exc)}"}), 502


@app.route("/api/refine", methods=["POST"])
def refine_ad():
    """
    Refinement endpoint: accepts an existing ad and user feedback,
    returns an improved version with reasoning.
    """
    original = sanitize(request.form.get("original_ad", ""), 2000)
    feedback = sanitize(request.form.get("feedback", ""), 500)

    if not original.strip():
        return jsonify({"success": False, "error": "Please provide the advertisement to refine."}), 400
    if not feedback.strip():
        return jsonify({"success": False, "error": "Please describe how you'd like it improved."}), 400
    if is_unsafe_input(original + feedback):
        return jsonify({"success": False, "error": "Content flagged as potentially unsafe."}), 422

    try:
        prompt = build_refine_prompt(original, feedback)
        result = call_groq(prompt)
        return jsonify({"success": True, "content": result})
    except Exception as exc:
        app.logger.error("Refine API error: %s", exc)
        return jsonify({"success": False, "error": f"AI service error: {str(exc)}"}), 502


@app.route("/api/tips", methods=["POST"])
def performance_tips():
    """
    Standalone Performance Tips endpoint: returns A/B tests, CTAs,
    SEO advice, posting times, and audience segments.
    """
    form = request.form
    errors = validate_inputs(form, TIPS_REQUIRED_FIELDS)
    if errors:
        return jsonify({"success": False, "error": " | ".join(errors)}), 400

    platforms = form.getlist("platforms")
    data = {
        "product_name":    sanitize(form.get("product_name", ""), 100),
        "target_audience": sanitize(form.get("target_audience", ""), 200),
        "campaign_goal":   sanitize(form.get("campaign_goal", ""), 150),
        "tone":            sanitize(form.get("tone", "Professional"), 50),
        "platforms":       [p for p in platforms if p in ["google", "instagram", "facebook"]],
    }

    try:
        prompt = build_tips_prompt(data)
        result = call_groq(prompt, max_tokens=2048)
        return jsonify({"success": True, "content": result})
    except Exception as exc:
        app.logger.error("Tips API error: %s", exc)
        return jsonify({"success": False, "error": f"AI service error: {str(exc)}"}), 502


@app.route("/about")
def about():
    """Render the About page."""
    return render_template("about.html")


@app.route("/how-it-works")
def how_it_works():
    """Render the How It Works page."""
    return render_template("how_it_works.html")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
