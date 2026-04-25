from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

W, H = A4
OUT = "URBS_Project_Report.pdf"

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=14*mm, bottomMargin=14*mm
)

CW = W - 36*mm   # usable content width ≈ 481 pts

# ── Palette ───────────────────────────────────────────────────
NAVY      = colors.HexColor("#0D1B3E")
STEEL     = colors.HexColor("#1E3A6E")
RULE_BLUE = colors.HexColor("#2E5BA8")
LIGHT_BG  = colors.HexColor("#F2F5FB")
WHITE_BG  = colors.HexColor("#FFFFFF")
BORDER    = colors.HexColor("#B0BCDA")
MID       = colors.HexColor("#2C2C2C")
MUTED     = colors.HexColor("#666666")
LINK_CLR  = colors.HexColor("#1A4FAA")
CAUTION_T = colors.HexColor("#7A3800")
CAUTION_B = colors.HexColor("#FFF4E5")
CAUTION_E = colors.HexColor("#D4890A")
WHITE     = colors.white

# ── Font aliases ──────────────────────────────────────────────
RB  = "Times-Bold"
RI  = "Times-Italic"
RR  = "Times-Roman"
HN  = "Helvetica"
HB  = "Helvetica-Bold"
MN  = "Courier"

# ── Style factory ─────────────────────────────────────────────
def ps(name, font=RR, size=8, color=MID, leading=None,
       align=TA_LEFT, space_after=0, space_before=0, li=0, ri=0):
    return ParagraphStyle(name, fontName=font, fontSize=size,
        textColor=color, leading=leading or size*1.35,
        alignment=align, spaceAfter=space_after,
        spaceBefore=space_before, leftIndent=li, rightIndent=ri)

S = {
    "title"  : ps("title",   RB,  19, NAVY,  24,  TA_CENTER),
    "sub"    : ps("sub",     RI,  9.5,MUTED, 14,  TA_CENTER),
    "meta"   : ps("meta",    HN,  7.5,MUTED, 11,  TA_CENTER),
    "abs_lbl": ps("abs_lbl", RB,  8.5,NAVY,  12,  TA_LEFT,  li=10),
    "abs"    : ps("abs",     RI,  8.5,MID,   13,  TA_JUSTIFY, li=10, ri=10),
    "sec_n"  : ps("sec_n",   RB,  9,  WHITE, 13,  TA_LEFT),
    "sec_t"  : ps("sec_t",   RB,  9,  WHITE, 13,  TA_LEFT),
    "th"     : ps("th",      HB,  7.8,WHITE, 11,  TA_LEFT),
    "td_h"   : ps("td_h",    HB,  8,  NAVY,  11,  TA_LEFT),
    "td"     : ps("td",      HN,  7.8,MID,   11.5,TA_JUSTIFY),
    "td_mn"  : ps("td_mn",   MN,  7,  MID,   11,  TA_LEFT),
    "m_name" : ps("m_name",  RB,  8.8,NAVY,  12,  TA_LEFT),
    "m_role" : ps("m_role",  RI,  8,  RULE_BLUE,11,TA_LEFT),
    "m_tags" : ps("m_tags",  HN,  7,  MUTED, 10,  TA_LEFT),
    "m_desc" : ps("m_desc",  HN,  7.8,MID,   11.5,TA_JUSTIFY),
    "lnk_h"  : ps("lnk_h",  RB,  8.5,NAVY,  12,  TA_LEFT),
    "lnk_url": ps("lnk_url", MN,  7,  LINK_CLR,11,TA_LEFT),
    "lnk_d"  : ps("lnk_d",  HN,  7.8,MID,   11.5,TA_JUSTIFY),
    "caut_h" : ps("caut_h",  HB,  8,  CAUTION_T,11,TA_LEFT),
    "caut_b" : ps("caut_b",  HN,  7.8,CAUTION_T,11.5,TA_JUSTIFY),
    "footer" : ps("footer",  HN,  7,  MUTED, 10,  TA_LEFT),
    "footer_r": ps("footer_r",HN, 7,  MUTED, 10,  TA_RIGHT),
    "badge"  : ps("badge",   HB,  6.5,WHITE,  9,  TA_CENTER),
    "mid_blue": ps("mid_blue",HB,  7.5,RULE_BLUE,11,TA_CENTER),
}

# ── Helpers ───────────────────────────────────────────────────
def sp(n=4):   return Spacer(1, n)
def hrule(t=1.4, c=NAVY):
    return HRFlowable(width="100%", thickness=t, color=c, spaceAfter=0)
def thinrule():
    return HRFlowable(width="100%", thickness=0.4, color=BORDER, spaceAfter=0)

def sec(num, title):
    t = Table(
        [[Paragraph(f"{num}.", S["sec_n"]),
          Paragraph(title.upper(), S["sec_t"])]],
        colWidths=[9*mm, CW - 9*mm]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), STEEL),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t

def footer_row(n, total=3):
    """Pinned footer — left text flush left, page number flush right."""
    t = Table(
        [[Paragraph("Unified Resource Booking System  ·  Group 25", S["footer"]),
          Paragraph(f"Page {n} of {total}", S["footer_r"])]],
        colWidths=[CW * 0.65, CW * 0.35]
    )
    t.setStyle(TableStyle([
        ("LEFTPADDING",   (0,0),(0,0), 0),    # ← flush left
        ("RIGHTPADDING",  (1,0),(1,0), 0),    # → flush right
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
    ]))
    return t

def base_table(data, widths, row_bgs=None):
    """Standard section table with navy header, alternating rows, grid."""
    bgs = row_bgs or [LIGHT_BG, WHITE_BG]
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), bgs),
        ("GRID",          (0,0), (-1,-1), 0.35, BORDER),
        ("LINEABOVE",     (0,1), (-1,1),  0.9,  STEEL),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 1 — TITLE · ABSTRACT · TECH STACK · PRIVILEGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story = []

story += [
    sp(3),
    Paragraph("Unified Resource Booking System", S["title"]),
    sp(2),
    hrule(1.5, NAVY),
    sp(3),
    Paragraph("Database Systems Course Project  ·  Group 25", S["sub"]),
    Paragraph(
        "Sahaj Jhamb (Group Leader)  ·  Arihant Bansal  ·  Tejas Bhat  ·  "
        "Amrit Kumar Ghoshal  ·  Pranav Prafulla Aherrao  ·  Nikshay Jain",
        S["meta"]),
    sp(5),
    hrule(0.4, BORDER),
    sp(5),
    Paragraph("Abstract", S["abs_lbl"]),
    sp(2),
    Paragraph(
        "This project presents a functional, full-stack web platform designed to streamline "
        "and bring transparency to the booking of shared campus resources — classrooms, "
        "laboratories, equipment, and seminar halls — for classes, evaluations, meetings, and "
        "departmental activities. The system manages submission, routing, and multi-faculty "
        "approval of booking requests through a structured role-based workflow, eliminating "
        "scheduling conflicts and manual coordination overhead while providing real-time status "
        "visibility to all stakeholders.",
        S["abs"]),
    sp(7),
]

# §1 Tech Stack
story += [sec("1", "System Overview — Technology Stack"), sp(5)]

stack = [
    [Paragraph(h, S["th"]) for h in ["Layer", "Technology", "Description"]],
    [Paragraph("Frontend", S["td_h"]),
     Paragraph("HTML5 · CSS3 · Bootstrap 5 · JavaScript", S["td"]),
     Paragraph("Seven Jinja2 templates (login, signup, dashboard, booking form, faculty dashboard, "
               "admin panel, summary) with Bootstrap 5 responsive layout. Client-side JS handles "
               "form validation, password-match indicator, date-floor, and dynamic approval hints.", S["td"])],
    [Paragraph("Backend", S["td_h"]),
     Paragraph("Python 3 · Flask · SQLAlchemy ORM · Gunicorn · WhiteNoise", S["td"]),
     Paragraph("22 Flask routes protected by three role decorators. Gunicorn is the production "
               "WSGI server on Render. WhiteNoise middleware is mounted directly on the WSGI app "
               "to serve /static/ files from Gunicorn without a separate web server or CDN.", S["td"])],
    [Paragraph("Database", S["td_h"]),
     Paragraph("PostgreSQL — Render Managed Cloud", S["td"]),
     Paragraph("Eleven-table schema with FK constraints and ENUM types. Developed and tested locally "
               "using a raw SQL schema, then migrated to a cloud-hosted PostgreSQL instance on Render "
               "for production. SQLAlchemy ORM keeps the codebase database-agnostic.", S["td"])],
    [Paragraph("Deployment", S["td_h"]),
     Paragraph("Render · render.yaml · Environment Variables", S["td"]),
     Paragraph("Declared via render.yaml. DATABASE_URL, SECRET_KEY, and ANTHROPIC_API_KEY are "
               "injected as Render environment variables — nothing hardcoded. db.create_all() "
               "initialises tables at startup; seed.py populates demo data once.", S["td"])],
    [Paragraph("AI Feature", S["td_h"]),
     Paragraph("Anthropic Claude API — auxiliary, read-only", S["td"]),
     Paragraph("Booking statistics are queried from PostgreSQL and sent to claude-sonnet-4-6 for "
               "a natural-language summary. Strictly read-only. Falls back to a deterministic "
               "rule-based summary when the API key is absent.", S["td"])],
]
story += [base_table(stack, [27*mm, 53*mm, None]), sp(8)]

# §2 Privileges
story += [sec("2", "User Roles & Privileges"), sp(5)]

privs = [
    [Paragraph(h, S["th"]) for h in ["Role", "Credentials", "Capabilities", "Restrictions"]],
    [Paragraph("Student", S["td_h"]),
     Paragraph("alice@college.edu\npass123", S["td_mn"]),
     Paragraph("Register, log in, browse resources, submit bookings, view own booking history "
               "with per-faculty approval progress and rejection reasons.", S["td"]),
     Paragraph("Cannot view others' bookings, access admin panel, faculty dashboard, "
               "or summary page. No cancellation.", S["td"])],
    [Paragraph("Faculty", S["td_h"]),
     Paragraph("bob@college.edu\npass123", S["td_mn"]),
     Paragraph("All student rights plus Faculty Approval Dashboard: view pending requests for "
               "assigned resources, approve/reject with reason, view personal action history.", S["td"]),
     Paragraph("Cannot manage resources, configure rules, assign faculty, or act outside "
               "assigned resources.", S["td"])],
    [Paragraph("augsd\n(Super Admin)", S["td_h"]),
     Paragraph("augsd@college.edu\naugsd123", S["td_mn"]),
     Paragraph("Full access: add/toggle resources, set ANY/ALL rules per resource, manage "
               "faculty assignments, override any booking, view all bookings system-wide, "
               "access Summary and AI Insights.", S["td"]),
     Paragraph("No restrictions. Only role with Booking Summary tab visibility.", S["td"])],
]
story += [base_table(privs, [22*mm, 30*mm, 70*mm, None]), sp(6)]

story += [thinrule(), sp(3), footer_row(1), sp(2)]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 2 — TEAM CONTRIBUTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(PageBreak())

story += [
    sp(3),
    hrule(1.5, NAVY),
    sp(5),
    sec("3", "Team Member Contributions"),
    sp(6),
]

members = [
    dict(
        name="Sahaj Jhamb", leader=True,
        role="ER Diagram & Normalisation · Project Lead",
        tags="ER Design  ·  3NF Normalisation  ·  System Architecture  ·  Integration",
        desc=(
            "Designed the complete ER diagram covering all 11 entities: departments, roles, users, "
            "resource types, resources, time slots, bookings, approval rules, faculty mappings, "
            "approvals, and usage logs. Applied 3NF normalisation — separating ResourceApprovalRule "
            "and ResourceFacultyMapping into independent tables directly enabled the ANY/ALL approval "
            "engine without redundancy. As group leader, coordinated all module handoffs, enforced "
            "naming consistency across SQL schema, ORM models, routes and templates, and managed "
            "end-to-end integration."
        ),
    ),
    dict(
        name="Arihant Bansal", leader=False,
        role="Triggers & Stored Procedures",
        tags="BEFORE INSERT Trigger  ·  Stored Procedures  ·  SQL View  ·  Conflict Detection",
        desc=(
            "Implemented database-level automation: (1) prevent_double_booking — a BEFORE INSERT "
            "trigger raising SQLSTATE '45000' when the same resource, slot, and date already holds "
            "a pending or approved booking. (2) GetBookingsByResource(p_resource_id) — a stored "
            "procedure joining bookings with users, time_slots, and resources for resource-specific "
            "lookups, demonstrated live on the Summary page. (3) booking_schedule — a six-table "
            "SQL view used across the dashboard and summary."
        ),
    ),
    dict(
        name="Tejas Bhat", leader=False,
        role="Backend Engineering & Cloud Deployment",
        tags="Flask  ·  SQLAlchemy  ·  Render  ·  PostgreSQL  ·  Gunicorn  ·  WhiteNoise",
        desc=(
            "Built all 22 Flask routes: authentication, booking creation with conflict detection, "
            "faculty approval/rejection, augsd override, resource management, and AI Insights. "
            "Authored the core _process_approval_outcome() engine evaluating ANY/ALL logic on every "
            "faculty action and auto-generating UsageLog entries. Led Render deployment: render.yaml, "
            "Gunicorn WSGI config, WhiteNoise static serving, postgres:// URI fix, and full "
            "environment-variable-driven credential management."
        ),
    ),
    dict(
        name="Amrit Kumar Ghoshal", leader=False,
        role="Analytic Queries & SQL Views",
        tags="SQL Views  ·  Aggregate Queries  ·  GROUP BY  ·  Dashboard Analytics",
        desc=(
            "Designed the booking_schedule SQL view — a six-table join across bookings, users, "
            "departments, resources, resource_types, and time_slots — providing a unified reporting "
            "surface for the dashboard and summary pages. Wrote all analytic queries: total booking "
            "count, status breakdown via GROUP BY, top-N resources by frequency, and usage "
            "distribution data consumed by both the Summary page and the AI Insights endpoint "
            "as statistical context for the Claude API prompt."
        ),
    ),
    dict(
        name="Pranav Prafulla Aherrao", leader=False,
        role="SQL Schema & Constraints",
        tags="DDL Schema  ·  Foreign Keys  ·  ENUM Types  ·  Constraints  ·  DBA Privileges",
        desc=(
            "Translated the ER diagram into a production-ready SQL schema: 11 tables with primary "
            "keys, cascaded foreign-key relationships, NOT NULL and UNIQUE constraints on emails and "
            "department names, ENUM types for booking status (pending/approved/rejected/cancelled) "
            "and rule type (ANY/ALL), and DEFAULT values for timestamps and flags. Authored the DBA "
            "privilege script demonstrating three tiers: read-only, read-update (SELECT + UPDATE on "
            "status, no DDL), and full admin — with SHOW GRANTS verification."
        ),
    ),
    dict(
        name="Nikshay Jain", leader=False,
        role="Frontend Development & Documentation",
        tags="HTML5  ·  Bootstrap 5  ·  Jinja2  ·  JavaScript  ·  Documentation",
        desc=(
            "Built all seven Jinja2 templates: login with credential hints, signup with role and "
            "department dropdowns, student dashboard showing per-faculty approval progress and "
            "rejection reasons, booking form with dynamic approval hint on resource selection, "
            "faculty dashboard with pending actions and history, augsd admin panel with tabbed "
            "resource/rules/bookings management, and the augsd-only summary page. Added JS "
            "validation across all forms and authored the full project documentation."
        ),
    ),
]

# ── Equal-height 2-column card grid ──────────────────────────
# All 6 members go into ONE Table (3 rows × 2 cols).
# ReportLab equalises left/right height within each row automatically.
# Card styling is applied to each cell — no nested tables.

HALF = CW / 2   # each column width

def member_cell(m):
    """Returns a list of Paragraphs/Spacers to fill one table cell."""
    parts = []
    if m["leader"]:
        # name + LEADER badge side by side via a mini table
        badge_w = 60
        name_w  = HALF - badge_w - 18 - 8   # cell padding 9 each side = 18
        bdata   = [[Paragraph(m["name"], S["m_name"]),
                    Paragraph("GROUP LEADER", S["badge"])]]
        bt = Table(bdata, colWidths=[name_w, badge_w])
        bt.setStyle(TableStyle([
            ("BACKGROUND",    (1,0),(1,0), RULE_BLUE),
            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(0,0),   0),
            ("RIGHTPADDING",  (0,0),(0,0),   2),
            ("LEFTPADDING",   (1,0),(1,0),   3),
            ("RIGHTPADDING",  (1,0),(1,0),   3),
            ("TOPPADDING",    (1,0),(1,0),   2),
            ("BOTTOMPADDING", (1,0),(1,0),   2),
            ("ROUNDEDCORNERS",[3]),
        ]))
        parts.append(bt)
    else:
        parts.append(Paragraph(m["name"], S["m_name"]))
    parts.append(Paragraph(m["role"], S["m_role"]))
    parts.append(Spacer(1, 3))
    parts.append(HRFlowable(width="100%", thickness=0.4, color=BORDER))
    parts.append(Spacer(1, 3))
    parts.append(Paragraph(m["tags"], S["m_tags"]))
    parts.append(Spacer(1, 4))
    parts.append(Paragraph(m["desc"], S["m_desc"]))
    return parts

# Build the 3×2 grid as a single flat Table
grid_data = []
grid_cmds = [
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ("TOPPADDING",    (0,0), (-1,-1), 9),
    ("BOTTOMPADDING", (0,0), (-1,-1), 9),
    ("LEFTPADDING",   (0,0), (-1,-1), 9),
    ("RIGHTPADDING",  (0,0), (-1,-1), 9),
    ("GRID",          (0,0), (-1,-1), 0.4, BORDER),
    # Top accent line for each cell (LINEABOVE on every row including row 0)
    ("LINEABOVE",     (0,0), (0,0),   2.0, STEEL),
    ("LINEABOVE",     (1,0), (1,0),   2.0, STEEL),
    ("LINEABOVE",     (0,1), (0,1),   2.0, RULE_BLUE),
    ("LINEABOVE",     (1,1), (1,1),   2.0, RULE_BLUE),
    ("LINEABOVE",     (0,2), (0,2),   2.0, STEEL),
    ("LINEABOVE",     (1,2), (1,2),   2.0, STEEL),
]

row_bg_pairs = [
    (LIGHT_BG, WHITE_BG),
    (WHITE_BG, LIGHT_BG),
    (LIGHT_BG, WHITE_BG),
]
for ri, i in enumerate(range(0, 6, 2)):
    left_cell  = member_cell(members[i])
    right_cell = member_cell(members[i + 1])
    grid_data.append([left_cell, right_cell])
    lb, rb = row_bg_pairs[ri]
    grid_cmds.append(("BACKGROUND", (0, ri), (0, ri), lb))
    grid_cmds.append(("BACKGROUND", (1, ri), (1, ri), rb))

grid = Table(grid_data, colWidths=[HALF, HALF])
grid.setStyle(TableStyle(grid_cmds))
story.append(grid)

story += [sp(6), thinrule(), sp(3), footer_row(2), sp(2)]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE 3 — MODULES · LINKS · CAUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
story.append(PageBreak())

story += [
    sp(3),
    hrule(1.5, NAVY),
    sp(5),
    sec("4", "Modules Developed"),
    sp(5),
]

modules = [
    ("M1","Authentication",
     "Session-based login/signup with email uniqueness check, 6-char password minimum, and "
     "role-restricted self-registration (augsd via seed.py only). Three route decorators "
     "(login_required, faculty_required, augsd_required) enforce access control on all routes."),
    ("M2","Resource Booking",
     "Core booking flow: resource/slot/date selection with server-side conflict detection. "
     "Creates one Approval row per mapped faculty for approval-required resources (status=pending), "
     "or immediately approves and logs usage otherwise. Form dynamically shows rule type + faculty count."),
    ("M3","Approval Engine",
     "_process_approval_outcome() re-evaluates status after every faculty action using the "
     "resource's ANY/ALL rule. A single rejection immediately sets the booking to rejected and "
     "stores the reason on the Booking record for display to the requesting user."),
    ("M4","Faculty Dashboard",
     "Faculty-exclusive view of pending approvals for assigned resources only — full booking "
     "context, approve/reject form with reason field, personal action history (last 20), and "
     "assigned resource list with rule-type badge. Strict resource-level isolation."),
    ("M5","augsd Admin Panel",
     "Three-tab superuser interface: Resources (add/activate/deactivate), Rules (set ANY/ALL "
     "per resource, assign/remove faculty), Bookings (full system list with one-click override "
     "that stamps all pending Approval rows for audit consistency)."),
    ("M6","Summary & Analytics",
     "augsd-only page. Metric cards for total/approved/pending/rejected counts, top-5 resource "
     "ranking by frequency, and recent-50 booking table — all driven by SQLAlchemy GROUP BY "
     "aggregate queries (equivalent to the booking_schedule SQL view)."),
    ("M7","AI Insights",
     "Queries three stats from PostgreSQL and sends them to claude-sonnet-4-6 (Anthropic API) "
     "for a natural-language summary. HTTP errors surfaced as readable messages. Falls back to "
     "a deterministic rule-based summary when the API key is absent. Strictly read-only."),
    ("M8","Database & Integrity",
     "11-table PostgreSQL schema via SQLAlchemy ORM with FK chains, ENUM constraints, and "
     "auto-generated UsageLog on approval. db.create_all() runs at startup; seed.py populates "
     "demo data idempotently. URI prefix fix ensures Render's postgres:// works with SQLAlchemy."),
]

mod_hdr = [Paragraph(h, S["th"]) for h in ["ID", "Module", "Description"]]
mod_rows = [mod_hdr]
for mid, mname, mdesc in modules:
    mod_rows.append([
        Paragraph(mid, S["mid_blue"]),
        Paragraph(mname, S["td_h"]),
        Paragraph(mdesc, S["td"]),
    ])

mod_t = base_table(mod_rows, [10*mm, 34*mm, None],
                   row_bgs=[LIGHT_BG, WHITE_BG] * 5)
story += [mod_t, sp(8)]

# §5 Links
story += [sec("5", "Project Links & Repository"), sp(5)]

# ── Two-column links block ────────────────────────────────────
# URLs are long; split them across two lines manually inside the cell.
LHALF = CW / 2 - 2*mm

gh_content = [
    Paragraph("Source Code — GitHub Repository", S["lnk_h"]),
    sp(2),
    # Break the long URL into two chunks so it never overflows 230pt column
    Paragraph("github.com/Sahaj47/", S["lnk_url"]),
    Paragraph("unified-booking-system", S["lnk_url"]),
    sp(3),
    Paragraph(
        "Complete source code, SQL schema, seed data, render.yaml, and all Flask/"
        "HTML/CSS files. Clone and configure a .env file with PostgreSQL credentials, "
        "then run seed.py once to get started locally.",
        S["lnk_d"]),
]

live_content = [
    Paragraph("Live Deployment — Render", S["lnk_h"]),
    sp(2),
    # Break the long URL at a natural point
    Paragraph("unified-booking-system-hjhf.", S["lnk_url"]),
    Paragraph("onrender.com/login", S["lnk_url"]),
    sp(3),
    Paragraph(
        "Publicly accessible live deployment. Use the demo credentials on Page 1 "
        "to sign in as student, faculty, or augsd superuser.",
        S["lnk_d"]),
]

links_t = Table(
    [[gh_content, live_content]],
    colWidths=[LHALF, LHALF]
)
links_t.setStyle(TableStyle([
    ("BACKGROUND",    (0,0),(0,0), LIGHT_BG),
    ("BACKGROUND",    (1,0),(1,0), WHITE_BG),
    ("BOX",           (0,0),(0,0), 0.5, BORDER),
    ("BOX",           (1,0),(1,0), 0.5, BORDER),
    ("LINEABOVE",     (0,0),(0,0), 2.0, STEEL),
    ("LINEABOVE",     (1,0),(1,0), 2.0, RULE_BLUE),
    ("TOPPADDING",    (0,0),(-1,-1), 8),
    ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ("LEFTPADDING",   (0,0),(-1,-1), 9),
    ("RIGHTPADDING",  (0,0),(-1,-1), 9),
    ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ("COLPADDING",    (0,0),(-1,-1), 3),
]))
story += [links_t, sp(6)]

# ── Caution box ───────────────────────────────────────────────
caut_content = [
    Paragraph("Note — Render Free Tier Cold Start Behaviour", S["caut_h"]),
    sp(3),
    Paragraph(
        "Render's free-tier web services spin down after approximately 15 minutes of inactivity. "
        "The first visit after an idle period may take up to 30–60 seconds to load — "
        "please wait rather than refreshing immediately. If a 500 Internal Server Error appears "
        "on the very first load (caused by the process being overwhelmed at startup), "
        "a single reload after a few seconds resolves it. All subsequent requests in the session "
        "will respond promptly.",
        S["caut_b"]),
]
caut_t = Table([[caut_content]], colWidths=[CW])
caut_t.setStyle(TableStyle([
    ("BACKGROUND",    (0,0),(-1,-1), CAUTION_B),
    ("BOX",           (0,0),(-1,-1), 0.6, CAUTION_E),
    ("LINEABOVE",     (0,0),(-1,0),  2.0, CAUTION_E),
    ("TOPPADDING",    (0,0),(-1,-1), 8),
    ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ("RIGHTPADDING",  (0,0),(-1,-1), 10),
]))
story += [caut_t, sp(8)]

# ── Closing rule & footer ─────────────────────────────────────
story += [
    hrule(1.5, NAVY),
    sp(3),
    Paragraph(
        "Unified Resource Booking System  ·  Group 25  ·  Database Systems Course Project",
        S["meta"]),
    sp(6),
    thinrule(),
    sp(3),
    footer_row(3),
    sp(2),
]

doc.build(story)
print("Done →", OUT)
