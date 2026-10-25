"""SkillWallet construction intelligence Streamlit application."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from typing import Any

import streamlit as st
from PIL import Image, UnidentifiedImageError

from intelligence import (
    AIServiceError,
    analyze_crack_image,
    analyze_safety_image,
    ask_engineering_assistant,
    calculate_plan,
    demo_crack_report,
    format_inr,
    weather_advisory,
)

st.set_page_config(
    page_title="SkillWallet | Construction Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGE_OPTIONS = {"home", "features", "dashboard", "about"}
FEATURE_OPTIONS = {"safety", "cracks", "planning", "assistant"}
page = st.query_params.get("view", "home")
if page not in PAGE_OPTIONS:
    page = "home"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --ink:#102033; --muted:#647184; --navy:#061b2a; --navy-soft:#102d43;
        --orange:#ff8a1d; --orange-dark:#a95308; --paper:#f6f8fd; --pale:#edf3ff;
        --line:#e5eaf2; --white:#ffffff; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background:var(--paper); color:var(--ink); }
    header[data-testid="stHeader"] { background:transparent; }
    .block-container { padding:0 0 2.5rem; max-width:1500px; }
    h1,h2,h3,h4 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; color:var(--ink); }
    a { color:var(--orange-dark); }
    .st-key-site_nav { background:var(--navy); padding:8px 4.5%; box-shadow:0 2px 8px #07172520; }
    .st-key-site_nav [data-testid="stHorizontalBlock"] { align-items:center; gap:8px; }
    .st-key-site_nav .stButton button { min-height:36px; padding:6px 9px; border:0;
        background:transparent; color:#c6d2dd; box-shadow:none; font-size:12px; white-space:nowrap; }
    .st-key-site_nav .stButton button:hover { background:#ffffff16; color:white; border:0; }
    .st-key-nav_home button,.st-key-nav_features button,.st-key-nav_dashboard button {
        border-radius:6px; }
    .hero-wrap { padding:30px 5% 26px; text-align:center; }
    .eyebrow { display:inline-flex; align-items:center; gap:7px; padding:6px 11px; border:1px solid #f2dfc9;
        background:#fff9f2; color:#8e480a; border-radius:999px; font-size:10px; font-weight:700;
        letter-spacing:.08em; text-transform:uppercase; }
    .eyebrow-dot { width:7px; height:7px; background:var(--orange); border-radius:50%; }
    .hero-wrap h1 { max-width:850px; margin:12px auto 8px; font-size:clamp(30px,4vw,46px); line-height:1.1; }
    .hero-wrap h1 span { color:var(--orange-dark); }
    .hero-wrap h1 span[data-heading-text] { color:var(--ink)!important; }
    .hero-wrap h1 span[data-heading-text] span { color:var(--orange-dark)!important; }
    .hero-copy { max-width:700px; margin:0 auto 18px; color:var(--muted); font-size:14px; line-height:1.65; }
    .st-key-home_actions { margin:0 auto 22px; max-width:720px; }
    .hero-photo { position:relative; display:block; width:min(100%,1160px); height:clamp(250px,43vw,500px);
        margin:0 auto; overflow:hidden; text-align:left; border-radius:9px;
        background:linear-gradient(0deg,#061b2ae8 0%,#061b2a00 58%),url('https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=1800&q=85') center 54%/cover,
        #19364a; box-shadow:0 14px 30px #0a1d2a20; }
    .photo-label { position:absolute; top:16px; right:16px; padding:7px 10px; border-radius:5px;
        background:#061b2ad9; color:white; font-size:10px; font-weight:700; letter-spacing:.04em; }
    .photo-label:before { content:''; display:inline-block; width:7px; height:7px; margin-right:7px;
        background:#51cf91; border-radius:50%; }
    .photo-caption { position:absolute; left:20px; bottom:18px; color:white; }
    .photo-caption strong { display:block; font:700 18px 'Manrope',sans-serif; }
    .photo-caption span { color:#d9e3ed; font-size:12px; }
    .capability-strip { display:flex; justify-content:space-around; flex-wrap:wrap; gap:15px;
        padding:15px 4%; background:#eef3ff; color:var(--navy); border-block:1px solid #e4eaf7;
        font-size:10px; font-weight:700; letter-spacing:.035em; }
    .capability-strip span:before { content:'•'; color:var(--orange); font-size:17px; vertical-align:-1px; margin-right:7px; }
    .section-wrap { padding:30px 4.5%; }
    .section-heading { display:flex; justify-content:space-between; align-items:end; gap:20px; margin-bottom:17px; }
    .section-kicker { margin-bottom:5px; color:var(--orange-dark); font-size:10px; font-weight:700;
        letter-spacing:.12em; text-transform:uppercase; }
    .section-heading h2 { margin:0; font-size:clamp(22px,2.8vw,30px); }
    .section-heading p { max-width:440px; margin:0; color:var(--muted); font-size:12px; line-height:1.55; }
    .feature-card { height:100%; padding:18px; border:1px solid var(--line); border-radius:9px;
        background:white; box-shadow:0 2px 7px #0a1d2a05; }
    .feature-icon { width:38px; height:38px; display:grid; place-items:center; border-radius:6px;
        background:#e8efff; color:var(--navy); font-size:19px; margin-bottom:15px; }
    .feature-tag { display:inline-block; color:#334155; background:#edf2fa; padding:3px 7px; font-size:9px;
        font-weight:700; letter-spacing:.035em; text-transform:uppercase; }
    .feature-card h3 { margin:8px 0 6px; font-size:16px; }
    .feature-card p { min-height:57px; margin:0 0 13px; color:var(--muted); font-size:11px; line-height:1.55; }
    .feature-card a { display:flex; justify-content:space-between; align-items:center; padding-top:10px;
        border-top:1px solid #eef1f5; color:var(--orange-dark); text-decoration:none; font-size:10px; font-weight:700; }
    .dashboard-head { padding:24px 4% 16px; }
    .dashboard-head h1 { margin:5px 0; font-size:30px; }
    .dashboard-head p { margin:0; max-width:760px; color:var(--muted); font-size:13px; line-height:1.6; }
    .status-bar { padding:9px 4%; display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;
        background:#edf3ff; color:#334155; font-size:10px; }
    .status-dot { color:var(--orange-dark); font-weight:700; }
    .dashboard-content { padding:0 4% 32px; }
    .page-header { margin:0 0 16px; }
    .page-header h2 { margin:4px 0; font-size:24px; }
    .page-header p { margin:0; color:var(--muted); font-size:12px; }
    .st-key-feature_navigation div[role="radiogroup"] { gap:5px; }
    section[data-testid="stSidebar"] { width:240px!important; min-width:240px!important;
        max-width:240px!important; background:var(--navy); border-right:1px solid #18354b; }
    [data-testid="stSidebar"] :is(p,span,label,div,h1,h2,h3,h4,h5,h6,li,strong) { color:#e8eff5; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#aab9c6; font-size:11px; }
    [data-testid="stSidebar"] input { color:#fff; background:#102d43; }
    [data-testid="stSidebar"] h2 { font-size:16px; }
    div[data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:1rem; border-radius:9px; }
    div[data-testid="stMetricLabel"] { color:var(--muted); }
    .notice { border:1px solid #dbe4f2; background:#edf3ff; border-radius:8px; padding:.85rem 1rem;
        color:var(--ink); margin:.5rem 0 1rem; font-size:.88rem; }
    .pill { display:inline-block; border-radius:999px; padding:.32rem .72rem; font-size:.78rem;
        font-weight:700; background:#e6eee8; color:#235843; }
    .pill.warn { background:#fff1d7; color:#8e5d00; }
    .pill.danger { background:#fde5e2; color:#a83226; }
    .small-muted { color:#aab9c6; font-size:.84rem; }
    button[kind="primary"] { background:var(--orange); border-color:var(--orange); color:var(--navy); }
    button[kind="primary"]:hover { background:#ff9b3e; border-color:#ff9b3e; color:var(--navy); }
    @media (max-width:700px) {
        .st-key-site_nav { padding:7px 2%; }
        .st-key-site_nav .stButton button { padding:5px 3px; font-size:10px; }
        section[data-testid="stSidebar"] { width:min(240px,82vw)!important;
            min-width:min(240px,82vw)!important; max-width:min(240px,82vw)!important; }
        .hero-wrap { padding:23px 4% 20px; }
        .hero-copy { font-size:12px; }
        .hero-photo { height:270px; }
        .section-heading { align-items:start; flex-direction:column; gap:7px; }
        .status-bar { flex-direction:column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
active_nav_style = (
    f".st-key-nav_{page} button {{ background:#ffffff18!important; color:#fff!important; }}"
    if page in {"home", "features", "dashboard"}
    else ""
)
st.markdown(
    f"<style>{active_nav_style}</style>",
    unsafe_allow_html=True,
)


def show_pill(text: str, kind: str = "") -> None:
    st.markdown(f'<span class="pill {kind}">{text}</span>', unsafe_allow_html=True)


def navigate_to(view: str, feature: str | None = None) -> None:
    st.query_params["view"] = view
    if feature in FEATURE_OPTIONS:
        st.query_params["feature"] = feature
        st.session_state["feature_navigation"] = feature
    else:
        st.query_params.pop("feature", None)


def report_download(report: dict[str, Any], filename: str) -> None:
    st.download_button(
        "Download JSON report",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name=filename,
        mime="application/json",
        use_container_width=False,
    )


def clear_stale_image_report(report_key: str, fingerprint_key: str, image: Any) -> str | None:
    fingerprint = hashlib.sha256(image.getvalue()).hexdigest() if image else None
    if st.session_state.get(fingerprint_key) != fingerprint:
        st.session_state.pop(report_key, None)
        if fingerprint is None:
            st.session_state.pop(fingerprint_key, None)
        else:
            st.session_state[fingerprint_key] = fingerprint
    return fingerprint


def validate_site_image(image: Any) -> tuple[bool, str | None]:
    if image is None:
        return False, "Upload a JPG or PNG image to continue."
    if image.size > 12 * 1024 * 1024:
        return False, "Image exceeds the 12 MB limit."
    try:
        with Image.open(BytesIO(image.getvalue())) as decoded_image:
            decoded_image.verify()
    except Image.DecompressionBombError:
        return False, "Image dimensions exceed the safe processing limit."
    except (UnidentifiedImageError, OSError):
        return False, "The uploaded file is not a readable image. Try a valid JPG or PNG."
    return True, None


def render_safety_report(report: dict[str, Any]) -> None:
    if report["analysis_status"] == "not_performed_demo_mode":
        st.warning(report["notice"])
        st.caption("The JSON below is an empty schema example, not a finding about the uploaded photo.")
    else:
        st.warning(
            "AI-generated preliminary visual observations only. This is not a safety inspection, "
            "PPE compliance certification, or legal determination."
        )
        score = report.get("safety_score")
        first, second = st.columns(2)
        first.metric("Preliminary visual score", f"{score:.0f} / 100" if score is not None else "Not assessed")
        second.markdown("**Overall status**")
        label = str(report.get("overall_status", "Unable to assess"))
        show_pill(label, "danger" if label == "Potential concerns" else "warn")
        st.subheader("PPE observations")
        ppe_labels = {
            "helmet": "Helmet",
            "high_visibility_vest": "High-visibility vest",
            "steel_toe_boots": "Steel-toe boots",
            "safety_harness": "Safety harness",
        }
        columns = st.columns(4)
        for column, (key, title) in zip(columns, ppe_labels.items()):
            item = report["ppe_detection"][key]
            status = item.get("status", "unclear").replace("_", " ").title()
            with column:
                st.markdown(f"**{title}**")
                show_pill(status, "warn" if status in {"Unclear", "Not Assessed"} else "")
                if item.get("evidence"):
                    st.caption(item["evidence"])
        st.subheader("Visible site hazards")
        hazards = report.get("site_hazards", [])
        if not hazards:
            st.info("No hazards were returned. This does not establish that the site is hazard-free.")
        for hazard in hazards:
            with st.container(border=True):
                st.markdown(f"**{hazard.get('hazard', 'Hazard')}**")
                show_pill(str(hazard.get("severity", "Unspecified")), "danger" if hazard.get("severity") in {"High", "Critical"} else "warn")
                st.write(f"**Visible evidence:** {hazard.get('evidence', 'Not provided')}")
                st.write(f"**Suggested corrective action:** {hazard.get('corrective_remedy', 'Not provided')}")
    report_download(report, "site-safety-report.json")
    with st.expander("Full report JSON"):
        st.json(report)


def render_crack_report(report: dict[str, Any]) -> None:
    if report["analysis_status"] == "not_performed_demo_mode":
        st.warning(report["notice"])
        st.caption("The JSON below is an empty schema example, not a diagnosis or measurement.")
    else:
        st.warning(
            "AI-generated preliminary visual observations only. Width is not a field measurement; "
            "a qualified structural engineer must assess the defect and determine repairs."
        )
        first, second, third = st.columns(3)
        first.metric("Visual defect hypothesis", report.get("defect_type") or "Unable to assess")
        width = report.get("estimated_crack_width_mm")
        second.metric("Estimated width", f"{width:g} mm" if width is not None else "Not measurable")
        third.metric("Suggested urgency", report.get("urgency", "Unable to assess"))
        st.caption(report.get("width_assessment", "No scale assessment provided."))
        left, right = st.columns(2)
        with left:
            st.markdown("**Possible causes to investigate**")
            causes = report.get("root_causes", [])
            st.write(causes if causes else "No causes returned.")
        with right:
            st.markdown("**Repair options for engineer review**")
            repairs = report.get("recommended_repairs", [])
            st.write(repairs if repairs else "No repair options returned.")
        if report.get("visual_evidence"):
            st.info(report["visual_evidence"])
    report_download(report, "crack-diagnostics-report.json")
    with st.expander("Full report JSON"):
        st.json(report)


def run_safety_tab(api_key: str) -> None:
    st.subheader("Site Safety & PPE Audit")
    st.markdown(
        '<div class="notice">Upload a site photo for a preliminary visual review. OSHA rules are task-'
        "and jurisdiction-dependent; IS 456 concerns concrete structures and is not a PPE standard. "
        "No photo can establish full site compliance.</div>",
        unsafe_allow_html=True,
    )
    image = st.file_uploader(
        "Construction-site photo",
        type=["jpg", "jpeg", "png"],
        key="safety_image",
        help="JPEG or PNG, maximum 12 MB. Images are sent to Gemini only after you submit with an API key.",
    )
    clear_stale_image_report("safety_report", "safety_image_fingerprint", image)
    image_is_valid, image_error = validate_site_image(image)
    if image:
        if image_is_valid:
            st.image(image, caption="Uploaded photo", use_container_width=True)
        else:
            st.error(image_error or "The uploaded image could not be validated.")
    if st.button(
        "Analyze site photo",
        type="primary",
        key="analyze_safety",
        disabled=not image_is_valid,
    ):
        st.session_state.pop("safety_report", None)
        if not api_key:
            st.error("Gemini API key required. Enter a key in the dashboard sidebar; no analysis was performed.")
        else:
            try:
                with st.spinner("Analyzing photo with Gemini…"):
                    report = analyze_safety_image(
                        api_key, image.getvalue(), image.type, image.name
                    )
            except AIServiceError as exc:
                st.error(str(exc))
            else:
                st.session_state.safety_report = report
    report = st.session_state.get("safety_report")
    if report:
        st.divider()
        render_safety_report(report)


def run_crack_tab(api_key: str) -> None:
    st.subheader("Crack Diagnostics & Structural Integrity")
    st.markdown(
        '<div class="notice">Image-based screening cannot determine structural safety. A crack-width '
        "estimate is withheld unless the image contains a usable scale reference; an engineer must "
        "verify defect type, causes, urgency, and repair method on site.</div>",
        unsafe_allow_html=True,
    )
    image = st.file_uploader(
        "Concrete or wall surface photo",
        type=["jpg", "jpeg", "png"],
        key="crack_image",
        help="JPEG or PNG, maximum 12 MB. Include a scale reference if you need a possible width estimate.",
    )
    clear_stale_image_report("crack_report", "crack_image_fingerprint", image)
    if image:
        st.image(image, caption="Uploaded surface", use_container_width=True)
    if st.button("Assess surface image", type="primary", key="analyze_crack", disabled=image is None):
        st.session_state.pop("crack_report", None)
        if image is None:
            st.error("Select an image before assessment.")
        elif image.size > 12 * 1024 * 1024:
            st.error("Image exceeds the 12 MB limit.")
        elif not api_key:
            st.session_state.crack_report = demo_crack_report(image.name)
        else:
            try:
                st.session_state.crack_report = analyze_crack_image(
                    api_key, image.getvalue(), image.type, image.name
                )
            except AIServiceError as exc:
                st.error(str(exc))
    report = st.session_state.get("crack_report")
    if report:
        st.divider()
        render_crack_report(report)


def run_planning_tab() -> None:
    st.subheader("Planning & Real Estate Valuation")
    st.markdown(
        '<div class="notice">Planning outputs are calculated only from your inputs. They are not '
        "market appraisals, quantity-surveyor estimates, bills of quantities, or verified expenditures. "
        "Location tier is contextual only; it does not silently change the entered rates.</div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        structure = st.selectbox(
            "Structure type",
            ["Residential", "Commercial", "Industrial", "Institutional", "Other"],
        )
        area = st.number_input("Built-up area (sq ft)", min_value=0.0, value=0.0, step=100.0)
        tier = st.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
        completion = st.slider("Physical completion (%)", min_value=0, max_value=100, value=0)
    with right:
        budget_rate = st.number_input(
            "Your budget rate (INR / sq ft)", min_value=0.0, value=0.0, step=100.0,
            help="Enter a project-specific rate; no market default is assumed.",
        )
        valuation_rate = st.number_input(
            "Your valuation rate (INR / sq ft)", min_value=0.0, value=0.0, step=100.0,
            help="Enter a supported valuation basis; this app does not fetch market data.",
        )
        steel_rate = st.number_input(
            "Steel assumption (kg / sq ft)", min_value=0.0, value=0.0, step=0.1,
            help="Enter a design/quantity-surveyor coefficient; not an engineering takeoff.",
        )
        cement_rate = st.number_input(
            "Cement assumption (50 kg bags / sq ft)", min_value=0.0, value=0.0, step=0.1,
            help="Enter a project-specific coefficient; not a bill of quantities.",
        )
    st.caption(f"Context: {structure} · {tier} city. These selections do not modify your supplied rates.")
    if area <= 0:
        st.info("Enter a built-up area greater than zero to calculate planning figures.")
    else:
        figures = calculate_plan(area, completion, budget_rate, valuation_rate, steel_rate, cement_rate)
        metric_columns = st.columns(3)
        metric_columns[0].metric(
            "Total project budget", format_inr(figures["total_budget_inr"]) if budget_rate > 0 else "Enter rate"
        )
        metric_columns[1].metric(
            "Pro-rata capex proxy", format_inr(figures["pro_rata_capex_inr"]) if budget_rate > 0 else "Not available"
        )
        metric_columns[2].metric(
            "User-input asset value", format_inr(figures["market_value_inr"]) if valuation_rate > 0 else "Enter rate"
        )
        st.caption(
            "Budget = area × your budget rate. Capex is a simple completion-percentage proxy, not an "
            "accounting record. Asset value = area × your valuation rate, not an independent appraisal."
        )
        st.progress(completion / 100, text=f"Milestone progress: {completion}%")
        quantity_columns = st.columns(2)
        quantity_columns[0].metric(
            "Steel planning quantity",
            f"{figures['steel_kg']:,.1f} kg" if steel_rate > 0 else "Enter coefficient",
        )
        quantity_columns[1].metric(
            "Cement planning quantity",
            f"{figures['cement_bags']:,.1f} bags" if cement_rate > 0 else "Enter coefficient",
        )
        st.caption(
            "Steel and cement are area multiplied by the coefficients you supplied; verify against "
            "approved drawings, specifications, and a quantity survey."
        )

    st.divider()
    st.markdown("**Conceptual 3D rendering prompt**")
    location = st.text_input("Project location or setting (optional)", placeholder="e.g. Pune, Maharashtra")
    render_prompt = (
        f"Conceptual architectural visualization of a {structure.lower()} construction project, "
        + (f"{area:,.0f} sq ft built-up area, " if area > 0 else "size unspecified, ")
        + f"{tier} Indian city"
        + (f", setting: {location.strip()}" if location.strip() else "")
        + ", realistic materials, daylight, professional architectural visualization, "
        "concept art only, not a construction drawing or approved design."
    )
    st.text_area("Generated prompt", value=render_prompt, height=95, disabled=True)
    from urllib.parse import quote

    rendering_url = f"https://pollinations.ai/prompt/{quote(render_prompt, safe='')}"
    st.link_button("Open conceptual image on Pollinations AI", rendering_url)
    st.caption("The prompt is sent to a third-party service only if you open the link. No project files are sent.")


def run_assistant_tab(api_key: str) -> None:
    st.subheader("Daily Site Assistant & Weather-Aware Advisory")
    condition = st.selectbox(
        "Current weather condition", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"]
    )
    title, steps = weather_advisory(condition)
    st.markdown(f"### {title}")
    for step in steps:
        st.markdown(f"- {step}")
    st.caption(
        "General reminders only. Follow site-specific risk assessments, equipment limits, "
        "approved method statements, and competent-person direction."
    )
    st.divider()
    st.markdown("### Construction engineering assistant")
    if not api_key:
        st.info("Demo mode: the Gemini assistant is inactive. Add an API key in the sidebar to enable answers.")
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask a construction engineering question")
    if question:
        if not api_key:
            st.warning("No AI response was generated. Add a Gemini API key; your message was not sent.")
        else:
            history = [*st.session_state.chat_history, {"role": "user", "content": question}]
            try:
                answer = ask_engineering_assistant(api_key, history)
            except AIServiceError as exc:
                st.error(str(exc))
            else:
                st.session_state.chat_history.extend(
                    [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
                )
                st.rerun()


FEATURES = {
    "safety": {
        "icon": "◈",
        "tag": "IMAGE REVIEW · GEMINI OPTIONAL",
        "title": "PPE Safety Audit",
        "description": "Review uploaded site photos for preliminary PPE observations and visible hazards. Not a compliance certification.",
        "link": "Open safety audit",
    },
    "cracks": {
        "icon": "⌁",
        "tag": "STRUCTURAL SCREENING",
        "title": "Crack Diagnostics",
        "description": "Request an image-based defect hypothesis and repair considerations for a qualified engineer to review.",
        "link": "Open crack diagnostics",
    },
    "planning": {
        "icon": "▦",
        "tag": "USER-DEFINED ASSUMPTIONS",
        "title": "Cost & Valuation Planning",
        "description": "Calculate budget, completion proxy, valuation, and materials from the rates and coefficients you provide.",
        "link": "Open planning tools",
    },
    "assistant": {
        "icon": "☼",
        "tag": "WEATHER · OPTIONAL AI CHAT",
        "title": "Weather & Site Assistant",
        "description": "View general weather-condition reminders and optionally ask Gemini a construction question.",
        "link": "Open site assistant",
    },
}


def render_navigation() -> None:
    with st.container(key="site_nav"):
        columns = st.columns([1, 1, 1])
        for column, label, view in zip(
            columns,
            ("Home", "Features", "Dashboard"),
            ("home", "features", "dashboard"),
        ):
            with column:
                st.button(
                    label,
                    key=f"nav_{view}",
                    on_click=navigate_to,
                    args=(view,),
                    use_container_width=True,
                )


def render_feature_cards() -> None:
    columns = st.columns(4, gap="medium")
    for column, (feature_id, feature) in zip(columns, FEATURES.items()):
        with column:
            st.markdown(
                f"""
                <article class="feature-card">
                  <div class="feature-icon">{feature['icon']}</div>
                  <span class="feature-tag">{feature['tag']}</span>
                  <h3>{feature['title']}</h3>
                  <p>{feature['description']}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )
            st.button(
                f"{feature['link']}  →",
                key=f"open_feature_{feature_id}",
                on_click=navigate_to,
                args=("dashboard", feature_id),
                use_container_width=True,
            )


def render_home() -> None:
    st.markdown(
        """
        <section class="hero-wrap">
          <div class="eyebrow"><span class="eyebrow-dot"></span> Optional AI · Practical site workflows</div>
          <h1>Build Smarter. <span>Build Safer.</span></h1>
          <p class="hero-copy">Construction safety observations, structural image screening, project planning,
          and daily site guidance in one focused workspace.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="home_actions"):
        spacers = st.columns([1, 1.05, 1.05, 1])
        with spacers[1]:
            st.button(
                "Start Analysis  →",
                key="home_start_analysis",
                type="primary",
                on_click=navigate_to,
                args=("dashboard",),
                use_container_width=True,
            )
        with spacers[2]:
            st.button(
                "⊙  Explore Features",
                key="home_explore_features",
                on_click=navigate_to,
                args=("features",),
                use_container_width=True,
            )
    st.markdown(
        """
        <section class="hero-wrap" style="padding-top:0">
          <div class="hero-photo" role="img" aria-label="Construction site during building work">
            <span class="photo-label">Construction intelligence workspace</span>
            <div class="photo-caption">
              <strong>From field observation to informed next steps</strong>
              <span>AI assistance is optional. Professional review remains essential.</span>
            </div>
          </div>
        </section>
        <div class="capability-strip">
          <span>Streamlit modular application</span>
          <span>Optional Gemini vision and chat</span>
          <span>Transparent user-input calculations</span>
          <span>No external application database</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_features_page() -> None:
    st.markdown(
        '<section class="dashboard-head"><div class="section-kicker">Project capabilities</div>'
        '<h1>Available Field Modules</h1><p>Choose a working module to continue. Gemini-backed image analysis and chat are optional and require an API key.</p></section>',
        unsafe_allow_html=True,
    )
    render_feature_cards()
    st.markdown(
        '<section class="dashboard-content"><div class="notice">No live sensors, telemetry feeds, '
        "calibrated image measurements, or third-party market data are connected in this project. "
        "The modules shown here reflect the functionality actually implemented.</div></section>",
        unsafe_allow_html=True,
    )


def render_about_page() -> None:
    st.markdown(
        """
        <section class="dashboard-head">
          <div class="section-kicker">About this project</div>
          <h1>SkillWallet Construction Intelligence</h1>
          <p>A Streamlit application combining optional Gemini image/text assistance with local, transparent planning calculations and general weather reminders.</p>
        </section>
        <section class="dashboard-content">
          <div class="notice"><strong>Professional-use disclaimer.</strong> This application does not certify safety or legal/code compliance, diagnose structural condition, provide approved engineering design, establish market value, or replace qualified site inspection. AI responses may be incomplete or wrong; verify all important results independently.</div>
          <div class="notice"><strong>Data handling.</strong> There is no external application database. The Gemini key and session results stay in Streamlit session state. Uploaded images and conversation text are sent to Google only when a Gemini request is explicitly submitted.</div>
          <div class="notice"><strong>Planning figures.</strong> Budget and valuation depend only on user-entered rates. Material quantities depend on user-entered coefficients. Completion-based capital expenditure is a simple proxy, not an accounting record or verified project expenditure.</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    requested_feature = st.query_params.get("feature")
    if requested_feature in FEATURE_OPTIONS:
        st.session_state["feature_navigation"] = requested_feature
        del st.query_params["feature"]

    with st.sidebar:
        st.markdown("## 🏗️ Field Intelligence")
        st.caption("PROJECT MODULES")
        feature_ids = list(FEATURES)
        selected_feature = st.radio(
            "Select a module",
            options=feature_ids,
            format_func=lambda feature_id: FEATURES[feature_id]["title"],
            key="feature_navigation",
            label_visibility="collapsed",
        )
        st.divider()
        st.markdown("### Gemini configuration")
        api_key = st.text_input(
            "Google Gemini API key",
            type="password",
            key="gemini_api_key",
            help="Used only after submitting an image analysis or assistant request.",
        ).strip()
        if api_key:
            st.caption("Key entered · not yet validated")
        else:
            st.caption("No key entered · Gemini features are inactive")

    st.markdown(
        '<div class="status-bar"><span><span class="status-dot">●</span> '
        + ("Gemini key entered (not validated)" if api_key else "Gemini key not configured")
        + '</span><span>Site data and project rates are not independently verified</span></div>'
        '<section class="dashboard-head"><div class="section-kicker">Field intelligence / dashboard</div>'
        '<h1>Welcome to SkillWallet</h1><p>Choose a project tool from the sidebar. '
        "AI is optional; your planning inputs remain visible and under your control.</p></section>",
        unsafe_allow_html=True,
    )
    feature = FEATURES[selected_feature]
    st.markdown(
        f'<section class="dashboard-content"><div class="page-header">'
        f'<div class="section-kicker">{feature["tag"]}</div><h2>{feature["title"]}</h2>'
        f'<p>{feature["description"]}</p></div></section>',
        unsafe_allow_html=True,
    )
    with st.container(key="dashboard_feature"):
        if selected_feature == "safety":
            run_safety_tab(api_key)
        elif selected_feature == "cracks":
            run_crack_tab(api_key)
        elif selected_feature == "planning":
            run_planning_tab()
        else:
            run_assistant_tab(api_key)


def main() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    render_navigation()
    if page == "dashboard":
        render_dashboard()
    elif page == "features":
        render_features_page()
    elif page == "about":
        render_about_page()
    else:
        render_home()


if __name__ == "__main__":
    main()
