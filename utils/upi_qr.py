import urllib.parse
from decimal import Decimal

def generate_upi_qr_url(upi_id: str, payee_name: str, amount: Decimal, transaction_note: str) -> str:
    """
    Generates a dynamic UPI Payment URI and formats it as an image URL.
    UPI URI standard format:
    upi://pay?pa={upi_id}&pn={payee_name}&am={amount}&tn={transaction_note}&cu=INR
    """
    if not upi_id:
        return ""
    
    clean_amt = f"{amount:.2f}"
    params = {
        "pa": upi_id,
        "pn": payee_name or "Restaurant",
        "am": clean_amt,
        "tn": transaction_note or "Bill Payment",
        "cu": "INR"
    }
    upi_uri = f"upi://pay?{urllib.parse.urlencode(params)}"
    
    # Use standard fast public QR chart API without requiring heavy external C-dependencies
    encoded_uri = urllib.parse.quote(upi_uri)
    return f"https://api.qrserver.com/v1/create-qr-code/?data={encoded_uri}&size=180x180&margin=0"
