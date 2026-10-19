from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Flowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = Path(
    "/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/"
    "outputs/partner_briefs/Tender_Export_OS_Partner_Brief_Grant_Thornton.pdf"
)

NAVY = colors.HexColor("#163A5F")
BLUE = colors.HexColor("#2E74B5")
GOLD = colors.HexColor("#B78328")
BODY = colors.HexColor("#222222")
MUTED = colors.HexColor("#5C6670")
LIGHT_BLUE = colors.HexColor("#EAF2F8")
LIGHT_GRAY = colors.HexColor("#F2F4F7")
BORDER = colors.HexColor("#D9DEE5")
WHITE = colors.white

PAGE_W, PAGE_H = LETTER
LEFT = 0.85 * inch
RIGHT = 0.85 * inch
TOP = 0.86 * inch
BOTTOM = 0.72 * inch
CONTENT_W = PAGE_W - LEFT - RIGHT


def header_footer(c: canvas.Canvas, doc):
    c.saveState()
    c.setTitle("Tender Export OS - Partner Brief")
    c.setAuthor("Raghav")
    c.setSubject("Governed automation architecture and workflow overview")

    header_y = PAGE_H - 0.42 * inch
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(MUTED)
    c.drawString(LEFT, header_y, "TENDER EXPORT OS")

    footer_y = 0.34 * inch
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_W - RIGHT, footer_y, f"Page {doc.page}")
    c.restoreState()


def build_styles():
    styles = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle(
            "Kicker",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=GOLD,
            spaceAfter=6,
        ),
        "title": ParagraphStyle(
            "TitleCustom",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=32,
            leading=36,
            textColor=NAVY,
            spaceAfter=16,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=14.5,
            leading=20,
            textColor=MUTED,
            spaceAfter=16,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.8,
            leading=14,
            textColor=BODY,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=BODY,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "H1Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=BLUE,
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "flow": ParagraphStyle(
            "Flow",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=12,
            alignment=TA_CENTER,
            textColor=NAVY,
            spaceBefore=3,
            spaceAfter=10,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=BODY,
        ),
        "step": ParagraphStyle(
            "Step",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=BODY,
            leftIndent=31,
            firstLineIndent=-22,
            bulletIndent=0,
            spaceAfter=9,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.3,
            leading=14.5,
            textColor=BODY,
            leftIndent=24,
            firstLineIndent=-14,
            bulletIndent=0,
            spaceAfter=7,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.3,
            leading=12,
            textColor=NAVY,
        ),
        "table_label": ParagraphStyle(
            "TableLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=12,
            textColor=NAVY,
        ),
        "table_body": ParagraphStyle(
            "TableBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12,
            textColor=BODY,
        ),
    }


def p(text, style):
    return Paragraph(text, style)


def callout(text, styles):
    box = Table(
        [[p(text, styles["callout"])]],
        colWidths=[CONTENT_W],
        hAlign="LEFT",
    )
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return box


def step(number, title, text, styles):
    content = (
        f'<font color="#163A5F"><b>{title}</b></font> {text}'
    )
    return p(content, styles["step"],) if False else Paragraph(
        content, styles["step"], bulletText=f"{number}."
    )


def bullet(title, text, styles):
    content = (
        f'<font color="#163A5F"><b>{title}</b></font> {text}'
    )
    return Paragraph(content, styles["bullet"], bulletText="•")


class SystemArchitectureDiagram(Flowable):
    """Vector system diagram sized for one partner-brief page."""

    def __init__(self, width=CONTENT_W, height=505):
        super().__init__()
        self.width = width
        self.height = height

    @staticmethod
    def _paragraph(title, body, text_color, title_size=10, body_size=7.9):
        style = ParagraphStyle(
            "DiagramBox",
            fontName="Helvetica",
            fontSize=body_size,
            leading=body_size + 2.1,
            alignment=TA_CENTER,
            textColor=text_color,
            spaceAfter=0,
            spaceBefore=0,
        )
        return Paragraph(
            f"<b><font size='{title_size}'>{title}</font></b>"
            f"<br/><font size='{body_size}'>{body}</font>",
            style,
        )

    def _box(
        self,
        c,
        x,
        y,
        w,
        h,
        title,
        body,
        *,
        fill,
        stroke,
        text_color=BODY,
        radius=8,
        title_size=10,
        body_size=7.9,
    ):
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(1.1)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
        para = self._paragraph(
            title, body, text_color, title_size=title_size, body_size=body_size
        )
        _, ph = para.wrap(w - 14, h - 10)
        para.drawOn(c, x + 7, y + (h - ph) / 2)

    @staticmethod
    def _down_arrow(c, x1, y1, x2, y2, color=NAVY):
        c.saveState()
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1.35)
        c.line(x1, y1, x2, y2 + 6)
        path = c.beginPath()
        path.moveTo(x2, y2)
        path.lineTo(x2 - 4.2, y2 + 7)
        path.lineTo(x2 + 4.2, y2 + 7)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        c.restoreState()

    @staticmethod
    def _right_arrow(c, x1, y1, x2, y2, color=NAVY):
        c.saveState()
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1.35)
        c.line(x1, y1, x2 - 6, y2)
        path = c.beginPath()
        path.moveTo(x2, y2)
        path.lineTo(x2 - 7, y2 - 4.2)
        path.lineTo(x2 - 7, y2 + 4.2)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        c.restoreState()

    def draw(self):
        c = self.canv
        w = self.width

        source_gap = 16
        source_w = (w - source_gap) / 2
        source_y = 445
        source_h = 55

        self._box(
            c,
            0,
            source_y,
            source_w,
            source_h,
            "ChatGPT Research Boardroom",
            "Broad discovery, market and category research, advisory leads",
            fill=LIGHT_GRAY,
            stroke=BORDER,
            title_size=9.6,
            body_size=7.5,
        )
        self._box(
            c,
            source_w + source_gap,
            source_y,
            source_w,
            source_h,
            "Public Sources and Documents",
            "Tender portals, RFQ sources, PDFs, BOQs and corrigenda",
            fill=LIGHT_GRAY,
            stroke=BORDER,
            title_size=9.6,
            body_size=7.5,
        )

        evidence_x, evidence_y, evidence_w, evidence_h = 42, 360, w - 84, 63
        self._box(
            c,
            evidence_x,
            evidence_y,
            evidence_w,
            evidence_h,
            "Evidence Capture and Validation",
            "Python and Playwright: exact capture, parsing, hashing, dedupe, "
            "schema checks and readiness validation",
            fill=LIGHT_BLUE,
            stroke=BLUE,
            title_size=10.2,
            body_size=7.8,
        )
        self._down_arrow(
            c,
            source_w / 2,
            source_y,
            evidence_x + evidence_w * 0.34,
            evidence_y + evidence_h,
            BLUE,
        )
        self._down_arrow(
            c,
            source_w + source_gap + source_w / 2,
            source_y,
            evidence_x + evidence_w * 0.66,
            evidence_y + evidence_h,
            BLUE,
        )

        main_w = w - 118
        side_x = main_w + 14
        side_w = w - side_x

        hermes_y, hermes_h = 278, 62
        self._box(
            c,
            0,
            hermes_y,
            main_w,
            hermes_h,
            "Hermes Control Plane",
            "Routes work, schedules jobs, manages Kanban, blockers, approvals "
            "and owner briefs",
            fill=NAVY,
            stroke=NAVY,
            text_color=WHITE,
            title_size=11,
            body_size=8,
        )
        self._box(
            c,
            side_x,
            hermes_y,
            side_w,
            hermes_h,
            "Policy-as-Code",
            "OPA and approval rules<br/>fail closed",
            fill=colors.HexColor("#FFF4D6"),
            stroke=GOLD,
            title_size=9.3,
            body_size=7.4,
        )
        self._down_arrow(
            c,
            evidence_x + evidence_w / 2,
            evidence_y,
            main_w / 2,
            hermes_y + hermes_h,
            NAVY,
        )
        self._right_arrow(
            c,
            main_w,
            hermes_y + hermes_h / 2,
            side_x,
            hermes_y + hermes_h / 2,
            GOLD,
        )

        workflow_y, workflow_h = 178, 76
        self._box(
            c,
            0,
            workflow_y,
            main_w,
            workflow_h,
            "Specialist Workflow",
            "Radar -> Fast Kill -> Deep Read -> Supplier Proof -> "
            "Pricing / Compliance -> Pack",
            fill=colors.HexColor("#F4F7FA"),
            stroke=NAVY,
            title_size=10.5,
            body_size=7.8,
        )
        self._box(
            c,
            side_x,
            workflow_y,
            side_w,
            workflow_h,
            "Codex Artifact Runtime",
            "Parsers, spreadsheets, PDFs, bid packs and quote packs",
            fill=colors.HexColor("#E8EEF5"),
            stroke=BLUE,
            title_size=9.2,
            body_size=7.3,
        )
        self._down_arrow(
            c,
            main_w / 2,
            hermes_y,
            main_w / 2,
            workflow_y + workflow_h,
            NAVY,
        )
        self._right_arrow(
            c,
            main_w,
            workflow_y + workflow_h / 2,
            side_x,
            workflow_y + workflow_h / 2,
            BLUE,
        )

        decision_y, decision_h = 96, 58
        approval_w = (main_w - 14) * 0.54
        execution_x = approval_w + 14
        execution_w = main_w - execution_x
        self._box(
            c,
            0,
            decision_y,
            approval_w,
            decision_h,
            "Owner Approval Gate",
            "Commercial, legal, financial, DSC, classification and delivery decisions",
            fill=colors.HexColor("#FFF4D6"),
            stroke=GOLD,
            title_size=9.8,
            body_size=7.2,
        )
        self._box(
            c,
            execution_x,
            decision_y,
            execution_w,
            decision_h,
            "Execution Tracker",
            "Approved actions, receipts, follow-ups and outcomes",
            fill=colors.HexColor("#EAF5EF"),
            stroke=colors.HexColor("#3D7A57"),
            title_size=9.7,
            body_size=7.3,
        )
        self._down_arrow(
            c,
            main_w / 2,
            workflow_y,
            approval_w / 2,
            decision_y + decision_h,
            GOLD,
        )
        self._right_arrow(
            c,
            approval_w,
            decision_y + decision_h / 2,
            execution_x,
            decision_y + decision_h / 2,
            colors.HexColor("#3D7A57"),
        )

        ledger_y, ledger_h = 12, 58
        self._box(
            c,
            0,
            ledger_y,
            w,
            ledger_h,
            "Canonical State and Audit Trail",
            "Append-only canonical ledger -> Kanban | registers | Google Drive | "
            "briefs | approval and execution receipts",
            fill=colors.HexColor("#263746"),
            stroke=colors.HexColor("#263746"),
            text_color=WHITE,
            title_size=10.2,
            body_size=7.7,
        )
        self._down_arrow(
            c,
            approval_w / 2,
            decision_y,
            w * 0.38,
            ledger_y + ledger_h,
            NAVY,
        )
        self._down_arrow(
            c,
            execution_x + execution_w / 2,
            decision_y,
            w * 0.62,
            ledger_y + ledger_h,
            NAVY,
        )


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()

    frame = Frame(
        LEFT,
        BOTTOM,
        CONTENT_W,
        PAGE_H - TOP - BOTTOM,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="partner_brief_frame",
    )
    template = PageTemplate(
        id="partner_brief",
        frames=[frame],
        onPage=header_footer,
        pagesize=LETTER,
    )
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Tender Export OS - Partner Brief",
        author="Raghav",
        subject="Governed automation architecture and workflow overview",
    )
    doc.addPageTemplates([template])

    story = []

    story.extend(
        [
            p("AUTOMATION &amp; OPERATING MODEL BRIEF", styles["kicker"]),
            p("Tender Export OS", styles["title"]),
            p(
                "How I turned a fragmented tender process into a governed, "
                "evidence-led operating system",
                styles["subtitle"],
            ),
            Spacer(1, 10),
            callout(
                '<font color="#163A5F"><b>In one line:</b></font> '
                "I have built a supervised automation system that helps a tender "
                "desk find, understand, qualify and prepare opportunities - while "
                "keeping commercially or legally binding decisions in human hands.",
                styles,
            ),
            p("Why I built it", styles["h1"]),
            p(
                "Tendering is rarely one clean process. An opportunity may begin "
                "on a portal, move into a PDF or BOQ, require supplier discovery, "
                "pass through pricing and compliance checks, and finally depend on "
                "somebody remembering a deadline or approval. In practice, this "
                "work is usually spread across browser tabs, spreadsheets, emails, "
                "folders and individual memory.",
                styles["body"],
            ),
            p(
                "I wanted to create something broader than a tender scraper. The "
                "idea was to build the operating backbone of a tender and export "
                "desk: every opportunity receives a case ID, evidence, a current "
                "status, a clear next step and an audit trail. The system assists "
                "the team throughout the process, but it does not pretend that AI "
                "should make every decision.",
                styles["body"],
            ),
            PageBreak(),
            p("What the system does", styles["h1"]),
            p(
                "DISCOVER  ->  VERIFY  ->  QUALIFY  ->  ANALYSE  ->  SOURCE  "
                "->  PRICE  ->  APPROVE  ->  EXECUTE  ->  LEARN",
                styles["flow"],
            ),
            step(
                1,
                "Find and verify opportunities.",
                "The Radar layer monitors tender and export sources and identifies "
                "retenders, corrigenda, repeat-buyer patterns and potentially "
                "under-served opportunities. A public listing is treated as a lead, "
                "not as proof that the opportunity is ready to pursue.",
                styles,
            ),
            step(
                2,
                "Qualify quickly.",
                "A Fast Kill stage checks the obvious constraints - eligibility, "
                "deadline, EMD, prior experience, buyer risk and product "
                "restrictions. Clear non-starters are removed early; incomplete or "
                "ambiguous cases move to a watchlist instead of being rejected on "
                "assumptions.",
                styles,
            ),
            step(
                3,
                "Understand the documents.",
                "The Deep Read stage extracts specifications, quantities, clauses, "
                "payment terms, penalties, delivery requirements and missing "
                "information from tender PDFs, BOQs, spreadsheets, corrigenda and "
                "RFQ documents.",
                styles,
            ),
            step(
                4,
                "Prove that supply is viable.",
                "The Supplier Engine uses a 5-3-2 discipline: five candidate "
                "suppliers, three different source types and two pieces of quotation "
                "proof before final pricing is considered ready.",
                styles,
            ),
            step(
                5,
                "Build the commercial and compliance view.",
                "Pricing models the complete landed-cost waterfall rather than "
                "using a single supplier number. Export cases can include EXW, FOB "
                "and CIF scenarios, while compliance remains a clearly labelled "
                "draft until an owner or qualified expert confirms it.",
                styles,
            ),
            step(
                6,
                "Prepare the decision pack.",
                "The system assembles bid packs, pricing sheets, compliance "
                "matrices, supplier comparisons, risk notes, missing-item lists and "
                "owner briefs so that the decision is made from one coherent "
                "evidence bundle.",
                styles,
            ),
            step(
                7,
                "Stop for human approval.",
                "Before any external commitment, the system creates an approval "
                "card that shows the proposed action, value, evidence, expected "
                "benefit, risks, missing information and recovery path.",
                styles,
            ),
            step(
                8,
                "Track execution and outcome.",
                "After approval, the Execution Tracker records submissions, "
                "responses, follow-ups, deadlines, receipts and final outcomes. "
                "The purpose is to learn from real results rather than from AI "
                "confidence alone.",
                styles,
            ),
            PageBreak(),
            p("System architecture at a glance", styles["h1"]),
            p(
                "The diagram below shows how research becomes verified evidence, "
                "how Hermes routes the work, and where policy and owner approval "
                "stop autonomous execution.",
                styles["body"],
            ),
            SystemArchitectureDiagram(),
            PageBreak(),
            p("How the system is structured", styles["h1"]),
            p(
                "The architecture separates the work into clear layers so that "
                "research, execution, control and accountability do not become "
                "mixed together.",
                styles["body"],
            ),
        ]
    )

    architecture = [
        [
            p("LAYER", styles["table_header"]),
            p("ROLE IN THE OPERATING SYSTEM", styles["table_header"]),
        ],
        [
            p("Hermes control plane", styles["table_label"]),
            p(
                "Runs the operating rhythm, routes work, manages the Kanban board, "
                "surfaces blockers and approval requests, and produces the owner brief.",
                styles["table_body"],
            ),
        ],
        [
            p("Specialist agents", styles["table_label"]),
            p(
                "Separate roles handle discovery, qualification, document analysis, "
                "supplier proof, pricing, compliance, pack building, approvals and "
                "execution tracking.",
                styles["table_body"],
            ),
        ],
        [
            p("Python and browser capture", styles["table_label"]),
            p(
                "Perform repeatable evidence capture from known sources, document "
                "parsing, deduplication, validation and scheduled internal jobs.",
                styles["table_body"],
            ),
        ],
        [
            p("Codex artifact runtime", styles["table_label"]),
            p(
                "Produces and tests practical outputs: spreadsheets, PDFs, Word "
                "documents, dashboards, bid packs and export quotation packs.",
                styles["table_body"],
            ),
        ],
        [
            p("ChatGPT research boardroom", styles["table_label"]),
            p(
                "Handles broad market research, category discovery and strategic "
                "analysis. Its output is advisory until evidence is verified locally.",
                styles["table_body"],
            ),
        ],
        [
            p("Event and knowledge layer", styles["table_label"]),
            p(
                "An append-only event ledger is the canonical record. Registers, "
                "Kanban cards, reports and Drive folders are controlled views of "
                "that record rather than competing sources of truth.",
                styles["table_body"],
            ),
        ],
        [
            p("Policy and approval layer", styles["table_label"]),
            p(
                "Policy-as-code, restricted tool interfaces and approval receipts "
                "keep external, financial, legal and compliance actions fail-closed.",
                styles["table_body"],
            ),
        ],
    ]
    architecture_table = Table(
        architecture,
        colWidths=[1.62 * inch, CONTENT_W - 1.62 * inch],
        repeatRows=1,
        hAlign="LEFT",
    )
    architecture_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
                ("GRID", (0, 0), (-1, -1), 0.55, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(architecture_table)
    story.extend(
        [
            p("What is genuinely different about it", styles["h1"]),
            bullet(
                "It separates AI judgment from operational proof.",
                "ChatGPT can discover and recommend, but deterministic tools must "
                "capture evidence before a case progresses.",
                styles,
            ),
            bullet(
                "It is a state machine, not a chain of prompts.",
                "Every case moves through explicit statuses, gates and stop conditions.",
                styles,
            ),
            bullet(
                "Evidence has a defined maturity level.",
                "A public listing, a downloaded document, a supplier quote and an "
                "approved action are not treated as equivalent evidence.",
                styles,
            ),
            bullet(
                "Governance is part of the architecture.",
                "The approval boundary is enforced by policy and receipts rather "
                "than left as a reminder inside an AI prompt.",
                styles,
            ),
            bullet(
                "The system is auditable and recoverable.",
                "The event stream can reconstruct working views and shows who or "
                "what changed a case, when it changed and what evidence supported "
                "the change.",
                styles,
            ),
            PageBreak(),
            p(
                "What is automated - and what is deliberately not",
                styles["h1"],
            ),
            p(
                '<font color="#163A5F"><b>Automated or automation-assisted:</b></font> '
                "source monitoring, evidence capture, document extraction, "
                "deduplication, scoring, supplier research, draft pricing, draft "
                "compliance, artifact generation, readiness checks, reporting and "
                "follow-up monitoring.",
                styles["body"],
            ),
            p(
                '<font color="#163A5F"><b>Human-controlled:</b></font> supplier or '
                "buyer communication, bid and quotation submission, portal uploads, "
                "payments, DSC use, final price, delivery commitments, payment terms, "
                "final classification, origin claims and legal certifications.",
                styles["body"],
            ),
            p("Current maturity", styles["h1"]),
            p(
                "The internal operating architecture is implemented as a supervised "
                "local runtime. The repository contains the workflow definitions, "
                "event and data schemas, source adapters, parsers, policy controls, "
                "approval lifecycle, artifact generators, projection rebuilds and "
                "extensive regression and edge-case tests.",
                styles["body"],
            ),
            p(
                "I would describe it as a working supervised automation platform - "
                "not as a finished zero-touch tender-submission bot. Credentialed "
                "portal operations and binding commercial or legal actions are "
                "intentionally outside the autonomous tool surface. That is a design "
                "choice, not an unfinished safety check.",
                styles["body"],
            ),
            Spacer(1, 6),
            callout(
                '<font color="#163A5F"><b>In simple terms,</b></font> I have built '
                "the digital operating backbone for a tender and export desk. It "
                "reduces dependence on scattered documents, spreadsheets and "
                "individual memory, while preserving the accountability required "
                "for high-stakes commercial work.",
                styles,
            ),
        ]
    )

    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
