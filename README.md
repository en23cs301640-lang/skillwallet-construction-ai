# SkillWallet — Multimodal Construction Intelligence Platform

**Skill Wallet Capstone Project 1** — a Streamlit application for preliminary
construction-site image review, user-driven project planning, and weather-aware
site reminders.

The application opens on a responsive landing page inspired by the supplied
design. Use **Start Analysis** to open the field dashboard, then select one of
the implemented modules from the left sidebar. The interface uses a navy and
orange theme; the decorative landing-page construction photo is loaded from
Unsplash and falls back to a plain background if unavailable.

## What it does

- **Site Safety & PPE Audit:** Gemini can return preliminary visible observations
  for helmets, high-visibility vests, steel-toe boots, and harnesses, plus visible
  hazards and suggested corrective actions. A photo cannot establish site-wide
  PPE compliance. OSHA requirements depend on the work and jurisdiction; IS 456
  is a concrete structural code, not a PPE standard.
- **Crack Diagnostics:** Gemini can suggest a visual defect category and possible
  causes and repair options for engineer review. It must not estimate crack width
  from pixels; a width is returned only when an image contains a usable scale
  reference. The result is not a structural diagnosis.
- **Planning & Valuation:** Calculations use only the rates and quantity
  coefficients entered by the user. They do not fetch market data, infer a rate
  from the city tier, or produce an independent appraisal or bill of quantities.
  “Capex incurred” is shown as a simple area-budget-times-completion proxy, not
  an accounting record.
- **Daily Site Assistant:** Weather selections show general reminders. A Gemini
  text assistant is available when a key is supplied.
- **Concept rendering:** Generates a prompt and an optional Pollinations AI link.
  The prompt is sent to that third party only if the user opens the link.

### Demonstration mode and data handling

Without a Gemini key, image reports contain an explicit `not_performed_demo_mode`
status, null measurements/scores, and no findings. They are blank schema
demonstrations—not generated example results or assessments of the uploaded
image. A failed Gemini request is shown as an error; it is never replaced with a
demo result.

The Gemini key is entered into a password field and used for requests initiated
by the user. The app has no external application database and stores chat/report
state only in the active Streamlit session. When analysis is requested, the
uploaded image and prompt are sent to Google Gemini. Avoid entering confidential
project information unless permitted by your organization.

## Local setup

Requirements: Python 3.10 or newer.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).
Enter a Google Gemini API key in the sidebar to enable image analysis and
assistant responses. Leaving it blank keeps those modules in honest demo mode.

Run the focused helper tests:

```powershell
python -m unittest discover -s tests -v
```

## Deploy on Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app
   from the repository, select the branch, and set the main file path to
   `app.py`.
3. Deploy. Community Cloud installs the packages from `requirements.txt`.
4. Users may enter their Gemini API key in the app sidebar when they choose to
   use Gemini. Do not commit API keys or put them in source control. For a
   managed deployment, follow your organization's secret-management policy.

No database, build step, or external service is required to start the app. Gemini
analysis and the optional rendering link require internet connectivity.

## Professional-use disclaimer

This application is an informational aid, not a substitute for a competent
person's site inspection, a qualified structural engineer's assessment, an
approved method statement/design, an OSHA or other legal compliance audit, or a
professional real-estate valuation. AI output may be incomplete or incorrect.
Verify observations, measurements, risks, material quantities, and financial
decisions against site conditions, approved drawings, applicable standards, and
authoritative project records.
