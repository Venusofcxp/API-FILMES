from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

# URLs de filmes e séries
url_filmes = "http://solutta.shop:80/player_api.php?username=angelicasb&password=323334ang&action=get_vod_streams"
url_series = "http://solutta.shop:80/player_api.php?username=angelicasb&password=323334ang&action=get_series"

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

@app.route('/api/misturar-filmes-series', methods=['GET'])
def misturar_filmes_series():
    filmes = obter_dados(url_filmes)
    series = obter_dados(url_series)
    combinados = filmes + series
    random.shuffle(combinados)

    # Paginação
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
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

    filmes = obter_dados(url_filmes)
    series = obter_dados(url_series)
    combinados = filmes + series

    # Filtrar resultados com base na pesquisa
    resultados = [item for item in combinados if query in item.get('name', '').lower()]

    if not resultados:
        return jsonify({'message': 'Nenhum resultado encontrado para a pesquisa.'}), 404

    return jsonify(resultados)

@app.route('/api/dados-brutos', methods=['GET'])
def dados_brutos():
    filmes = obter_dados(url_filmes)
    series = obter_dados(url_series)
    combinados = filmes + series

    return jsonify(combinados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
