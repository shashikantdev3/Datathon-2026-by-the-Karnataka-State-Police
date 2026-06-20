"""Export the chat conversation (with evidence trail) to a local PDF."""
import io, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def conversation_to_pdf(history):
    """history: list of dicts {q, answer, sql, reasoning, ts}. Returns PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    ss = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=ss["Title"], fontSize=18, textColor=colors.HexColor("#0b3d91"))
    h = ParagraphStyle("h", parent=ss["Heading3"], textColor=colors.HexColor("#b91c1c"))
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14)
    mono = ParagraphStyle("m", parent=ss["Code"], fontSize=8, textColor=colors.HexColor("#334155"))
    small = ParagraphStyle("s", parent=ss["BodyText"], fontSize=8, textColor=colors.grey)

    el = [Paragraph("CrimeSense by DevWithData", title),
          Paragraph("Conversation History &amp; Evidence Trail", ss["Heading2"]),
          Paragraph("Generated: " + datetime.datetime.now().strftime("%d %b %Y, %H:%M") +
                    "  |  Confidential — for authorised law-enforcement use only", small),
          Spacer(1, 0.4 * cm)]

    for i, turn in enumerate(history, 1):
        el.append(Paragraph(f"Q{i}.  {_esc(turn['q'])}", h))
        el.append(Paragraph(_esc(turn["answer"]).replace("**", ""), body))
        if turn.get("reasoning"):
            el.append(Paragraph("Reasoning:", small))
            for r in turn["reasoning"]:
                el.append(Paragraph("• " + _esc(r), small))
        if turn.get("sql"):
            el.append(Spacer(1, 0.1 * cm))
            el.append(Paragraph("SQL: " + _esc(turn["sql"]), mono))
        el.append(Spacer(1, 0.35 * cm))

    doc.build(el)
    return buf.getvalue()


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
