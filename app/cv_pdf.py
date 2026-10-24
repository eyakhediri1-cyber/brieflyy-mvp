import html
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ACCENT = colors.HexColor("#1F3A5F")
GREY = colors.HexColor("#555555")


def _t(value) -> str:
    return html.escape(str(value)) if value not in (None, "") else ""


def _styles():
    return {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=22, leading=26, alignment=TA_CENTER, textColor=ACCENT),
        "role": ParagraphStyle("role", fontName="Helvetica-Oblique", fontSize=11, leading=14, alignment=TA_CENTER, textColor=GREY),
        "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER, textColor=GREY),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=10, spaceAfter=2, textColor=ACCENT),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=12.5),
        "job": ParagraphStyle("job", fontName="Helvetica-Bold", fontSize=9.5, leading=12.5),
        "right": ParagraphStyle("right", fontName="Helvetica", fontSize=9, leading=12.5, alignment=TA_RIGHT, textColor=GREY),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, leading=12.5, leftIndent=12, bulletIndent=2),
    }


def _section(title: str, st) -> list:
    return [Paragraph(title.upper(), st["h2"]), HRFlowable(width="100%", thickness=0.6, color=ACCENT, spaceAfter=4)]


def _head(parts, sep: str) -> str:
    return sep.join(_t(p) for p in parts if p not in (None, ""))


def _entry(head_text: str, right: str, st) -> Table:
    table = Table(
        [[Paragraph(head_text, st["job"]), Paragraph(_t(right), st["right"])]],
        colWidths=["75%", "25%"],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _bullets(items, st) -> list:
    return [Paragraph(_t(i), st["bullet"], bulletText="•") for i in (items or []) if i]


def render_cv_pdf(cv: dict, title: str = "CV") -> bytes:
    """Génère le CV en PDF. Rien n'est ajouté : seul le contenu fourni est affiché."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=title,
                            leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    st = _styles()
    story = []

    if cv.get("nom"):
        story.append(Paragraph(_t(cv["nom"]), st["name"]))
    if cv.get("titre"):
        story.append(Paragraph(_t(cv["titre"]), st["role"]))
    contacts = [_t(cv.get(k)) for k in ("email", "ville", "linkedin", "github") if cv.get(k)]
    if contacts:
        story.append(Spacer(1, 4))
        story.append(Paragraph("  |  ".join(contacts), st["contact"]))
    story.append(Spacer(1, 6))

    if cv.get("profil"):
        story += _section("Profil", st)
        story.append(Paragraph(_t(cv["profil"]), st["body"]))

    if cv.get("competences"):
        story += _section("Compétences clés", st)
        story.append(Paragraph("  •  ".join(_t(s) for s in cv["competences"]), st["body"]))

    if cv.get("experiences"):
        story += _section("Expériences professionnelles", st)
        for exp in cv["experiences"]:
            story.append(_entry(_head([exp.get("poste"), exp.get("entreprise")], " | "), exp.get("dates") or "", st))
            story += _bullets(exp.get("missions"), st)
            story.append(Spacer(1, 5))

    if cv.get("projets"):
        story += _section("Projets", st)
        for p in cv["projets"]:
            story.append(_entry(_head([p.get("nom")], ""), p.get("dates") or "", st))
            story += _bullets(p.get("description"), st)
            if p.get("lien"):
                story.append(Paragraph(_t(p["lien"]), st["contact"]))
            story.append(Spacer(1, 5))

    if cv.get("formations"):
        story += _section("Formation académique", st)
        for f in cv["formations"]:
            story.append(_entry(_head([f.get("diplome"), f.get("etablissement")], " — "), f.get("annee") or "", st))
            story += _bullets(f.get("details"), st)
            story.append(Spacer(1, 4))

    if cv.get("associations"):
        story += _section("Associations", st)
        for a in cv["associations"]:
            story.append(_entry(_head([a.get("nom"), a.get("role")], " — "), a.get("dates") or "", st))

    if cv.get("certifications"):
        story += _section("Certifications", st)
        story += _bullets(cv["certifications"], st)

    if cv.get("langues"):
        story += _section("Langues", st)
        story.append(Paragraph("  •  ".join(_t(l) for l in cv["langues"]), st["body"]))

    doc.build(story)
    return buf.getvalue()
