from flask import Flask, request, jsonify
import requests
import random
from cachetools import TTLCache
from functools import wraps
import time

app = Flask(__name__)

# Configurações
DOMINIO = "https://hiveos.space"
USUARIO = "VenusPlay"
SENHA = "659225573"

# Endpoints da API IPTV
URLS = {
    "filmes": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_streams",
    "series": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series",
    "categorias_filmes": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_categories",
    "categorias_series": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series_categories"
}

# Cache de 300 segundos (5 minutos) para cada requisição externa
cache = TTLCache(maxsize=100, ttl=300)

# Gêneros proibidos
GENERO_PROIBIDO = ["xxx adultos", "xxx onlyfans"]

# Decorador para cache de função
def cache_data(func):
    @wraps(func)
    def wrapper(url):
        if url in cache:
            return cache[url]
        result = func(url)
        cache[url] = result
        return result
    return wrapper

@cache_data
def obter_dados(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERRO] Falha ao requisitar {url}: {e}")
        return []

def limpar_nome_genero(nome_original):
    parte = nome_original.split("|")[1].strip() if "|" in nome_original else nome_original
    parte_minuscula = parte.lower()

    for proibido in GENERO_PROIBIDO:
        if proibido in parte_minuscula:
            return None
    return parte

def filtrar_conteudo_adulto(lista):
    return [
        item for item in lista
        if not any(proibido in item.get('category_name', '').lower() for proibido in GENERO_PROIBIDO)
    ]

@app.route('/api/venus/generos', methods=['GET'])
def listar_generos():
    categorias_filmes = obter_dados(URLS["categorias_filmes"])
    categorias_series = obter_dados(URLS["categorias_series"])

    todas_categorias = categorias_filmes + categorias_series
    categorias_unicas = {}
    nomes_vistos = set()

    for cat in todas_categorias:
        nome_genero = limpar_nome_genero(cat.get('category_name', ''))
        if nome_genero and nome_genero not in nomes_vistos:
            nomes_vistos.add(nome_genero)
            categorias_unicas[cat['category_id']] = {
                "category_id": cat['category_id'],
                "category_name": nome_genero,
                "parent_id": cat.get('parent_id', 0)
            }

    return jsonify(list(categorias_unicas.values()))

@app.route('/api/venusplay/page', methods=['GET'])
def misturar_filmes_series():
    filmes = filtrar_conteudo_adulto(obter_dados(URLS["filmes"]))
    series = filtrar_conteudo_adulto(obter_dados(URLS["series"]))
    combinados = filmes + series
    random.shuffle(combinados)

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 27))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = combinados[start:end]

    if not paginated_data:
        return jsonify({'error': 'Nenhum dado encontrado para esta página.'}), 404

    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': len(combinados),
        'data': paginated_data
    })

@app.route('/api/venusplay/pesquisar', methods=['GET'])
def pesquisar():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify({'error': 'Por favor, forneça um termo de pesquisa usando o parâmetro "q".'}), 400

    filmes = filtrar_conteudo_adulto(obter_dados(URLS["filmes"]))
    series = filtrar_conteudo_adulto(obter_dados(URLS["series"]))
    combinados = filmes + series

    resultados = [item for item in combinados if query in item.get('name', '').lower()]

    if not resultados:
        return jsonify({'message': 'Nenhum resultado encontrado para a pesquisa.'}), 404

    return jsonify(resultados)

@app.route('/api/venusplay/todos', methods=['GET'])
def dados_brutos():
    filmes = filtrar_conteudo_adulto(obter_dados(URLS["filmes"]))
    series = filtrar_conteudo_adulto(obter_dados(URLS["series"]))
    combinados = filmes + series
    return jsonify(combinados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
