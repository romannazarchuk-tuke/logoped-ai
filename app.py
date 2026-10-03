from flask import Flask, request, jsonify, render_template, Response, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import json
import re
import unicodedata
from collections import Counter
from datetime import timedelta

app = Flask(__name__)

app.secret_key = "super_secret_key_dla_logopeda"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(DATA_DIR, 'logoped.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    chats = db.relationship('ChatSession', backref='user', lazy=True)

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default="Nový chat")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10), nullable=False) 
    content = db.Column(db.Text, nullable=False)    
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)

with app.app_context():
    db.create_all()

GEMINI_API_KEY = "" 
UNI_API_KEY = ""
UNI_API_URL = ""


KNOWLEDGE_CHUNKS = []

def stem_slovak(word):
    word = unicodedata.normalize('NFKD', word).encode('ASCII', 'ignore').decode('utf-8').lower()
    
    endings = ['iach', 'iam', 'och', 'ach', 'ich', 'ych', 'ovi', 'ami', 'emi', 'ou', 'om', 'am', 'em', 'ia', 'ie', 'iu', 'ov', 'y', 'a', 'e', 'i', 'u', 'o']
    
    for ending in endings:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[:-len(ending)]
    return word

def load_and_chunk_knowledge():
    global KNOWLEDGE_CHUNKS
    dataset_folder = "Dataset"
    files = ["Dateset.txt", "Dateset 2.txt", "Instruction-Response.txt", "Instruction-Response 2.txt"]
    chunks = []
    
    for filename in files:
        filepath = os.path.join(dataset_folder, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                paragraphs = text.split('\n\n')
                current_chunk = f"--- Zdroj: {filename} ---\n"
                
                for p in paragraphs:
                    if len(current_chunk) + len(p) > 1500:
                        words = re.findall(r'\w+', current_chunk)
                        stems = [stem_slovak(w) for w in words]
                        chunks.append({"text": current_chunk.strip(), "stems": Counter(stems)})
                        
                        current_chunk = f"--- Zdroj: {filename} ---\n" + p + "\n\n"
                    else:
                        current_chunk += p + "\n\n"
                if current_chunk.strip():
                    words = re.findall(r'\w+', current_chunk)
                    stems = [stem_slovak(w) for w in words]
                    chunks.append({"text": current_chunk.strip(), "stems": Counter(stems)})
        else:
            print(f" {filepath} do not find!")
            
    KNOWLEDGE_CHUNKS = chunks

def retrieve_relevant_chunks(query, top_k=3):
    if not KNOWLEDGE_CHUNKS:
        return ""
    
    query_words = re.findall(r'\w+', query)
    query_stems = set(stem_slovak(w) for w in query_words)
    
    if not query_stems:
        return KNOWLEDGE_CHUNKS[0]["text"]
        
    scores = []
    for chunk_data in KNOWLEDGE_CHUNKS:
        chunk_stems = chunk_data["stems"]
        score = sum(chunk_stems[stem] for stem in query_stems)
        scores.append((score, chunk_data["text"]))
        
    scores.sort(key=lambda x: x[0], reverse=True)
    relevant_chunks = [text for score, text in scores[:top_k] if score > 0]
    
    if not relevant_chunks:
        return "Špecifické detaily v datasete sa nenašli. Použi všeobecné znalosti."
        
    return "\n\n...\n\n".join(relevant_chunks)

load_and_chunk_knowledge()

BASE_PROMPT = """Si expertný logopedický asistent. Tvojou prioritou sú poskytnuté materiály (súbory Instruction-Response.txt, Instruction-Response 2.txt, Dateset.txt, Dateset 2.txt).

Pravidlá pre zdroj informácií a flexibilitu:
1. Priorita dát: Pri nácviku konkrétnych hlások (R, L, sykavky atď.) čerpaj výhradne zo zadaných materiálov. Neimprovizuj v slovách, vetách ani básničkách.
2. Všeobecné znalosti: Ak sa používateľ spýta na všeobecnú logopedickú vec, ktorá v materiáloch nie je (napr. motivácia dieťaťa, základná anatómia rečových orgánov, všeobecné rady pre rodičov), môžeš použiť svoje všeobecné znalosti.

Pravidlá pre štruktúru nácviku hlásky:
Keď ťa používateľ požiada o nácvik konkrétnej hlásky, tvoja odpoveď musí VŽDY obsahovať tieto kroky v tomto poradí:
- Inštrukcie (Artikulácia): Presný popis polohy jazyka, pier a dýchania.
- Prípravné cvičenia (ak sú relevantné).
- Slabiky: Zoznam na precvičenie.
- Slová: Logicky štruktúrované (začiatok, stred, koniec slova). MAXIMÁLNE 7 až 10 slov z každej skupiny.
- Vety: MAXIMÁLNE 3 až 5 viet.
- Básničky alebo Riekanky: 1 alebo 2 z databázy.

Všeobecné pravidlá:
- Hovor len po slovensky.
- Primerané množstvo (Dávkovanie): Nezahlcuj textom. Ak používateľ chce viac príkladov, napíš: "Ak chcete viac slov alebo viet na precvičenie, stačí napísať!"

7. DÔLEŽITÉ FORMÁTOVANIE NA KONCI:
Na úplný koniec odpovede (bez akýchkoľvek nadpisov ako "Ďalšie kroky") VŽDY pridaj 3 návrhy na doplňujúce otázky. MUSÍŠ použiť tento presný formát s pomlčkami:
---OTÁZKY---
- [Tvoja prvá otázka]
- [Tvoja druhá otázka]
- [Tvoja tretia otázka]

8. Názov chatu: Vygeneruj krátky názov (3-4 slová) pre tento rozhovor. MUSÍŠ použiť tento presný formát s pomlčkami:
---NÁZOV---
[Krátky názov]"""

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True 
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            return "Nesprávne meno alebo heslo", 401
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return "Používateľ s týmto menom už existuje", 400
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/get_chats', methods=['GET'])
def get_chats():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    chats = ChatSession.query.filter_by(user_id=session['user_id']).order_by(ChatSession.id.desc()).all()
    chat_list = [{"id": c.id, "title": c.title} for c in chats]
    return jsonify({"chats": chat_list})

@app.route('/get_history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    chat_id = request.args.get('chat_id')
    if not chat_id:
        return jsonify({"messages": []})
        
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.id).all()
    history = [{"role": msg.role, "content": msg.content} for msg in messages]
    return jsonify({"messages": history})

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"reply": "Prosím, prihláste sa."}), 401

    data = request.json
    user_message = data.get('message', '').strip()
    chat_id = data.get('chat_id')
    selected_model = data.get('model', 'model2')
    user_id = session['user_id']

    if not user_message:
        return jsonify({"reply": "Napíšte prosím nejakú správu."}), 400

    if len(user_message) > 2000:
        return jsonify({"reply": "Vaša správa je príliš dlhá. Skúste ju skrátiť."}), 400

    is_new_chat = False
    if chat_id:
        chat_session = ChatSession.query.filter_by(id=chat_id, user_id=user_id).first()
    else:
        chat_session = None

    if not chat_session:
        chat_session = ChatSession(title="Generujem názov...", user_id=user_id)
        db.session.add(chat_session)
        db.session.commit()
        is_new_chat = True
    
    current_chat_id = chat_session.id
    
    new_user_msg = Message(role='user', content=user_message, chat_id=current_chat_id)
    db.session.add(new_user_msg)
    db.session.commit()
    
    relevant_context = retrieve_relevant_chunks(user_message)
    DYNAMIC_SYSTEM_PROMPT = BASE_PROMPT + "\n\n--- RELEVANTNÉ DÁTA Z DATASETU ---\n" + relevant_context + "\n--- KONIEC DÁT ---"

    chat_history = Message.query.filter_by(chat_id=current_chat_id).order_by(Message.id).all()[-10:]
    
    gemini_contents = []
    uni_messages = [{"role": "system", "content": DYNAMIC_SYSTEM_PROMPT}]

    for msg in chat_history:
        gemini_role = "user" if msg.role == "user" else "model"
        gemini_contents.append({"role": gemini_role, "parts": [{"text": msg.content}]})
        
        uni_role = "user" if msg.role == "user" else "assistant"
        uni_messages.append({"role": uni_role, "content": msg.content})

    def generate():
        full_bot_response = "" 
        try:
            if selected_model == "model2":
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {UNI_API_KEY}'
                }
                api_payload = {
                    "model": "model120-fast",
                    "messages": uni_messages,
                    "stream": True
                }
                response = requests.post(UNI_API_URL, headers=headers, json=api_payload, stream=True)
                
                if response.status_code != 200:
                    yield f"Chyba API Univerzity: Nepodarilo sa získať odpoveď (Kód: {response.status_code})."
                    return

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: ') and decoded_line != 'data: [DONE]':
                            try:
                                chunk_data = json.loads(decoded_line[6:])
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        text_chunk = delta['content']
                                        full_bot_response += text_chunk 
                                        yield text_chunk
                            except: 
                                pass

            else:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:streamGenerateContent?alt=sse"
                headers = {'Content-Type': 'application/json', 'x-goog-api-key': GEMINI_API_KEY}
                api_payload = {
                    "systemInstruction": {"parts": [{"text": DYNAMIC_SYSTEM_PROMPT}]},
                    "contents": gemini_contents
                }
                
                response = requests.post(gemini_url, headers=headers, json=api_payload, stream=True)
                
                if response.status_code != 200:
                    yield f"Chyba API Gemini: Nepodarilo sa získať odpoveď (Kód: {response.status_code})."
                    return

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            json_str = decoded_line[6:]
                            try:
                                chunk_data = json.loads(json_str)
                                if 'candidates' in chunk_data and len(chunk_data['candidates']) > 0:
                                    text_chunk = chunk_data['candidates'][0]['content']['parts'][0].get('text', '')
                                    full_bot_response += text_chunk 
                                    yield text_chunk
                            except: 
                                pass
                            
            with app.app_context():
                final_text = full_bot_response
                new_title = None
                
                if "---NÁZOV---" in full_bot_response:
                    parts = full_bot_response.split("---NÁZOV---")
                    final_text = parts[0].strip()
                    if len(parts) > 1:
                        raw_title = parts[1].strip()
                        new_title = raw_title.split('\n')[0].replace('*', '').replace('[', '').replace(']', '').strip()

                new_bot_msg = Message(role='bot', content=final_text, chat_id=current_chat_id)
                db.session.add(new_bot_msg)
                
                if is_new_chat:
                    chat_to_update = ChatSession.query.get(current_chat_id)
                    if chat_to_update:
                        chat_to_update.title = new_title[:40] if new_title else user_message[:25]+"..."
                
                db.session.commit()
                
        except Exception as e:
            yield f"Chyba: {str(e)}"

    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)