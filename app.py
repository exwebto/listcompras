from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json 
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
# Importação necessária para segurança de senha
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração do Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Chave secreta para sessões (ESSENCIAL para Flask-Login)
app.config['SECRET_KEY'] = 'uma-chave-muito-secreta-para-a-sessao-do-flask'

# CONFIGURAÇÃO DO FLASK-LOGIN
# ------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define a página de login
db = SQLAlchemy(app)

# ------------------------------------
# DEFINIÇÃO DOS MODELOS (CLASSES DE TABELAS)
# ------------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Armazenaremos a senha com hash
    password_hash = db.Column(db.String(128), nullable=False)
    items = db.relationship('Item', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bought = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Item {self.name}>'

# ------------------------------------
# FUNÇÃO DE CARREGAMENTO DE USUÁRIO
# ------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------------
# ROTAS DE AUTENTICAÇÃO
# ------------------------------------

# Rota de Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verifica se o usuário já existe
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Nome de usuário já existe. Escolha outro.', 'error')
            return redirect(url_for('register'))

        # Cria um novo usuário e define a senha com hash
        new_user = User(username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro bem-sucedido! Você pode fazer login agora.', 'success')
        return redirect(url_for('login'))
    
    # Renderiza o template de registro (ainda precisamos criar register.html)
    return render_template('register.html')

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Verifica se o usuário existe E se a senha está correta
        if user is None or not user.check_password(password):
            flash('Nome de usuário ou senha inválidos.', 'error')
            return redirect(url_for('login'))
        
        # Faz o login do usuário
        login_user(user)
        flash('Login bem-sucedido!', 'success')
        # Redireciona para a página inicial (ou a página que o usuário tentou acessar)
        return redirect(url_for('index'))
    
    # Renderiza o template de login (ainda precisamos criar login.html)
    return render_template('login.html')

# Rota de Logout
@app.route('/logout')
@login_required # Só permite logout se o usuário estiver logado
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# ------------------------------------
# ROTAS (ADAPTADAS PARA BANCO DE DADOS E LOGIN)
# ------------------------------------

# Rota Inicial (index)
@app.route('/')
def index():
    # Se o usuário estiver logado, mostramos apenas os itens dele.
    # Se não estiver logado, mostramos uma lista vazia ou todos os itens (dependendo da sua preferência inicial).
    if current_user.is_authenticated:
        items_from_db = Item.query.filter_by(user_id=current_user.id).order_by(Item.date_added).all()
    else:
        items_from_db = [] # Mostra uma lista vazia se não estiver logado
        
    return render_template('index.html', lista=items_from_db)

# Rota para Adicionar Itens
@app.route('/adicionar', methods=['POST'])
@login_required # Protege a rota: só permite adicionar se estiver logado
def adicionar():
    nome_item = request.form['nome_item'].strip()

    if nome_item:
        # AGORA USAMOS O ID DO USUÁRIO LOGADO (current_user.id)
        novo_item = Item(name=nome_item, user_id=current_user.id)
        
        db.session.add(novo_item)
        db.session.commit()

    return redirect(url_for('index'))

# Rota para Marcar/Desmarcar Item como Comprado
@app.route('/marcar/<int:item_id>')
@login_required # Protege a rota
def marcar(item_id):
    # Encontra o item pelo ID e verifica se pertence ao usuário logado
    item_a_marcar = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

    # Inverte o status de 'bought'
    item_a_marcar.bought = not item_a_marcar.bought

    try:
        db.session.commit()
        return redirect(url_for('index'))
    except Exception:
        db.session.rollback()
        flash("Erro ao marcar item", 'error')
        return redirect(url_for('index'))

# Rota para Remover Item
@app.route('/remover/<int:item_id>')
@login_required # Protege a rota
def remover(item_id):
    # Encontra o item pelo ID e verifica se pertence ao usuário logado
    item_a_remover = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

    try:
        db.session.delete(item_a_remover)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception:
        db.session.rollback()
        flash("Erro ao remover item", 'error')
        return redirect(url_for('index'))