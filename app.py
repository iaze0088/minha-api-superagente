from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/mensagem', methods=['POST'])
def responder():
    dados = request.get_json()
    mensagem = dados.get("mensagem", "").lower()

    if "oi" in mensagem:
        resposta = "Olá! Como posso te ajudar?"
    elif "teste" in mensagem:
        resposta = "Você está testando a API corretamente!"
    else:
        resposta = "Desculpe, não entendi. Tente reformular a pergunta."

    return jsonify({"resposta": resposta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
