"""
AdForge AI — Automated Test Suite
===================================
Tests all core functions and Flask routes without requiring
a real Groq API key. Safe to run at any time.

Usage:
    python test_app.py

All tests should print ✅ PASSED. Any ❌ FAILED indicates an issue.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Set dummy env vars BEFORE importing app so Groq client doesn't crash
# ---------------------------------------------------------------------------
os.environ.setdefault("GROQ_API_KEY", "")        # empty = client will be None
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("FLASK_ENV", "testing")

# ---------------------------------------------------------------------------
# Import app components
# ---------------------------------------------------------------------------
try:
    from app import (
        app,
        is_unsafe_input,
        sanitize,
        build_ad_prompt,
        build_refine_prompt,
        build_tips_prompt,
        validate_inputs,
        AD_REQUIRED_FIELDS,
        TIPS_REQUIRED_FIELDS,
    )
except ImportError as e:
    print(f"\n❌ Could not import app.py: {e}")
    print("   Make sure you're running this from the adforge/ directory.\n")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

PASS = "✅ PASSED"
FAIL = "❌ FAILED"
results = []


def run_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"  {status}  {name}"
    if not condition and detail:
        msg += f"\n         → {detail}"
    print(msg)
    results.append(condition)


def section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ---------------------------------------------------------------------------
# Sample valid campaign data
# ---------------------------------------------------------------------------

SAMPLE_DATA = {
    "product_name":    "NovaBrew Coffee",
    "category":        "Specialty Coffee",
    "description":     "Premium single-origin Ethiopian coffee with zero-plastic packaging.",
    "target_audience": "Remote workers aged 25-40",
    "industry":        "Food and Beverage",
    "usp":             "100% organic, single-origin, zero-plastic, 24-hour delivery",
    "campaign_goal":   "Sales / Conversions",
    "brand_personality": "Warm, adventurous",
    "tone":            "Emotional",
    "keywords":        "organic, sustainable, premium coffee",
    "cta":             "Order Now and Save 30%",
    "offer":           "30% off first order",
    "price":           "₹1,999 per month",
    "launch_type":     "New Product Launch",
    "competitor":      "Starbucks",
    "notes":           "Emphasise eco-friendly packaging.",
    "platforms":       ["google", "instagram", "facebook"],
}


# ============================================================
# SECTION 1 — Safety Filter
# ============================================================
section("1. Content Safety Filter")

run_test(
    "Blocks 'cocaine' in product name",
    is_unsafe_input("cocaine delivery service"),
)
run_test(
    "Blocks 'fraud' keyword",
    is_unsafe_input("investment fraud scheme"),
)
run_test(
    "Blocks 'porn' content",
    is_unsafe_input("adult porn website"),
)
run_test(
    "Blocks 'terrorism'",
    is_unsafe_input("terrorism support group"),
)
run_test(
    "Allows legitimate coffee brand",
    not is_unsafe_input("NovaBrew premium organic coffee"),
)
run_test(
    "Allows fashion brand",
    not is_unsafe_input("Urban Vogue sustainable fashion for young professionals"),
)
run_test(
    "Allows SaaS product",
    not is_unsafe_input("TaskFlow project management software for remote teams"),
)


# ============================================================
# SECTION 2 — Input Sanitisation
# ============================================================
section("2. Input Sanitisation (Bleach)")

result = sanitize("<script>alert('xss')</script>hello world")
run_test(
    "Strips <script> tags",
    "script" not in result.lower() and "hello world" in result,
    f"Got: {repr(result)}",
)

result2 = sanitize("<b>bold</b> text with <a href='x'>link</a>")
run_test(
    "Strips all HTML tags",
    "<" not in result2 and "bold" in result2 and "text" in result2,
    f"Got: {repr(result2)}",
)

result3 = sanitize("a" * 600, max_len=100)
run_test(
    "Enforces max_len=100",
    len(result3) == 100,
    f"Length was: {len(result3)}",
)

result4 = sanitize("  hello world  ")
run_test(
    "Strips leading/trailing whitespace",
    result4 == "hello world",
    f"Got: {repr(result4)}",
)

result5 = sanitize("<img src=x onerror=alert(1)>Safe text")
run_test(
    "Strips <img> with event handlers",
    "onerror" not in result5 and "Safe text" in result5,
    f"Got: {repr(result5)}",
)


# ============================================================
# SECTION 3 — Prompt Builders
# ============================================================
section("3. Prompt Engineering")

prompt = build_ad_prompt(SAMPLE_DATA)

run_test("Prompt contains product name",     "NovaBrew Coffee" in prompt)
run_test("Prompt contains target audience",  "Remote workers" in prompt)
run_test("Prompt contains USP",             "organic" in prompt)
run_test("Prompt contains Google Ads section", "Google Ads" in prompt)
run_test("Prompt contains Instagram section",  "Instagram" in prompt)
run_test("Prompt contains Facebook section",   "Facebook" in prompt)
run_test("Prompt contains Slogans section",    "Marketing Slogans" in prompt)
run_test("Prompt contains tone",              "Emotional" in prompt)

# Test platform filtering
data_google_only = {**SAMPLE_DATA, "platforms": ["google"]}
prompt_g = build_ad_prompt(data_google_only)
run_test("Google-only prompt excludes Instagram", "Instagram" not in prompt_g)
run_test("Google-only prompt excludes Facebook",  "Facebook"  not in prompt_g)

# Refine prompt
refine_prompt = build_refine_prompt(
    original="Buy our coffee. It is good.",
    feedback="Make it more emotional and add urgency.",
)
run_test("Refine prompt contains original ad",  "Buy our coffee" in refine_prompt)
run_test("Refine prompt contains feedback",     "emotional" in refine_prompt)
run_test("Refine prompt requests Improved Version", "Improved Version" in refine_prompt)
run_test("Refine prompt requests Improvement Score", "Improvement Score" in refine_prompt)

# Tips prompt
tips_prompt = build_tips_prompt({
    "product_name":    "NovaBrew Coffee",
    "target_audience": "Remote workers 25-40",
    "campaign_goal":   "Sales",
    "tone":            "Emotional",
    "platforms":       ["google", "instagram"],
})
run_test("Tips prompt contains A/B Testing",         "A/B Testing" in tips_prompt)
run_test("Tips prompt contains CTA Improvements",    "CTA" in tips_prompt)
run_test("Tips prompt contains Audience Recommendations", "Audience" in tips_prompt)


# ============================================================
# SECTION 4 — Input Validation
# ============================================================
section("4. Input Validation")


class MockForm(dict):
    """Minimal mock of Flask's ImmutableMultiDict for testing."""
    def getlist(self, key):
        val = self.get(key, [])
        return val if isinstance(val, list) else [val]


# Valid ad form
valid_form = MockForm({
    "product_name":    "NovaBrew",
    "description":     "Premium coffee",
    "target_audience": "Professionals",
    "industry":        "F&B",
    "usp":             "Organic",
    "campaign_goal":   "Sales",
    "tone":            "Emotional",
    "platforms":       ["google"],
})
errors = validate_inputs(valid_form, AD_REQUIRED_FIELDS)
run_test("Valid ad form passes with no errors", len(errors) == 0, str(errors))

# Missing product_name
missing_name = MockForm({**valid_form, "product_name": ""})
errors = validate_inputs(missing_name, AD_REQUIRED_FIELDS)
run_test("Missing product_name caught", any("product name" in e.lower() for e in errors))

# Missing description
missing_desc = MockForm({**valid_form, "description": ""})
errors = validate_inputs(missing_desc, AD_REQUIRED_FIELDS)
run_test("Missing description caught", any("description" in e.lower() for e in errors))

# Missing platforms
no_platform = MockForm({k: v for k, v in valid_form.items() if k != "platforms"})
errors = validate_inputs(no_platform, AD_REQUIRED_FIELDS)
run_test("Missing platform caught", any("platform" in e.lower() for e in errors))

# Tips form — no description required
valid_tips = MockForm({
    "product_name":    "NovaBrew",
    "target_audience": "Professionals",
    "industry":        "F&B",
    "usp":             "Organic",
    "campaign_goal":   "Sales",
    "tone":            "Emotional",
    "platforms":       ["google"],
})
errors = validate_inputs(valid_tips, TIPS_REQUIRED_FIELDS)
run_test("Tips form passes without description field", len(errors) == 0, str(errors))


# ============================================================
# SECTION 5 — Flask Routes
# ============================================================
section("5. Flask Routes & HTTP Responses")

with app.test_client() as client:

    # GET / → 200
    r = client.get("/")
    run_test("GET / returns 200",          r.status_code == 200, f"Got {r.status_code}")

    # GET /about → 200
    r = client.get("/about")
    run_test("GET /about returns 200",     r.status_code == 200, f"Got {r.status_code}")

    # GET /how-it-works → 200
    r = client.get("/how-it-works")
    run_test("GET /how-it-works returns 200", r.status_code == 200, f"Got {r.status_code}")

    # POST /api/generate with empty form → 400
    r = client.post("/api/generate", data={})
    run_test("POST /api/generate empty → 400", r.status_code == 400, f"Got {r.status_code}")

    # POST /api/generate with unsafe input → 422
    r = client.post("/api/generate", data={
        "product_name":    "cocaine",
        "description":     "illegal drug dealing",
        "target_audience": "anyone",
        "industry":        "illegal",
        "usp":             "cheap drugs",
        "campaign_goal":   "Sales",
        "tone":            "Bold",
        "platforms":       "google",
    })
    run_test("POST /api/generate unsafe → 422", r.status_code == 422, f"Got {r.status_code}")

    # POST /api/refine with empty fields → 400
    r = client.post("/api/refine", data={"original_ad": "", "feedback": ""})
    run_test("POST /api/refine empty → 400",   r.status_code == 400, f"Got {r.status_code}")

    # POST /api/tips with empty form → 400
    r = client.post("/api/tips", data={})
    run_test("POST /api/tips empty → 400",     r.status_code == 400, f"Got {r.status_code}")

    # POST /api/tips without description (correct — tips form has no description) → not 400 due to missing description
    r = client.post("/api/tips", data={
        "product_name":    "NovaBrew",
        "target_audience": "Professionals",
        "industry":        "F&B",
        "usp":             "Organic",
        "campaign_goal":   "Sales",
        "tone":            "Emotional",
        "platforms":       "google",
    })
    # Will be 502 (no real API key) but NOT 400 — validation passes
    run_test(
        "POST /api/tips without description not rejected by validation",
        r.status_code != 400,
        f"Got {r.status_code} — should be 502 (no API key), not 400",
    )

    # JSON response structure check
    r = client.post("/api/generate", data={})
    import json
    body = json.loads(r.data)
    run_test("Error response has 'success': false", body.get("success") is False)
    run_test("Error response has 'error' key",      "error" in body)


# ============================================================
# SECTION 6 — Page Content Verification
# ============================================================
section("6. Page Content Verification")

with app.test_client() as client:

    r = client.get("/")
    html = r.data.decode()
    run_test("Home page contains 'AdForge'",         "AdForge" in html)
    run_test("Home page contains Ad Generator tab",  "Ad Generator" in html)
    run_test("Home page contains Refine Ad tab",     "Refine Ad" in html)
    run_test("Home page contains Performance Tips",  "Performance Tips" in html)
    run_test("Home page links to /how-it-works",     "/how-it-works" in html)
    run_test("Home page links to /about",            "/about" in html)

    r = client.get("/about")
    html = r.data.decode()
    run_test("About page contains Tech Stack section", "Technology Stack" in html)
    run_test("About page mentions Qwen3-32B",          "Qwen3-32B" in html or "qwen3-32b" in html.lower())
    run_test("About page mentions Groq",               "Groq" in html)
    run_test("About page lists Core Modules",          "Core Modules" in html)
    run_test("About page mentions Bleach security",    "Bleach" in html or "bleach" in html.lower())

    r = client.get("/how-it-works")
    html = r.data.decode()
    run_test("How It Works page has step-by-step flow", "Step by Step" in html or "step" in html.lower())
    run_test("How It Works page covers Ngrok section",  "Ngrok" in html or "ngrok" in html.lower())
    run_test("How It Works page covers local testing",  "Local Testing" in html or "test" in html.lower())
    run_test("How It Works page covers data flow",      "Data Flow" in html or "flow" in html.lower())
    run_test("How It Works page mentions psychology",   "Psychology" in html or "AIDA" in html)


# ============================================================
# RESULTS SUMMARY
# ============================================================

total  = len(results)
passed = sum(results)
failed = total - passed

print(f"\n{'='*55}")
print(f"  TEST RESULTS")
print(f"{'='*55}")
print(f"  Total  : {total}")
print(f"  Passed : {passed} ✅")
print(f"  Failed : {failed} {'❌' if failed else '✅'}")
print(f"{'='*55}\n")

if failed == 0:
    print("  🎉 All tests passed! AdForge AI is ready.\n")
else:
    print(f"  ⚠️  {failed} test(s) failed. Review the output above.\n")
    sys.exit(1)
