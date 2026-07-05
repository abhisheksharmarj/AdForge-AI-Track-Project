# Source Code

# AdForge AI — Generative AI Advertisement Copy Generator

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-lightgrey)](https://flask.palletsprojects.com)
[![Groq](https://img.shields.io/badge/Groq-Qwen3--32B-orange)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-Educational-green)](#)

> Harnessing Generative AI to create high-converting, platform-optimised 
> advertisement copy for Google, Instagram, and Facebook — in seconds.

## About This Project

AdForge AI is a full-stack web application developed as part of an academic 
project to demonstrate the practical application of Generative AI in digital 
marketing automation.

The system integrates the Qwen3-32B large language model via the Groq API 
within a Python Flask backend to generate professional, platform-specific 
advertisement copy tailored to the user's product, target audience, tone, 
and campaign objective.

## Key Features

- Multi-platform ad generation — Google Ads, Instagram, Facebook
- Advertisement Refinement Engine with improvement scoring
- Performance Intelligence Generator with A/B testing suggestions
- 16 marketing tone options
- Content safety filtering and XSS protection
- Public deployment support via Ngrok
- 60-test automated test suite

## Project Structure

adforge/
├── app.py               # Flask backend, routes, Groq API integration
├── templates/           # Jinja2 HTML templates
├── static/              # CSS and JavaScript
├── test_app.py          # Automated test suite (60 tests)
├── ngrok_start.py       # Public deployment script
├── requirements.txt     # Dependencies
└── .env.example         # Environment variable template

## Tech Stack

- Backend  — Python 3.8+, Flask 3.0.3
- AI Model — Qwen3-32B via Groq API
- Frontend — HTML5, CSS3, Vanilla JavaScript
- Security — Bleach, python-dotenv, input validation

## Setup

git clone https://github.com/your-username/adforge-ai.git
cd adforge-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Add your GROQ_API_KEY
python app.py               # Visit http://localhost:5000

## Run Tests

python test_app.py

## Academic Submission

Institution  : [Your Institution Name]
Project      : Generative AI Application Development
Submitted by : [Your Name]
