import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# Habilita CORS para o seu GitHub Pages conseguir acessar
CORS(app)

def converter_json_para_txt():
    """Lê o arquivo cookies.json e converte para o formato Netscape TXT que o yt-dlp exige"""
    if os.path.exists('cookies.json') and not os.path.exists('cookies.txt'):
        try:
            with open('cookies.json', 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# Gerado automaticamente pelo backend a partir do JSON\n")
                
                for c in cookies:
                    domain = c.get('domain', '')
                    # O formato Netscape precisa saber se o domínio começa com ponto
                    flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                    path = c.get('path', '/')
                    secure = 'TRUE' if c.get('secure', False) else 'FALSE'
                    
                    # Evita erro caso algum cookie não tenha data de expiração
                    expiration = str(int(c.get('expirationDate', 0))) if 'expirationDate' in c else '0'
                    name = c.get('name', '')
                    value = c.get('value', '')
                    
                    # Monta a linha exata que o yt-dlp consegue ler
                    linha = f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n"
                    f.write(linha)
            print("Cookies convertidos de JSON para TXT com sucesso!")
        except Exception as e:
            print(f"Erro ao converter cookies: {e}")

# Executa a conversão logo que o app iniciar
converter_json_para_txt()

@app.route('/descascar', methods=['POST'])
def descascar():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Nenhum link fornecido"}), 400

    # Configuração do yt-dlp
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
    }
    
    # Se a conversão funcionou e o txt existir, usa ele para passar pelo YouTube
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
