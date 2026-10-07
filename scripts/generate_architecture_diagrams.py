"""
Generate publication-quality system architecture diagrams for Jinder in PNG format.
Uses matplotlib to generate clean vector-raster diagrams matching Jinder design tokens.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

OUTPUT_DIR = Path("/Users/dinhduy/hackathon/Excelerate-Skill-Bridge/Document/diagrams")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Colors matching Jinder Design Tokens
C_BG = "#FFFFFF"
C_SURFACE = "#F8F9FA"
C_CARD = "#FFFFFF"
C_INK = "#151531"
C_BODY = "#495057"
C_BORDER = "#CED4DA"
C_HAIRLINE = "#E9ECEF"
C_VIOLET = "#6868F7"
C_VIOLET_TINT = "#F0F0FE"
C_CORAL = "#F27C0D"
C_CORAL_TINT = "#FFE9C8"
C_GREEN = "#16A34A"
C_GREEN_TINT = "#DAF9D4"
C_BLUE = "#0284C7"
C_BLUE_TINT = "#E0F2FE"

def draw_rounded_box(ax, x, y, w, h, bg, border, radius=0.03, lw=1.5, zorder=2):
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius},rounding_size=0.04",
        facecolor=bg, edgecolor=border,
        linewidth=lw, zorder=zorder
    )
    ax.add_patch(box)
    return box

def draw_arrow(ax, x1, y1, x2, y2, color=C_VIOLET, lw=2.0, zorder=3, style="-|>"):
    arrow = patches.FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        mutation_scale=14,
        color=color, linewidth=lw,
        zorder=zorder
    )
    ax.add_patch(arrow)

# =====================================================================
# DIAGRAM 1: End-to-End System Architecture Overview
# =====================================================================
def generate_diagram_1():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=200)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # Header
    ax.text(0.5, 8.55, "Jinder — End-to-End System Architecture", fontsize=18, fontweight="bold", color=C_INK)
    ax.text(0.5, 8.25, "Zero-Build Vanilla ES6 Client • Pure Python REST Gateway • Continuous Mathematical Intelligence Engine • SQLite WAL", fontsize=10.5, color=C_BODY)

    # Layer 1: Client Tier
    draw_rounded_box(ax, 0.5, 6.0, 13.0, 1.8, C_VIOLET_TINT, C_VIOLET, lw=2.0)
    ax.text(0.8, 7.5, "CLIENT TIER — Zero-Build Vanilla ES6 Single-Page Application (SPA)", fontsize=11, fontweight="bold", color=C_VIOLET)
    
    components_client = [
        ("Job Seeker Feed", "Live continuous scoring\nSalary upside & gap pills", 0.8, 6.2),
        ("Comparison Tray", "Floating multi-job tray\n5-axis radar differential", 3.9, 6.2),
        ("Recruiter Talent Board", "Zero-PII candidate ranking\nSkill coverage & audit view", 7.0, 6.2),
        ("Reactive Stores", "SessionStore & CompareStore\nDOM Event Dispatcher", 10.1, 6.2),
    ]
    for title, desc, cx, cy in components_client:
        draw_rounded_box(ax, cx, cy, 2.7, 1.05, C_CARD, C_BORDER, lw=1.2)
        ax.text(cx + 0.15, cy + 0.75, title, fontsize=9.5, fontweight="bold", color=C_INK)
        ax.text(cx + 0.15, cy + 0.30, desc, fontsize=8, color=C_BODY)

    # Arrows Client -> Gateway
    for cx in [2.15, 5.25, 8.35, 11.45]:
        draw_arrow(ax, cx, 6.0, cx, 5.3, color=C_VIOLET)

    # Layer 2: API Gateway & HTTP Dispatcher
    draw_rounded_box(ax, 0.5, 4.0, 13.0, 1.3, C_CORAL_TINT, C_CORAL, lw=2.0)
    ax.text(0.8, 4.95, "SERVER & GATEWAY TIER — Pure Python HTTP Server (Port 8095)", fontsize=11, fontweight="bold", color=C_CORAL)

    components_gateway = [
        ("BaseHTTP Server", "Standard Library\nNon-blocking I/O", 0.8, 4.15),
        ("Rate Limiter", "Sliding window 60s\nIP token bucket", 3.9, 4.15),
        ("Auth & RBAC Guard", "Bearer session tokens\nRole permission check", 7.0, 4.15),
        ("Route Dispatcher", "REST JSON API\n/api/v1/* endpoints", 10.1, 4.15),
    ]
    for title, desc, cx, cy in components_gateway:
        draw_rounded_box(ax, cx, cy, 2.7, 0.7, C_CARD, C_BORDER, lw=1.2)
        ax.text(cx + 0.15, cy + 0.45, title, fontsize=9, fontweight="bold", color=C_INK)
        ax.text(cx + 0.15, cy + 0.15, desc, fontsize=7.8, color=C_BODY)

    # Arrows Gateway -> Engine & DB
    for cx in [2.15, 5.25, 8.35]:
        draw_arrow(ax, cx, 4.0, cx, 3.2, color=C_CORAL)
    draw_arrow(ax, 11.45, 4.0, 11.45, 2.4, color=C_CORAL)

    # Layer 3: Intelligence Engine (Left & Center)
    draw_rounded_box(ax, 0.5, 1.2, 9.8, 2.0, C_BLUE_TINT, C_BLUE, lw=2.0)
    ax.text(0.8, 2.85, "INTELLIGENCE ENGINE V2 — Deterministic Continuous Mathematical Scoring", fontsize=11, fontweight="bold", color=C_BLUE)

    formulas = [
        ("F-01 SMF & Fit", "Smooth skill match\nContinuous seniority", 0.8, 1.4),
        ("F-02 SGF & JRS", "Readiness severity\nParallel bridge max+0.18", 3.9, 1.4),
        ("F-03 JPI Proximity", "Job distance & pivot\nSalary logarithm ratio", 7.0, 1.4),
        ("F-04 RMS Merit", "Depth, evid, levels\nZero PII / zero CV count", 0.8, 2.1),
        ("F-05 FRS Feed", "Seeker ranking feed\nLogistic wage upside", 3.9, 2.1),
        ("F-06 TSS Search", "Recruiter talent search\nContinuous decimals", 7.0, 2.1),
    ]
    for title, desc, fx, fy in formulas:
        draw_rounded_box(ax, fx, fy, 2.7, 0.65, C_CARD, C_BORDER, lw=1.0)
        ax.text(fx + 0.12, fy + 0.40, title, fontsize=8.5, fontweight="bold", color=C_INK)
        ax.text(fx + 0.12, fy + 0.12, desc, fontsize=7.2, color=C_BODY)

    # Layer 4: Persistence Tier (Right)
    draw_rounded_box(ax, 10.5, 0.4, 3.0, 2.8, C_GREEN_TINT, C_GREEN, lw=2.0)
    ax.text(10.7, 2.85, "PERSISTENCE TIER", fontsize=11, fontweight="bold", color=C_GREEN)
    
    draw_rounded_box(ax, 10.7, 1.6, 2.6, 1.0, C_CARD, C_BORDER, lw=1.2)
    ax.text(10.85, 2.3, "SQLite 3 Database", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(10.85, 1.8, "• WAL Mode active\n• Relational tables\n• Atomic transactions", fontsize=7.8, color=C_BODY)

    draw_rounded_box(ax, 10.7, 0.5, 2.6, 0.95, C_CARD, C_BORDER, lw=1.2)
    ax.text(10.85, 1.15, "Reference Taxonomy", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(10.85, 0.7, "• ict_taxonomy.json\n• In-memory index\n• Aliases & weights", fontsize=7.8, color=C_BODY)

    # Cross arrow Intelligence Engine <-> DB
    draw_arrow(ax, 10.3, 2.0, 10.7, 2.0, color=C_BLUE, style="<|-|>")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "01_system_architecture_overview.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("Generated 01_system_architecture_overview.png")

# =====================================================================
# DIAGRAM 2: Frontend Architecture (SPA, Stores, Routing)
# =====================================================================
def generate_diagram_2():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=200)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    ax.text(0.5, 8.1, "Jinder — Frontend Client Architecture (Vanilla ES6 SPA)", fontsize=17, fontweight="bold", color=C_INK)
    ax.text(0.5, 7.8, "Zero-Framework Architecture • Pure CSS Custom Properties • Custom DOM Reactive Event Bus", fontsize=10, color=C_BODY)

    # Core Container Box
    draw_rounded_box(ax, 0.5, 0.4, 13.0, 7.2, C_SURFACE, C_HAIRLINE, lw=1.5)

    # Block 1: Entry & Design Tokens (Left)
    draw_rounded_box(ax, 0.8, 4.4, 3.6, 2.9, C_VIOLET_TINT, C_VIOLET, lw=1.5)
    ax.text(1.0, 6.95, "Application Entrypoint", fontsize=11, fontweight="bold", color=C_VIOLET)
    ax.text(1.0, 6.55, "• index.html (Strict Semantic HTML5)", fontsize=8.5, color=C_BODY)
    ax.text(1.0, 6.25, "• styles.css (Jinder Design Tokens)", fontsize=8.5, color=C_BODY)
    ax.text(1.0, 5.95, "• styles-core.css (Components & Badges)", fontsize=8.5, color=C_BODY)
    ax.text(1.0, 5.65, "• CSP Compliance (Zero inline unsafe)", fontsize=8.5, color=C_BODY)
    ax.text(1.0, 5.35, "• Inter & Plain Black Typography", fontsize=8.5, color=C_BODY)
    ax.text(1.0, 5.05, "• Viewport scaling & Mobile Safe Area", fontsize=8.5, color=C_BODY)

    # Block 2: Router & Navigation (Middle-Top)
    draw_rounded_box(ax, 4.7, 4.4, 4.3, 2.9, C_BLUE_TINT, C_BLUE, lw=1.5)
    ax.text(4.9, 6.95, "Hash Router & View Dispatcher", fontsize=11, fontweight="bold", color=C_BLUE)
    ax.text(4.9, 6.55, "• window.addEventListener('hashchange')", fontsize=8.5, color=C_BODY)
    ax.text(4.9, 6.25, "• Dynamic Route Matching (#feed, #job/:id)", fontsize=8.5, color=C_BODY)
    ax.text(4.9, 5.95, "• Role Authorization Guard (Seeker/Recruiter)", fontsize=8.5, color=C_BODY)
    ax.text(4.9, 5.65, "• Breadcrumb & Modal State Restoration", fontsize=8.5, color=C_BODY)
    ax.text(4.9, 5.35, "• Clean View Teardown & Memory Garbage Coll.", fontsize=8.5, color=C_BODY)
    ax.text(4.9, 5.05, "• Smooth Tab Transitions (zero flicker)", fontsize=8.5, color=C_BODY)

    # Block 3: Reactive State Stores (Right-Top)
    draw_rounded_box(ax, 9.3, 4.4, 3.9, 2.9, C_CORAL_TINT, C_CORAL, lw=1.5)
    ax.text(9.5, 6.95, "Reactive Client State Stores", fontsize=11, fontweight="bold", color=C_CORAL)
    ax.text(9.5, 6.55, "• SessionStore (Token, Role, Profile)", fontsize=8.5, color=C_BODY)
    ax.text(9.5, 6.25, "• CompareStore (Basket tray, 4 slots)", fontsize=8.5, color=C_BODY)
    ax.text(9.5, 5.95, "• FilterStore (Domain, Mode, Salary)", fontsize=8.5, color=C_BODY)
    ax.text(9.5, 5.65, "• LocalStorage Persistence with TTL", fontsize=8.5, color=C_BODY)
    ax.text(9.5, 5.35, "• CustomEvent('state:change') Dispatch", fontsize=8.5, color=C_BODY)
    ax.text(9.5, 5.05, "• Optimistic UI Updates & Error Rollback", fontsize=8.5, color=C_BODY)

    # Arrows from Top to UI Views
    draw_arrow(ax, 2.6, 4.4, 2.6, 3.7, color=C_VIOLET)
    draw_arrow(ax, 6.85, 4.4, 6.85, 3.7, color=C_BLUE)
    draw_arrow(ax, 11.25, 4.4, 11.25, 3.7, color=C_CORAL)

    # Block 4: UI Views and Visual Presentation Layer (Bottom)
    draw_rounded_box(ax, 0.8, 0.7, 12.4, 2.9, C_CARD, C_BORDER, lw=1.5)
    ax.text(1.0, 3.25, "UI Presentation Views & Component Hierarchies", fontsize=11, fontweight="bold", color=C_INK)

    views = [
        ("Job Seeker Feed", "JobCard, MatchBadge, SalaryUpside, SkillPillList, OneClickApply", 1.0, 0.9, 2.8, 2.0),
        ("Compare Tray & Matrix", "MultiJobBasket, RadarSeriesSVG, DimensionalDifferenceTable", 4.1, 0.9, 2.8, 2.0),
        ("Recruiter Talent Board", "CandidateCard, ZeroPIIBadge, ContinuousScore, ActionShortlist", 7.2, 0.9, 2.8, 2.0),
        ("Profile & Settings", "SkillLevelEditor, CertificationsInput, PIIIsolationSwitch", 10.3, 0.9, 2.7, 2.0),
    ]
    for title, desc, vx, vy, vw, vh in views:
        draw_rounded_box(ax, vx, vy, vw, vh, C_SURFACE, C_HAIRLINE, lw=1.2)
        ax.text(vx + 0.12, vy + 1.65, title, fontsize=9, fontweight="bold", color=C_INK)
        ax.text(vx + 0.12, vy + 0.50, desc.replace(", ", "\n• "), fontsize=7.8, color=C_BODY)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "02_frontend_architecture.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("Generated 02_frontend_architecture.png")

# =====================================================================
# DIAGRAM 3: Backend Architecture (REST, Middleware, Services)
# =====================================================================
def generate_diagram_3():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=200)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    ax.text(0.5, 8.1, "Jinder — Backend Architecture & Service Request Pipeline", fontsize=17, fontweight="bold", color=C_INK)
    ax.text(0.5, 7.8, "Pure Python Standard Library Server • Sliding Window Rate Limiting • In-Memory Caching • WAL Persistence", fontsize=10, color=C_BODY)

    # Step 1: Inbound Request (Left)
    draw_rounded_box(ax, 0.5, 2.5, 2.2, 4.8, C_VIOLET_TINT, C_VIOLET, lw=1.5)
    ax.text(0.65, 6.9, "1. Inbound HTTP", fontsize=10.5, fontweight="bold", color=C_VIOLET)
    ax.text(0.65, 6.4, "• Client Fetch Request\n• Method: GET/POST\n• /api/v1/* path\n• Bearer Authorization\n• JSON Payload\n• Client IP Header\n• User-Agent", fontsize=8.2, color=C_BODY)

    draw_arrow(ax, 2.7, 5.0, 3.2, 5.0, color=C_VIOLET)

    # Step 2: Middlewares (Col 2)
    draw_rounded_box(ax, 3.2, 2.5, 2.8, 4.8, C_CORAL_TINT, C_CORAL, lw=1.5)
    ax.text(3.35, 6.9, "2. Middleware Pipeline", fontsize=10.5, fontweight="bold", color=C_CORAL)
    ax.text(3.35, 6.3, "• CORS Header Handler\n  (Origin, Methods, Allow)\n• Sliding Rate Limiter\n  (60 req/min per IP)\n• Bearer Token Validator\n  (HMAC SHA256 / Session)\n• RBAC Permission Guard\n  (Role: Seeker vs Recruiter)\n• JSON Parsing & Sanitizer", fontsize=8.2, color=C_BODY)

    draw_arrow(ax, 6.0, 5.0, 6.5, 5.0, color=C_CORAL)

    # Step 3: Route Dispatcher & Controller (Col 3)
    draw_rounded_box(ax, 6.5, 2.5, 3.2, 4.8, C_BLUE_TINT, C_BLUE, lw=1.5)
    ax.text(6.65, 6.9, "3. Domain Services", fontsize=10.5, fontweight="bold", color=C_BLUE)
    ax.text(6.65, 6.3, "• AuthService\n  (Login, Register, Logout)\n• TalentProfileService\n  (Verified skills, levels)\n• JobCatalogService\n  (Search, filter, salary)\n• ApplicationService\n  (Apply, withdraw, review)\n• ScoringEngineCoordinator\n  (F-01..F-06 Orchestrator)", fontsize=8.2, color=C_BODY)

    draw_arrow(ax, 9.7, 5.8, 10.2, 5.8, color=C_BLUE)
    draw_arrow(ax, 9.7, 3.8, 10.2, 3.8, color=C_GREEN)

    # Step 4: Engine & Persistence (Col 4)
    draw_rounded_box(ax, 10.2, 4.8, 3.3, 2.5, C_BLUE_TINT, C_BLUE, lw=1.5)
    ax.text(10.35, 6.9, "Intelligence Engine V2", fontsize=10.5, fontweight="bold", color=C_BLUE)
    ax.text(10.35, 6.4, "• Continuous Smooth Models\n• F-01 SMF, F-02 SGF, F-03 JPI\n• F-04 RMS, F-05 FRS, F-06 TSS\n• Execution time: < 5ms", fontsize=8.2, color=C_BODY)

    draw_rounded_box(ax, 10.2, 1.8, 3.3, 2.6, C_GREEN_TINT, C_GREEN, lw=1.5)
    ax.text(10.35, 4.0, "SQLite 3 WAL Database", fontsize=10.5, fontweight="bold", color=C_GREEN)
    ax.text(10.35, 3.5, "• Transaction Isolation\n• Users, Talents, Employers\n• Jobs & Applications\n• Zero data deletion policy", fontsize=8.2, color=C_BODY)

    # Bottom Footer Note
    draw_rounded_box(ax, 0.5, 0.5, 13.0, 0.9, C_SURFACE, C_HAIRLINE, lw=1.0)
    ax.text(0.8, 1.05, "Operational Metrics:", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(2.6, 1.05, "Latency P95 < 20ms  |  Test Coverage: 729 automated tests (100% OK)  |  Deterministic Zero-Stochastic Output", fontsize=8.5, color=C_BODY)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "03_backend_architecture.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("Generated 03_backend_architecture.png")

# =====================================================================
# DIAGRAM 4: Intelligence Engine Pipeline (V2 Smooth Formulas)
# =====================================================================
def generate_diagram_4():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=200)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(0.5, 8.55, "Jinder — Intelligence Engine V2 Mathematical Scoring Pipeline", fontsize=17, fontweight="bold", color=C_INK)
    ax.text(0.5, 8.25, "Deterministic Continuous Architecture • Zero Hard Cutoffs • Zero PII Leakage • Mathematical Proof of Differentiation", fontsize=10, color=C_BODY)

    # Stage 1: Input Feature Normalization
    draw_rounded_box(ax, 0.5, 5.0, 3.8, 3.0, C_VIOLET_TINT, C_VIOLET, lw=1.5)
    ax.text(0.7, 7.6, "STAGE 1: INPUT INGESTION", fontsize=10.5, fontweight="bold", color=C_VIOLET)
    ax.text(0.7, 7.15, "Talent Vector C:", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(0.7, 6.75, "• Skill set {s_i} with levels l_i in [1..5]\n• Exact years of experience Y_C\n• Career level r_C in [0..5]\n• Certifications & Industry Awards\n• Degree level (soft boost)", fontsize=7.8, color=C_BODY)
    ax.text(0.7, 5.75, "Job Vector J:", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(0.7, 5.35, "• Must / Nice skills {s_j} with target level\n• Min/Max experience range Y_min..Y_max\n• Compensation M, Location, Mode", fontsize=7.8, color=C_BODY)

    draw_arrow(ax, 4.3, 6.5, 4.9, 6.5, color=C_VIOLET)

    # Stage 2: Reference Taxonomy Matching
    draw_rounded_box(ax, 4.9, 5.0, 3.8, 3.0, C_CORAL_TINT, C_CORAL, lw=1.5)
    ax.text(5.1, 7.6, "STAGE 2: TAXONOMY ALIGNMENT", fontsize=10.5, fontweight="bold", color=C_CORAL)
    ax.text(5.1, 7.15, "ABS ANZSCO 2026 Taxonomy:", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(5.1, 6.75, "• 6-digit Unit Group hierarchy\n• Tree distance penalty exp(-0.26*(6-c)^1.3)\n• Skill rarity weights rho in [1.0..3.0]\n• Alias canonicalization (case-insensitive)\n• Group coverage & method overlaps\n• Prep months tau & learnability factors", fontsize=7.8, color=C_BODY)

    draw_arrow(ax, 8.7, 6.5, 9.3, 6.5, color=C_CORAL)

    # Stage 3: Smooth Function Evaluation
    draw_rounded_box(ax, 9.3, 5.0, 4.2, 3.0, C_BLUE_TINT, C_BLUE, lw=1.5)
    ax.text(9.5, 7.6, "STAGE 3: CONTINUOUS FUNCTIONS", fontsize=10.5, fontweight="bold", color=C_BLUE)
    ax.text(9.5, 7.15, "Mathematical Smooth Operators:", fontsize=9, fontweight="bold", color=C_INK)
    ax.text(9.5, 6.75, "• Saturation: sat(x, a) = 1 - exp(-x/a)\n• Logistic: L(x; k) = 1 / (1 + exp(-kx))\n• Exponential Decay: exp(-0.55*|d|^1.2)\n• Power Credit: (h/n)^1.3 for h < n\n• Weighted Jaccard: sum min / sum max\n• Parallel Bridge: max(T) + 0.18*sum(others)", fontsize=7.8, color=C_BODY)

    # Flow down to 6 Formulas
    draw_arrow(ax, 2.4, 5.0, 2.4, 4.2, color=C_VIOLET)
    draw_arrow(ax, 6.8, 5.0, 6.8, 4.2, color=C_CORAL)
    draw_arrow(ax, 11.4, 5.0, 11.4, 4.2, color=C_BLUE)

    # Stage 4: Six Formula Engines (Bottom)
    draw_rounded_box(ax, 0.5, 0.8, 13.0, 3.3, C_SURFACE, C_HAIRLINE, lw=1.5)
    ax.text(0.7, 3.7, "STAGE 4: DUAL-SIDED PLATFORM FORMULAS (F-01 TO F-06)", fontsize=11, fontweight="bold", color=C_INK)

    formula_boxes = [
        ("F-01 SMF & Fit", "Skill match + 9-part\ncomposite product fit", 0.7, 1.1, 1.9),
        ("F-02 SGF & JRS", "Skill gap severity &\nJob readiness (0-100)", 2.8, 1.1, 1.9),
        ("F-03 JPI Proximity", "Job-to-job distance\n& career pivot parity", 4.9, 1.1, 1.9),
        ("F-04 RMS Merit", "Candidate benchmarking\nZero CV word counting", 7.0, 1.1, 1.9),
        ("F-05 FRS Feed", "Seeker live job feed\n0.55*fit + 0.45*FRS*", 9.1, 1.1, 1.9),
        ("F-06 TSS Search", "Recruiter talent search\n0.6*cov + 0.4*TSS", 11.2, 1.1, 2.1),
    ]
    for title, desc, bx, by, bw in formula_boxes:
        draw_rounded_box(ax, bx, by, bw, 2.3, C_CARD, C_BORDER, lw=1.2)
        ax.text(bx + 0.1, by + 1.9, title, fontsize=8.5, fontweight="bold", color=C_INK)
        ax.text(bx + 0.1, by + 1.2, desc, fontsize=7.5, color=C_BODY)
        ax.text(bx + 0.1, by + 0.4, "Output: [0..100]\nDecimal: 1 place", fontsize=7, color=C_VIOLET)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "04_intelligence_engine_pipeline.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("Generated 04_intelligence_engine_pipeline.png")

# =====================================================================
# DIAGRAM 5: Data Modeling ERD & In-Memory Taxonomy Index
# =====================================================================
def generate_diagram_5():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=200)
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    ax.text(0.5, 8.1, "Jinder — Relational Data Modeling (ERD) & Taxonomy Index", fontsize=17, fontweight="bold", color=C_INK)
    ax.text(0.5, 7.8, "SQLite 3 Normalized Schema • Foreign Keys Active • WAL Concurrency • In-Memory Inverted Index", fontsize=10, color=C_BODY)

    # Table: users
    draw_rounded_box(ax, 0.5, 4.4, 3.6, 2.8, C_VIOLET_TINT, C_VIOLET, lw=1.5)
    ax.text(0.7, 6.85, "users (Authentication)", fontsize=10.5, fontweight="bold", color=C_VIOLET)
    ax.text(0.7, 6.45, "• id: INTEGER PRIMARY KEY\n• email: TEXT UNIQUE\n• password_hash: TEXT (PBKDF2)\n• role: TEXT ('seeker'|'recruiter')\n• created_at: TIMESTAMP\n• last_login_at: TIMESTAMP", fontsize=8.2, color=C_BODY)

    # Table: talents
    draw_rounded_box(ax, 0.5, 0.8, 3.6, 3.2, C_VIOLET_TINT, C_VIOLET, lw=1.5)
    ax.text(0.7, 3.65, "talents (Candidate Profile)", fontsize=10.5, fontweight="bold", color=C_VIOLET)
    ax.text(0.7, 3.25, "• id: INTEGER PRIMARY KEY\n• user_id: INT (FK -> users.id)\n• current_role: TEXT\n• target_role: TEXT\n• level: INT (0:Intern .. 5:Principal)\n• years_experience: REAL\n• verified_skills_json: TEXT\n• certifications_json: TEXT\n• education_json: TEXT", fontsize=8.0, color=C_BODY)

    # Relation users -> talents
    draw_arrow(ax, 2.3, 4.4, 2.3, 4.0, color=C_VIOLET)

    # Table: employers
    draw_rounded_box(ax, 5.0, 4.4, 3.8, 2.8, C_CORAL_TINT, C_CORAL, lw=1.5)
    ax.text(5.2, 6.85, "employers (Enterprise)", fontsize=10.5, fontweight="bold", color=C_CORAL)
    ax.text(5.2, 6.45, "• id: INTEGER PRIMARY KEY\n• user_id: INT (FK -> users.id)\n• company_name: TEXT\n• domain: TEXT\n• website: TEXT\n• verified_status: INT\n• subscription_tier: TEXT", fontsize=8.2, color=C_BODY)

    # Relation users -> employers
    draw_arrow(ax, 4.1, 5.8, 5.0, 5.8, color=C_CORAL)

    # Table: jobs
    draw_rounded_box(ax, 5.0, 0.8, 3.8, 3.2, C_CORAL_TINT, C_CORAL, lw=1.5)
    ax.text(5.2, 3.65, "jobs (Job Vacancies)", fontsize=10.5, fontweight="bold", color=C_CORAL)
    ax.text(5.2, 3.25, "• id: INTEGER PRIMARY KEY\n• employer_id: INT (FK -> employers)\n• title: TEXT\n• anzsco_code: TEXT (6-digit)\n• min_years: REAL, max_years: REAL\n• required_skills_json: TEXT\n• salary_min: INT, salary_max: INT\n• work_mode: TEXT ('Remote'|'Hybrid')\n• city: TEXT", fontsize=8.0, color=C_BODY)

    # Relation employers -> jobs
    draw_arrow(ax, 6.9, 4.4, 6.9, 4.0, color=C_CORAL)

    # Table: applications
    draw_rounded_box(ax, 9.6, 3.8, 3.9, 3.4, C_BLUE_TINT, C_BLUE, lw=1.5)
    ax.text(9.8, 6.85, "applications (Interactions)", fontsize=10.5, fontweight="bold", color=C_BLUE)
    ax.text(9.8, 6.45, "• id: INTEGER PRIMARY KEY\n• talent_id: INT (FK -> talents.id)\n• job_id: INT (FK -> jobs.id)\n• status: TEXT ('applied'|'shortlist')\n• fit_score: REAL (Computed)\n• frs_score: REAL (Computed)\n• jrs_score: REAL (Computed)\n• created_at: TIMESTAMP\n• is_saved: INT, is_hidden: INT", fontsize=8.0, color=C_BODY)

    # Relations to applications
    draw_arrow(ax, 4.1, 2.4, 9.6, 4.5, color=C_BLUE)
    draw_arrow(ax, 8.8, 2.4, 9.6, 4.2, color=C_BLUE)

    # Reference Taxonomy (Bottom Right)
    draw_rounded_box(ax, 9.6, 0.8, 3.9, 2.6, C_GREEN_TINT, C_GREEN, lw=1.5)
    ax.text(9.8, 3.05, "ict_taxonomy.json (In-Memory)", fontsize=10.5, fontweight="bold", color=C_GREEN)
    ax.text(9.8, 2.65, "• Inverted Index by Skill & Alias\n• Skill Rarity Factor (rho: 1.0..3.0)\n• Expected Months to Learn (tau)\n• Method & Soft Competency Maps\n• Fast Lookup: O(1) hash map", fontsize=8.0, color=C_BODY)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "05_data_modeling_erd.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("Generated 05_data_modeling_erd.png")

if __name__ == "__main__":
    generate_diagram_1()
    generate_diagram_2()
    generate_diagram_3()
    generate_diagram_4()
    generate_diagram_5()
    print("All architecture diagrams successfully generated in Document/diagrams/")
