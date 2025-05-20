from flask import Flask, request, jsonify
import requests
import random
import time

app = Flask(__name__)

# Configuração
DOMINIO = "https://hiveos.site"
USUARIO = "219886848"
SENHA = "248454967"

# URLs
URLS = {
    "filmes": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_streams",
    "series": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series",
    "categorias_filmes": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_categories",
    "categorias_series": f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series_categories"
}

GENERO_PROIBIDO = ["xxx adultos", "xxx onlyfans"]

EMOJI_GENEROS = {
    "lançamentos": "🔄", "4k": "📺", "ação": "🔥", "aventura": "🗺️", "animes": "🎌",
    "animação": "🐭", "infantil": "🧸", "marvel": "🦸‍♂️", "dc": "🦸‍♀️", "guerra": "⚔️",
    "faroeste": "🤠", "nacionais": "🇧🇷", "religiosos": "🙏", "romance": "❤️",
    "suspense": "🕵️", "terror": "👻", "fantasia": "🧙", "ficção": "🚀",
    "família": "👨‍👩‍👧‍👦", "especial de natal": "🎄", "cinema": "🎥", "crime": "🕵️‍♂️",
    "comédia": "😂", "documentários": "📚", "drama": "🎭", "legendados": "🔤",
    "shows": "🎤", "rock in rio": "🎸"
}

# Cache com expiração
CACHE = {}
CACHE_EXPIRACAO = 300  # segundos

def obter_dados_cache(nome, url):
    agora = time.time()
    if nome in CACHE and (agora - CACHE[nome]['timestamp']) < CACHE_EXPIRACAO:
        return CACHE[nome]['dados']
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            CACHE[nome] = {"dados": dados, "timestamp": agora}
            return dados
        else:
            print(f"Erro ao obter dados de {url}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro ao requisitar {url}: {e}")
        return []

def limpar_nome_genero(nome_original):
    if "|" in nome_original:
        parte = nome_original.split("|")[1].strip()
    else:
        parte = nome_original

    parte_minuscula = parte.lower()
    for proibido in GENERO_PROIBIDO:
        if proibido in parte_minuscula:
            return None

    for chave, emoji in EMOJI_GENEROS.items():
        if chave in parte_minuscula:
            return f"{emoji} {parte}"
    return parte

def filtrar_conteudo_adulto(lista):
    return [
        item for item in lista
        if not any(proibido in item.get('category_name', '').lower() for proibido in GENERO_PROIBIDO)
    ]

@app.route('/api/generos', methods=['GET'])
def listar_generos():
    categorias_filmes = obter_dados_cache("categorias_filmes", URLS["categorias_filmes"])
    categorias_series = obter_dados_cache("categorias_series", URLS["categorias_series"])

    todas = categorias_filmes + categorias_series
    nomes_vistos = set()
    categorias_unicas = []

    for cat in todas:
        nome_genero = limpar_nome_genero(cat.get('category_name', ''))
        if nome_genero and nome_genero not in nomes_vistos:
            nomes_vistos.add(nome_genero)
            categorias_unicas.append({
                "category_id": cat['category_id'],
                "category_name": nome_genero,
                "parent_id": cat.get('parent_id', 0)
            })

    return jsonify(categorias_unicas)

@app.route('/api/misturar-filmes-series', methods=['GET'])
def misturar_filmes_series():
    filmes = filtrar_conteudo_adulto(obter_dados_cache("filmes", URLS["filmes"]))
    series = filtrar_conteudo_adulto(obter_dados_cache("series", URLS["series"]))
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

@app.route('/api/pesquisar', methods=['GET'])
def pesquisar():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'error': 'Forneça um termo usando "q".'}), 400

    filmes = filtrar_conteudo_adulto(obter_dados_cache("filmes", URLS["filmes"]))
    series = filtrar_conteudo_adulto(obter_dados_cache("series", URLS["series"]))
    combinados = filmes + series

    resultados = [item for item in combinados if query in item.get('name', '').lower()]
    if not resultados:
        return jsonify({'message': 'Nenhum resultado encontrado.'}), 404

    return jsonify(resultados)

@app.route('/api/dados-brutos', methods=['GET'])
def dados_brutos():
    filmes = filtrar_conteudo_adulto(obter_dados_cache("filmes", URLS["filmes"]))
    series = filtrar_conteudo_adulto(obter_dados_cache("series", URLS["series"]))
    return jsonify(filmes + series)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
