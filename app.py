from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
# Habilita CORS para o seu GitHub Pages conseguir acessar
CORS(app)

@app.route('/descascar', methods=['POST'])
def descascar():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Nenhum link fornecido"}), 400

    # Configuração do yt-dlp para extrair a melhor qualidade mp4 combinada
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url_direta = info.get('url')
            
            if url_direta:
                return jsonify({"url": url_direta}), 200
            else:
                return jsonify({"error": "Não foi possível extrair a URL direta."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Servidores na nuvem definem a própria porta, se não achar, usa 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
