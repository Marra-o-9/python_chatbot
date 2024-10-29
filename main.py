import os
import logging
from typing import List
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Função para formatar resposta com ou sem evento de acompanhamento
# Função para formatar resposta
def format_response(texts: List[str], user_name: str = "") -> jsonify:
    follow_up_message = f"Precisa de mais alguma coisa, {user_name}?" if user_name else "Precisa de mais alguma coisa?"
    return jsonify({"fulfillmentMessages": [{"text": {"text": texts}}, {"text": {"text": [follow_up_message]}}]})

# Função para consulta de endereço por CEP
def get_address_by_cep(cep: str) -> str:
    api_url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            address_data = response.json()
            if "erro" not in address_data:
                address = (
                    f"Endereço: {address_data['logradouro']}, "
                    f"Bairro: {address_data['bairro']}, "
                    f"Cidade: {address_data['localidade']}, "
                    f"Estado: {address_data['uf']}"
                )
                return address
            else:
                return "Não encontrei informações para esse CEP. Verifique e tente novamente."
        else:
            return "Desculpe, não consegui acessar as informações do endereço no momento."
    except Exception as e:
        logger.error(f"Erro ao acessar a API ViaCEP: {e}")
        return "Ocorreu um erro ao tentar consultar o endereço."

# Endpoint principal do webhook
@app.route('/dialogflow', methods=['POST'])
def dialogflow():
    data = request.get_json()
    action = data['queryResult'].get('action', 'Unknown Action')
    parameters = data['queryResult'].get('parameters', {})

    # Condição para consulta de CEP
    if action == 'address.query':
        cep = parameters.get('cep', None)
        if cep:
            address_info = get_address_by_cep(cep)
            # Envia resposta e define um evento de acompanhamento, por exemplo, 'continue_conversation'
            response = format_response([address_info], followup_event="continue_conversation")
        else:
            response = format_response(["Por favor, informe um CEP válido."])
    else:
        response = format_response(['Ação não reconhecida.'])

    return response

# Ponto de entrada para o Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port)
