from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

# Nome do arquivo onde a lista será salva
NOME_ARQUIVO = "lista_compras.json"

def carregar_lista():
    """Carrega a lista de compras de um arquivo JSON."""
    if os.path.exists(NOME_ARQUIVO):
        with open(NOME_ARQUIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_lista(lista):
    """Salva a lista de compras em um arquivo JSON."""
    with open(NOME_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    """Página inicial que exibe a lista de compras."""
    lista_de_compras = carregar_lista()
    return render_template('index.html', lista=lista_de_compras)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    """Adiciona um novo item à lista."""
    nome_item = request.form['nome_item'].strip()
    if nome_item:
        lista_de_compras = carregar_lista()
        lista_de_compras.append({"nome": nome_item, "comprado": False})
        salvar_lista(lista_de_compras)
    return redirect(url_for('index'))

@app.route('/marcar/<int:item_id>')
def marcar(item_id):
    """Marca um item como comprado/desmarcado."""
    lista_de_compras = carregar_lista()
    if 0 <= item_id < len(lista_de_compras):
        lista_de_compras[item_id]['comprado'] = not lista_de_compras[item_id]['comprado']
        salvar_lista(lista_de_compras)
    return redirect(url_for('index'))

@app.route('/remover/<int:item_id>')
def remover(item_id):
    """Remove um item da lista."""
    lista_de_compras = carregar_lista()
    if 0 <= item_id < len(lista_de_compras):
        lista_de_compras.pop(item_id)
        salvar_lista(lista_de_compras)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Cria o arquivo JSON vazio se ele não existir
    if not os.path.exists(NOME_ARQUIVO):
        salvar_lista([])
    app.run(debug=True) # debug=True reinicia o servidor automaticamente em cada mudança
