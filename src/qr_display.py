import os
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from io import StringIO


def generate_qr_terminal(url: str, clear_screen: bool = True) -> str:
    if clear_screen:
        os.system("cls" if os.name == "nt" else "clear")

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=2,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    output = StringIO()
    output.write("\n")
    output.write("=" * 50 + "\n")
    output.write("  OpenTouch-Remote\n")
    output.write("  Scan QR Code to connect:\n")
    output.write("=" * 50 + "\n\n")

    qr.print_ascii(out=output, invert=True)

    output.write("\n")
    output.write(f"  URL: {url}\n")
    output.write("\n")
    output.write("  Press Ctrl+C to stop the server\n")
    output.write("=" * 50 + "\n")

    return output.getvalue()


def display_connection_info(url: str):
    qr_output = generate_qr_terminal(url)
    print(qr_output)
