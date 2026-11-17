"""Generate the QR codes used on /connect.

  images/qr-connect.svg / .png  -> https://amir-zare.com/connect/  (permanent: printed on cards and slides, never change)
  images/qr-contact.svg         -> the contact itself as a vCard ("Add contact" on iPhone and Android, no download)

Needs the `qrcode` package (not used by the site build or CI):
  python3 -m venv /tmp/qrenv && /tmp/qrenv/bin/pip install qrcode==7.4.2 pillow==11.3.0
  /tmp/qrenv/bin/python tools/make-qr.py

Re-run it when the contact details below change. The connect QR content never changes.
"""
import pathlib

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONNECT_URL = "https://amir-zare.com/connect/"

# Kept short (no photo, no note) and low error correction so the code stays easy to scan from a phone screen.
CONTACT = "\r\n".join([
    "BEGIN:VCARD", "VERSION:3.0", "N:Zare;Amir;;;", "FN:Amir Zare", "ORG:DataLayer",
    "TITLE:AI & Data Engineer, Founder of DataLayer", "TEL;TYPE=CELL:+37477393112",
    "EMAIL;TYPE=INTERNET:info@amir-zare.com", "URL:https://amir-zare.com",
    "item1.URL:https://t.me/MrProgrammingX", "item1.X-ABLabel:Telegram",
    "item2.URL:https://linkedin.com/in/binahayat00", "item2.X-ABLabel:LinkedIn",
    "END:VCARD", ""])


def svg(data, level, title):
    q = qrcode.QRCode(error_correction=level, border=2)
    q.add_data(data)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    d = "".join(f"M{x} {y}h1v1h-1z" for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges"><title>{title}</title>'
            f'<rect width="{n}" height="{n}" fill="#fff"/><path fill="#0b1220" d="{d}"/></svg>\n'), q


def main():
    page_svg, q = svg(CONNECT_URL, ERROR_CORRECT_H, f"QR code: {CONNECT_URL}")
    (ROOT / "images/qr-connect.svg").write_text(page_svg)
    q.box_size = 24
    q.make_image(fill_color="#0b1220", back_color="white").save(ROOT / "images/qr-connect.png")
    contact_svg, q2 = svg(CONTACT, ERROR_CORRECT_L, "QR code: Amir Zare contact card")
    (ROOT / "images/qr-contact.svg").write_text(contact_svg)
    print(f"qr-connect: version {q.version}; qr-contact: version {q2.version}, {len(CONTACT)} bytes")


if __name__ == "__main__":
    main()
