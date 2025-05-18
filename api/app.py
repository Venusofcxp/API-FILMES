from flask import Flask, request, jsonify
import requests
import random
import time
import threading

app = Flask(__name__)

session = requests.Session()

CACHE_TIMEOUT = 60  # segundos

# Configurações para montar os links
DOMINIO = "http://solutta.shop:80"
USUARIO = "881101381017"
SENHA = "896811296068"

url_filmes = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_streams"
url_series = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series"
url_categorias_filmes = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_categories"
url_categorias_series = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series_categories"

# Cache separado para cada tipo
cache = {
    "filmes": {"dados": [], "atualizado": 0, "lock": threading.Lock()},
    "series": {"dados": [], "atualizado": 0, "lock": threading.Lock()},
    "generos_filmes": {"dados": [], "atualizado": 0, "lock": threading.Lock()},
    "generos_series": {"dados": [], "atualizado": 0, "lock": threading.Lock()},
}

def cache_expirado(tipo):
    return time.time() - cache[tipo]["atualizado"] > CACHE_TIMEOUT

def atualizar_cache_async(tipo, url):
    def worker():
        try:
            resp = session.get(url, timeout=5)
            if resp.status_code == 200:
                with cache[tipo]["lock"]:
                    cache[tipo]["dados"] = resp.json()
                    cache[tipo]["atualizado"] = time.time()
            else:
                print(f"[ERRO] Código {resp.status_code} ao atualizar cache de {tipo}")
        except Exception as e:
            print(f"[ERRO] Exceção ao atualizar cache de {tipo}: {e}")

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

def obter_cache(tipo, url):
    with cache[tipo]["lock"]:
        if cache_expirado(tipo):
            # Atualiza cache assincronamente
            atualizar_cache_async(tipo, url)
        # Retorna o dado atual (mesmo que possa estar expirado, evita bloqueio)
        return cache[tipo]["dados"]

def limpar_dados(lista, tipo):
    campos_permitidos = ['name', 'stream_id', 'stream_type', 'rating']
    dados_limpos = []
    for item in lista:
        novo = {k: item.get(k) for k in campos_permitidos if k in item}
        novo["tipo"] = tipo
        dados_limpos.append(novo)
    return dados_limpos

def obter_combinados():
    filmes = limpar_dados(obter_cache("filmes", url_filmes), "filme")
    series = limpar_dados(obter_cache("series", url_series), "serie")
    combinados = filmes + series
    random.shuffle(combinados)
    return combinados

@app.route('/api/misturar-filmes-series', methods=['GET'])
def misturar_filmes_series():
    combinados = obter_combinados()

    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 27)), 100)
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
    return jsonify(obter_combinados())

@app.route('/api/generos', methods=['GET'])
def generos():
    # Para gêneros filmes
    generos_filmes = obter_cache("generos_filmes", url_categorias_filmes)
    generos_series = obter_cache("generos_series", url_categorias_series)

    if not generos_filmes or not generos_series:
        return jsonify({'error': 'Erro ao obter os gêneros'}), 500

    return jsonify({
        'filmes': generos_filmes,
        'series': generos_series
    })

@app.errorhandler(500)
def erro_interno(e):
    return jsonify({'error': 'Erro interno no servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
