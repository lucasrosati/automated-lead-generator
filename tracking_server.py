
from flask import Flask, request, send_file, redirect
import sqlite3
from datetime import datetime
import io
import base64

app = Flask(__name__)

# Pixel transparente 1x1
PIXEL_DATA = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")

@app.route("/pixel/<tracking_id>.png")
def track_open(tracking_id):
    # Registrar abertura
    conn = sqlite3.connect("email_analytics.db")
    cursor = conn.cursor()
    
    ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")
    
    cursor.execute("""
        INSERT INTO tracking_events 
        (tracking_id, evento_tipo, timestamp, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
    """, (tracking_id, "abertura", datetime.now(), ip_address, user_agent))
    
    cursor.execute("""
        UPDATE email_campaigns 
        SET aberto = 1, 
            primeiro_abertura = COALESCE(primeiro_abertura, ?),
            total_aberturas = total_aberturas + 1
        WHERE tracking_id = ?
    """, (datetime.now(), tracking_id))
    
    conn.commit()
    conn.close()
    
    return send_file(io.BytesIO(PIXEL_DATA), mimetype="image/png")

@app.route("/click/<tracking_id>")
def track_click(tracking_id):
    url = request.args.get("url", "https://linkedin.com")
    
    # Registrar clique
    conn = sqlite3.connect("email_analytics.db")
    cursor = conn.cursor()
    
    ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")
    
    cursor.execute("""
        INSERT INTO tracking_events 
        (tracking_id, evento_tipo, timestamp, ip_address, user_agent, dados_extras)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tracking_id, "clique", datetime.now(), ip_address, user_agent, url))
    
    cursor.execute("""
        UPDATE email_campaigns 
        SET clicou_link = 1,
            primeiro_clique = COALESCE(primeiro_clique, ?),
            total_cliques = total_cliques + 1
        WHERE tracking_id = ?
    """, (datetime.now(), tracking_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url)

@app.route("/unsubscribe/<tracking_id>")
def unsubscribe(tracking_id):
    return f"<h2>Descadastrado com sucesso!</h2><p>ID: {tracking_id}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
