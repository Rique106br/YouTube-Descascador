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
            
            # Se o JSON exportado for um dicionário, extrai a lista de dentro dele
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        data = value
                        break
            
            # Se ainda assim não for uma lista, cancela a conversão
            if not isinstance(data, list):
                print("Formato do cookies.json não reconhecido. Não é uma lista válida.")
                return

            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# Gerado automaticamente pelo backend a partir do JSON\n")
                
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
                    
            print("Cookies convertidos de JSON para TXT com sucesso!")
        except Exception as e:
            print(f"Erro ao converter cookies: {e}")

# Executa a conversão logo que o app iniciar no Render
converter_json_para_txt()

@app.route('/descascar', methods=['POST'])
def descascar():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Nenhum link fornecido"}), 400

    # Usamos um filtro de formato super abrangente para o yt-dlp NUNCA travar por falta de formato
    ydl_opts = {
        'format': 'best[ext=mp4]/best/b/bestvideo/worst', 
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
    }
    
    # Usa os cookies gerados para passar pelo bloqueio do YouTube
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Baixa toda a árvore de dados do link
            info = ydl.extract_info(url, download=False)
            
            # Pegamos a lista bruta de formatos para filtrar na mão
            formats = info.get('formats', [])
            url_direta = None
            
            # 1. Procura apenas os formatos que tenham vídeo E áudio juntos (vcodec e acodec ativos)
            combinados = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            
            if combinados:
                # Prioriza MP4 porque roda liso no A-Frame e Moto G84
                mp4s = [f for f in combinados if f.get('ext') == 'mp4']
                if mp4s:
                    # Pega o de melhor resolução
                    mp4s.sort(key=lambda x: x.get('height') or 0, reverse=True)
                    url_direta = mp4s[0].get('url')
                else:
                    # Se não tem MP4, pega a melhor combinação que existir (ex: webm)
                    combinados.sort(key=lambda x: x.get('height') or 0, reverse=True)
                    url_direta = combinados[0].get('url')
            else:
                # 2. Se for um vídeo chato sem formato combinado, pega a melhor imagem pra não dar tela preta
                apenas_video = [f for f in formats if f.get('vcodec') != 'none']
                if apenas_video:
                    apenas_video.sort(key=lambda x: x.get('height') or 0, reverse=True)
                    url_direta = apenas_video[0].get('url')
                else:
                    # 3. Fallback cego (caso de extremo erro do YouTube)
                    url_direta = info.get('url')
            
            if url_direta:
                return jsonify({"url": url_direta}), 200
            else:
                return jsonify({"error": "Não foi possível extrair nenhuma URL de mídia utilizável."}), 500
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
