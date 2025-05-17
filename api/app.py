from flask import Flask, request, jsonify
import requests
import random
import time

app = Flask(__name__)

# Cache simples em memória com timeout
cache = {
    "filmes": {"dados": [], "atualizado": 0},
    "series": {"dados": [], "atualizado": 0}
}
CACHE_TIMEOUT = 60  # segundos

# URLs IPTV
url_filmes = "http://solutta.shop:80/player_api.php?username=881101381017&password=896811296068&action=get_vod_streams"
url_series = "http://solutta.shop:80/player_api.php?username=881101381017&password=896811296068&action=get_series"

def obter_dados(url, tipo):
    agora = time.time()
    if agora - cache[tipo]["atualizado"] > CACHE_TIMEOUT:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                cache[tipo]["dados"] = response.json()
                cache[tipo]["atualizado"] = agora
            else:
                print(f"[ERRO] Código {response.status_code} para {tipo}")
        except Exception as e:
            print(f"[ERRO] Exceção ao buscar {tipo}: {e}")
    return cache[tipo]["dados"]

def obter_combinados():
    filmes = obter_dados(url_filmes, "filmes")
    series = obter_dados(url_series, "series")
    combinados = filmes + series
    random.shuffle(combinados)
    return combinados

@app.route('/api/misturar-filmes-series', methods=['GET'])
def misturar_filmes_series():
    combinados = obter_combinados()

    # Paginação
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 27)), 100)  # limite máximo de 100
    start = (page - 1) * per_page
    end = start + per_page
    paginados = combinados[start:end]

    if not paginados:
        return jsonify({'error': 'Nenhum dado encontrado para esta página.'}), 404

    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': len(combinados),
        'data': paginados
    })

@app.route('/api/pesquisar', methods=['GET'])
def pesquisar():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify({'error': 'Por favor, forneça um termo de pesquisa com ?q=seutermo'}), 400

    combinados = obter_combinados()
    resultados = [item for item in combinados if query in item.get('name', '').lower()]

    if not resultados:
        return jsonify({'message': 'Nenhum resultado encontrado.'}), 404

    return jsonify(resultados)

@app.route('/api/dados-brutos', methods=['GET'])
def dados_brutos():
    combinados = obter_combinados()
    return jsonify(combinados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
