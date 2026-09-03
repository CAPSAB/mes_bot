import os
from dependency_bootstrap import ensure_runtime_dependencies

ensure_runtime_dependencies(["Pillow", "reportlab", "qrcode"])

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io
import logging
from PIL import Image

logger = logging.getLogger("mesbot-pdf")

_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = "/app" if os.path.isdir("/app") else os.path.dirname(_PYTHON_DIR)
_ASSETS_DIR = os.path.join(_PROJ_ROOT, "assets")
_TRAJECTORY_IMAGE_DIR = os.path.join(_ASSETS_DIR, "common", "img", "trajectories")


def _load_project_env() -> None:
    env_path = os.path.join(_PROJ_ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            key = key.strip()
            if not separator or key not in {"EMAIL_USER", "EMAIL_PASS", "EMAIL_FROM"}:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            os.environ.setdefault(key, value)


_load_project_env()
_QR_PRINT_SIZE = 30 * mm
_QR_LABEL_PADDING = 0.8 * mm
_QR_LABEL_STROKE_WIDTH = 0.5
_SUPPORTED_CARD_LAYOUTS = {
    "2x2": (2, 2),
    "2x3": (2, 3),
    "3x3": (3, 3),
}


def _parse_card_layout(layout: str | None) -> tuple[int, int, str]:
    key = str(layout or "2x3").lower().replace("by", "x").replace(" ", "")
    if key not in _SUPPORTED_CARD_LAYOUTS:
        raise ValueError(f"Unsupported PDF layout: {layout!r}. Use 2x2, 2x3, or 3x3.")
    cols, rows = _SUPPORTED_CARD_LAYOUTS[key]
    return cols, rows, key


def _resolve_trajectory_image(cell_img_name):
    if not cell_img_name:
        return None
    candidates = []
    if os.path.isabs(str(cell_img_name)):
        candidates.append(str(cell_img_name))
    candidates.extend([
        os.path.join(_TRAJECTORY_IMAGE_DIR, str(cell_img_name)),
        os.path.join(_ASSETS_DIR, str(cell_img_name)),
        os.path.join(_ASSETS_DIR, "trajectories", str(cell_img_name)),
    ])
    for img_path in candidates:
        if os.path.exists(img_path):
            return img_path
    logger.warning(f"Trajectory image not found: {cell_img_name}")
    return None


def _load_print_image(img_path):
    img_obj = Image.open(img_path).convert("RGBA")
    bg = Image.new("RGBA", img_obj.size, "WHITE")
    bg.paste(img_obj, (0, 0), img_obj)
    return bg.convert("RGB")


def _qr_image(content):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(content)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _draw_qr_overlay(c, qr_img, qr_x, qr_y):
    
    backing_x = qr_x - _QR_LABEL_PADDING
    backing_y = qr_y - _QR_LABEL_PADDING
    backing_size = _QR_PRINT_SIZE + (2 * _QR_LABEL_PADDING)
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(0.12, 0.12, 0.12)
    c.setLineWidth(_QR_LABEL_STROKE_WIDTH)
    c.rect(backing_x, backing_y, backing_size, backing_size, stroke=1, fill=1)
    c.drawInlineImage(qr_img, qr_x, qr_y, width=_QR_PRINT_SIZE, height=_QR_PRINT_SIZE)


def _draw_image_with_qr(c, img_path, qr_img, x, y, w, h):
    if img_path:
        try:
            clean_img = _load_print_image(img_path)
            c.drawInlineImage(clean_img, x, y, width=w, height=h, preserveAspectRatio=True, anchor="c")
        except Exception as e:
            logger.error(f"Error drawing PDF image {img_path}: {e}")
    else:
        c.setStrokeColorRGB(0.75, 0.8, 0.82)
        c.setFillColorRGB(0.96, 0.98, 0.98)
        c.rect(x, y, w, h, stroke=1, fill=1)
        c.setFillColorRGB(0.35, 0.42, 0.45)
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + w / 2, y + h / 2, "No trajectory image")

    qr_x = x + w - _QR_PRINT_SIZE - 4 * mm
    qr_y = y + 4 * mm
    _draw_qr_overlay(c, qr_img, qr_x, qr_y)


def generate_trajectory_pdf(trajectory_name, frames, output_path, trajectory_image=None, trajectory_id=None):
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    
    cols = 4
    rows = 4
    margin = 15 * mm
    cell_w = (width - 2 * margin) / cols
    cell_h = (height - 2 * margin) / rows
    
    trajectory_img_path = _resolve_trajectory_image(trajectory_image)

    for i, frame in enumerate(frames):
        if i > 0 and i % 16 == 0:
            c.showPage()
            
        page_idx = i % 16
        col = page_idx % cols
        row = rows - 1 - (page_idx // cols) 
        
        x = margin + col * cell_w
        y = margin + row * cell_h
        
        
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(x, y, cell_w, cell_h, stroke=1, fill=0)

        
        label = frame.get('name') or f"Cell {i+1}"
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + cell_w/2, y + cell_h - 5 * mm, label)
        
        
        traj_id = trajectory_id or frame.get('trajectory_id') or 0
        qr_content = f"LOAD_TRAJECTORY:{traj_id}"
        img_box_w = cell_w - 8 * mm
        img_box_h = cell_h - 22 * mm
        img_x = x + 4 * mm
        img_y = y + 8 * mm
        _draw_image_with_qr(c, trajectory_img_path, _qr_image(qr_content), img_x, img_y, img_box_w, img_box_h)

        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + cell_w/2, y + 2 * mm, f"TRAJ_ID: {traj_id} | STEP: {i+1}")

    c.save()
    return output_path

def generate_multi_trajectory_pdf(trajectories_data, output_path, layout: str = "2x3"):
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    cols, rows, layout_key = _parse_card_layout(layout)
    margin = 15 * mm
    cell_w = (width - 2 * margin) / cols
    cell_h = (height - 2 * margin) / rows

    
    total_trajs = len(trajectories_data)
    slots_per_page = cols * rows
    total_slots = ((total_trajs + slots_per_page - 1) // slots_per_page) * slots_per_page
    
    for i in range(total_slots):
        page_idx = i % slots_per_page
        if i > 0 and page_idx == 0:
            c.showPage()
            
        col = page_idx % cols
        row = rows - 1 - (page_idx // cols)
        
        x = margin + col * cell_w
        y = margin + row * cell_h
        
        
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setDash(1, 2) 
        c.rect(x, y, cell_w, cell_h, stroke=1, fill=0)
        c.setDash() 

        if i < total_trajs:
            traj = trajectories_data[i]
            
            name = traj.get('name', f"Trajectory {traj.get('id')}")
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x + cell_w/2, y + cell_h - 10 * mm, name)
            
            
            traj_id = traj.get('id') or 0
            img_path = _resolve_trajectory_image(traj.get('cell_image'))
            img_box_x = x + 8 * mm
            img_box_y = y + 16 * mm
            img_box_w = cell_w - 16 * mm
            img_box_h = cell_h - 34 * mm
            _draw_image_with_qr(
                c,
                img_path,
                _qr_image(f"LOAD_TRAJECTORY:{traj_id}"),
                img_box_x,
                img_box_y,
                img_box_w,
                img_box_h,
            )

            
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(x + cell_w/2, y + 3 * mm, f"TRAJECTORY ID: {traj_id} | {layout_key}")
        else:
            
            c.setFillColorRGB(0.55, 0.55, 0.55)
            c.setFont("Helvetica", 10)
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.drawCentredString(x + cell_w/2, y + cell_h/2, "EMPTY SLOT")

    c.save()
    return output_path

import smtplib
import re
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587


def _validate_email(address: str) -> bool:
    return bool(_EMAIL_PATTERN.match(address))


def send_pdf_email(destination: str, pdf_path: str, subject: str = "MES-BOT: Trajectory Report") -> None:
    
    if not _validate_email(destination):
        raise ValueError(f"Invalid email address: {destination!r}")
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    login = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    sender = os.environ.get("EMAIL_FROM") or login
    if not login or not password:
        raise RuntimeError("EMAIL_USER and EMAIL_PASS environment variables are required")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = destination
    msg["Subject"] = subject
    msg.attach(MIMEText("Please find the trajectory report attached.", "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(pdf_path)}"')
    msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(login, password)
        server.sendmail(sender, destination, msg.as_string())
