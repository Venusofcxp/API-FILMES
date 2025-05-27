from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

# Configurações
DOMINIO = "https://hiveos.space"
USUARIO = "VenusPlay"
SENHA = "659225573"

url_filmes = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_streams"
url_series = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series"

url_categorias_filmes = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_vod_categories"
url_categorias_series = f"{DOMINIO}/player_api.php?username={USUARIO}&password={SENHA}&action=get_series_categories"

# Gêneros proibidos
GENERO_PROIBIDO = ["xxx adultos", "xxx onlyfans"]

def obter_dados(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao obter dados de {url}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro ao fazer requisição para {url}: {e}")
        return []

def limpar_nome_genero(nome_original):
    if "|" in nome_original:
        parte = nome_original.split("|")[1].strip()
    else:
        parte = nome_original

    parte_minuscula = parte.lower()

    for proibido in GENERO_PROIBIDO:
        if proibido in parte_minuscula:
            return None  # Gênero proibido

    return parte  # Apenas retorna a parte limpa, sem emoji

@app.route('/api/generos', methods=['GET'])
def listar_generos():
    categorias_filmes = obter_dados(url_categorias_filmes)
    categorias_series = obter_dados(url_categorias_series)

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

def filtrar_conteudo_adulto(lista):
    filtrada = []
    for item in lista:
        categoria_name = item.get('category_name', '').lower()
        if not any(proibido in categoria_name for proibido in GENERO_PROIBIDO):
            filtrada.append(item)
    return filtrada

@app.route('/api/misturar-filmes-series', methods=['GET'])
def misturar_filmes_series():
    filmes = filtrar_conteudo_adulto(obter_dados(url_filmes))
    series = filtrar_conteudo_adulto(obter_dados(url_series))
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
        return jsonify({'error': 'Por favor, forneça um termo de pesquisa usando o parâmetro "q".'}), 400

    filmes = filtrar_conteudo_adulto(obter_dados(url_filmes))
    series = filtrar_conteudo_adulto(obter_dados(url_series))
    combinados = filmes + series

    resultados = [item for item in combinados if query in item.get('name', '').lower()]

    if not resultados:
        return jsonify({'message': 'Nenhum resultado encontrado para a pesquisa.'}), 404

    return jsonify(resultados)

@app.route('/api/dados-brutos', methods=['GET'])
def dados_brutos():
    filmes = filtrar_conteudo_adulto(obter_dados(url_filmes))
    series = filtrar_conteudo_adulto(obter_dados(url_series))
    combinados = filmes + series
    return jsonify(combinados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
