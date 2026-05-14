import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# Habilita CORS para o seu GitHub Pages conseguir acessar
CORS(app)

def converter_json_para_txt():
    """Lê o arquivo cookies.json em vários formatos e converte para o formato Netscape TXT do yt-dlp"""
    if os.path.exists('cookies.json') and not os.path.exists('cookies.txt'):
        try:
            with open('cookies.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        data = value
                        break
            
            if not isinstance(data, list):
                print("Formato do cookies.json não reconhecido. Não é uma lista válida.")
                return

            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# Gerado automaticamente\n")
                
                for c in data:
                    if not isinstance(c, dict):
                        continue
                    domain = c.get('domain', '')
                    flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                    path = c.get('path', '/')
                    secure = 'TRUE' if c.get('secure', False) else 'FALSE'
                    expiration = str(int(c.get('expirationDate', 0))) if 'expirationDate' in c else '0'
                    name = c.get('name', '')
                    value = c.get('value', '')
                    
                    linha = f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n"
                    f.write(linha)
            print("Cookies convertidos com sucesso!")
        except Exception as e:
            print(f"Erro ao converter cookies: {e}")

converter_json_para_txt()

@app.route('/descascar', methods=['POST'])
def descascar():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Nenhum link fornecido"}), 400

    # Pede explicitamente o melhor vídeo em mp4 e o melhor áudio em m4a (separados) ou o melhor formato único
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Se o yt-dlp conseguir separar vídeo e áudio em alta qualidade, ele cria a chave 'requested_formats'
            if 'requested_formats' in info:
                url_video = info['requested_formats'][0]['url']
                url_audio = info['requested_formats'][1]['url']
                return jsonify({"url_video": url_video, "url_audio": url_audio}), 200
            else:
                # Fallback: Se for um vídeo antigo que só tem formato único (tipo o ID 18)
                url_video = info.get('url')
                return jsonify({"url_video": url_video, "url_audio": None}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
