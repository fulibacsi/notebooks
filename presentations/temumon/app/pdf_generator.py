"""PDF generation for monster trading cards."""
import random
import io
from typing import Dict
from reportlab.lib.pagesizes import letter, A6
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def draw_ascii_monster(c: canvas.Canvas, x: float, y: float, width: float) -> None:
    """Draw a simple ASCII art representation of the monster."""
    ascii_arts = [
        ["  ^___^", " (o o)", "  \\_/"],
        ["  /\\_/\\", " ( o.o )", "  > ^ <"],
        [" .-''''-.", "/ o  o \\", "\\  <>  /", " '.__..'"],
        ["  ___", " {o,o}", " |)__)", " -\"-\""],
        [" .--.", "/.---.\\", "|>.<|", "\\___/"],
    ]
    art = random.choice(ascii_arts)
    c.setFont("Courier", 10)
    c.setFillColor(colors.HexColor("#333333"))
    for i, line in enumerate(art):
        c.drawCentredString(x + width/2, y - i*12, line)


def draw_stat_block_2x2(c: canvas.Canvas, x: float, y: float, stats: Dict) -> None:
    """Draw stats in 2x2 grid layout."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, f"ATK: {stats['atk']}")
    c.drawString(x + 80, y, f"DEF: {stats['def']}")
    c.drawString(x, y - 20, f"SPD: {stats['spd']}")
    c.drawString(x + 80, y - 20, f"HP: {stats['hp']}")


def draw_stat_block_1x4(c: canvas.Canvas, x: float, y: float, stats: Dict) -> None:
    """Draw stats in 1x4 vertical layout."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, f"ATK: {stats['atk']}")
    c.drawString(x, y - 18, f"DEF: {stats['def']}")
    c.drawString(x, y - 36, f"SPD: {stats['spd']}")
    c.drawString(x, y - 54, f"HP: {stats['hp']}")


def draw_stat_block_4x1(c: canvas.Canvas, x: float, y: float, stats: Dict) -> None:
    """Draw stats in 4x1 horizontal layout."""
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, f"ATK:{stats['atk']}")
    c.drawString(x + 60, y, f"DEF:{stats['def']}")
    c.drawString(x + 120, y, f"SPD:{stats['spd']}")
    c.drawString(x + 180, y, f"HP:{stats['hp']}")


def generate_card_pdf(monster: Dict) -> bytes:
    """Generate a monster card PDF and return as bytes.
    
    Args:
        monster: Dictionary with keys: name, lore, type, weakness, atk, def, spd, hp
        
    Returns:
        PDF file contents as bytes
    """
    # Create PDF in memory
    buffer = io.BytesIO()
    
    # Random page size for variety
    page_size = random.choice([letter, A6, (6*inch, 8*inch)])
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size
    
    # Border
    border_color = random.choice([colors.black, colors.HexColor("#8B4513"), 
                                  colors.HexColor("#4B0082"), colors.HexColor("#2F4F4F")])
    c.setStrokeColor(border_color)
    c.setLineWidth(random.choice([3, 4, 5, 6]))
    c.rect(0.25*inch, 0.25*inch, width - 0.5*inch, height - 0.5*inch)
    
    # Monster name - randomize position and style
    name_y = random.choice([height - 0.7*inch, 0.6*inch])
    name_size = random.randint(16, 24)
    c.setFont(random.choice(["Helvetica-Bold", "Times-Bold", "Courier-Bold"]), name_size)
    name_color = random.choice([colors.black, colors.HexColor("#8B0000"), 
                                colors.HexColor("#000080"), colors.HexColor("#006400")])
    c.setFillColor(name_color)
    
    # Random text decoration
    name_x = width / 2
    if random.choice([True, False]):  # underline
        c.line(0.5*inch, name_y - 5, width - 0.5*inch, name_y - 5)
    
    c.drawCentredString(name_x, name_y, monster['name'])
    
    # Type and Weakness badges - random location
    badge_y = random.uniform(height * 0.4, height * 0.7)
    badge_x = random.uniform(0.5*inch, width * 0.3)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.white)
    
    # Type badge
    type_colors = {
        "Fire": "#FF4500", "Ice": "#00CED1", "Shadow": "#483D8B",
        "Storm": "#FFD700", "Earth": "#8B4513", "Poison": "#9370DB",
        "Light": "#FFD700", "Void": "#000000"
    }
    c.setFillColor(colors.HexColor(type_colors.get(monster['type'], "#808080")))
    c.rect(badge_x, badge_y, 1.2*inch, 0.3*inch, fill=1)
    c.setFillColor(colors.white)
    c.drawCentredString(badge_x + 0.6*inch, badge_y + 0.08*inch, monster['type'])
    
    # Weakness badge
    c.setFillColor(colors.HexColor(type_colors.get(monster['weakness'], "#808080")))
    c.rect(badge_x + 1.4*inch, badge_y, 1.2*inch, 0.3*inch, fill=1)
    c.setFillColor(colors.white)
    c.drawCentredString(badge_x + 2.0*inch, badge_y + 0.08*inch, f"Weak: {monster['weakness']}")
    
    # Stats - random layout style
    stat_layout = random.choice([draw_stat_block_2x2, draw_stat_block_1x4, draw_stat_block_4x1])
    stat_y = random.uniform(height * 0.25, height * 0.5)
    c.setFillColor(colors.black)
    stat_layout(c, 0.5*inch, stat_y, monster)
    
    # Lore text - random position and style
    lore_y = random.choice([1.2*inch, height - 1.5*inch, stat_y - 0.8*inch])
    lore_font = random.choice(["Helvetica", "Times-Italic", "Helvetica-Oblique"])
    c.setFont(lore_font, 8)
    c.setFillColor(colors.HexColor("#555555"))
    
    # Wrap lore text
    max_width = width - 1*inch
    words = monster['lore'].split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if c.stringWidth(test_line, lore_font, 8) > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    for i, line in enumerate(lines):
        c.drawCentredString(width / 2, lore_y - i*10, line)
    
    # ASCII monster art
    ascii_y = random.uniform(height * 0.35, height * 0.55)
    ascii_x = random.uniform(width * 0.6, width * 0.8)
    draw_ascii_monster(c, ascii_x, ascii_y, 1*inch)
    
    c.save()
    
    # Get PDF bytes from buffer
    buffer.seek(0)
    return buffer.getvalue()
