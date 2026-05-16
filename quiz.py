import streamlit as st
import json
import random
import os

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Master Quiz", page_icon="🎓", layout="wide")
DB_FILE = "quiz_db.json"

# --- 1. GESTIONE DATABASE E TABELLE ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for q in data:
                if "materia" not in q:
                    q["materia"] = "Generale"
                if "table_md" not in q:
                    q["table_md"] = ""
            return data
    return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def estrai_tabella_da_testo(testo_completo):
    if not testo_completo.strip():
        return "", ""
        
    lines = [line.strip() for line in testo_completo.strip().split('\n') if line.strip()]
    blocchi = []
    table_rows = []
    
    for line in lines:
        is_bullet = line.startswith(('-', '•', '*', '1.', '2.', 'a)', 'b)')) and line.count('\t') >= 1
        
        if '\t' in line and not is_bullet:
            cols = line.split('\t')
            if not table_rows:
                table_rows.append("| " + " | ".join(cols) + " |")
                table_rows.append("|" + "|".join(["---"] * len(cols)) + "|")
            else:
                table_rows.append("| " + " | ".join(cols) + " |")
        else:
            if table_rows:
                blocchi.append("\n".join(table_rows))
                table_rows = []
            
            if is_bullet:
                line = line.replace('\t', ' ', 1)
            blocchi.append(line)
            
    if table_rows:
        blocchi.append("\n".join(table_rows))
        
    question_clean = "\n\n".join(blocchi)
    return question_clean, ""

# --- 2. INIZIALIZZAZIONE STATO ---
if 'db' not in st.session_state:
    st.session_state.db = load_data()
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'shuffled_questions' not in st.session_state:
    st.session_state.shuffled_questions = []
if 'current_options' not in st.session_state:
    st.session_state.current_options = []
if 'risposto' not in st.session_state:
    st.session_state.risposto = False
if 'scelta_utente' not in st.session_state:
    st.session_state.scelta_utente = None

if 'form_key' not in st.session_state:
    st.session_state.form_key = 0
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

materie_esistenti = list(set([q["materia"] for q in st.session_state.db]))
materie_esistenti.sort()

# --- 3. MENU DI NAVIGAZIONE LATERALE ---
with st.sidebar:
    st.title("Navigazione")
    app_mode = st.radio("Scegli Area:", ["🎓 Area Studente (Quiz)", "👨‍🏫 Area Professore"])
    st.divider()
    st.write(f"📚 Domande totali: **{len(st.session_state.db)}**")
    
    if st.session_state.quiz_started and app_mode == "🎓 Area Studente (Quiz)":
        if st.button("🛑 Interrompi Quiz"):
            st.session_state.quiz_started = False
            st.rerun()

# ==========================================
# AREA PROFESSORE (INSERIMENTO & GESTIONE)
# ==========================================
if app_mode == "👨‍🏫 Area Professore":
    st.title("👨‍🏫 Area Professore")
    
    tab_inserisci, tab_gestisci = st.tabs(["➕ Inserimento Rapido", "🗄️ Banca Domande"])
    
    # --- TAB 1: INSERIMENTO ---
    with tab_inserisci:
        
        # IL NUOVO SISTEMA DI NOTIFICA FLUTTUANTE (TOAST)
        if st.session_state.show_success:
            st.toast("Domanda archiviata con successo!", icon="✅")
            st.session_state.show_success = False
            
        col1, col2 = st.columns([1, 1])
        fk = st.session_state.form_key
        
        with col1:
            scelta_inserimento = st.selectbox("Scegli Materia:", ["+ Crea Nuova Materia"] + materie_esistenti)
            if scelta_inserimento == "+ Crea Nuova Materia":
                materia_input = st.text_input("Nome nuova materia:")
            else:
                materia_input = scelta_inserimento
                
            correct_a = st.text_input("✔️ Risposta Corretta:", key=f"c_{fk}")
            wrong_1 = st.text_input("❌ Sbagliata 1:", key=f"w1_{fk}")
            wrong_2 = st.text_input("❌ Sbagliata 2 (Opzionale):", key=f"w2_{fk}")
            wrong_3 = st.text_input("❌ Sbagliata 3 (Opzionale):", key=f"w3_{fk}")
            
        with col2:
            new_q_raw = st.text_area("Testo della Domanda (Testo e Tabelle):", height=280, key=f"q_{fk}")
            
        if st.button("💾 Salva nel Database", type="primary", use_container_width=True):
            if new_q_raw and correct_a and wrong_1 and materia_input:
                materia_pulita = materia_input.strip().upper()
                wrongs = [w for w in [wrong_1, wrong_2, wrong_3] if w.strip() != ""]
                question_clean, tabella_md = estrai_tabella_da_testo(new_q_raw)
                
                st.session_state.db.append({
                    "materia": materia_pulita,
                    "question": question_clean,
                    "table_md": tabella_md, 
                    "correct": correct_a,
                    "wrongs": wrongs
                })
                save_data(st.session_state.db)
                
                st.session_state.form_key += 1
                st.session_state.show_success = True
                st.rerun()
            else:
                st.error("Inserisci Materia, Domanda, Risposta giusta e almeno una sbagliata.")

    # --- TAB 2: BANCA DOMANDE (Modifica/Elimina) ---
    with tab_gestisci:
        if len(st.session_state.db) == 0:
            st.info("Il database è vuoto.")
        else:
            filtro_materia = st.selectbox("Filtra per Materia:", materie_esistenti)
            st.write("---")
            
            for idx, q in enumerate(st.session_state.db):
                if q["materia"] == filtro_materia:
                    titolo_expander = q["question"][:60].replace("\n", " ") + "..."
                    with st.expander(f"📝 {titolo_expander}"):
                        
                        edit_q = st.text_area("Testo Domanda (Markdown/Tabella supportata)", q["question"], height=150, key=f"edit_q_{idx}")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            edit_corr = st.text_input("Risposta Corretta", q["correct"], key=f"edit_c_{idx}")
                        with col_b:
                            wrongs_str = ", ".join(q["wrongs"])
                            edit_wrongs = st.text_input("Risposte Sbagliate (separate da virgola)", wrongs_str, key=f"edit_w_{idx}")
                            
                        col_save, col_del = st.columns([3, 1])
                        with col_save:
                            if st.button("🔄 Aggiorna Domanda", key=f"save_{idx}"):
                                st.session_state.db[idx]["question"] = edit_q
                                st.session_state.db[idx]["correct"] = edit_corr
                                st.session_state.db[idx]["wrongs"] = [w.strip() for w in edit_wrongs.split(",") if w.strip()]
                                save_data(st.session_state.db)
                                st.toast("Domanda aggiornata!", icon="🔄")
                                st.rerun()
                        with col_del:
                            if st.button("🗑️ Elimina", type="primary", key=f"del_{idx}"):
                                st.session_state.db.pop(idx)
                                save_data(st.session_state.db)
                                st.rerun()

# ==========================================
# AREA STUDENTE (QUIZ ATTIVO)
# ==========================================
elif app_mode == "🎓 Area Studente (Quiz)":
    st.title("🎓 Simulatore d'Esame")

    if not st.session_state.quiz_started:
        if len(st.session_state.db) > 0:
            st.write("Scegli l'argomento e metti alla prova la tua preparazione.")
            materia_quiz = st.selectbox("Su quale materia vuoi esercitarti?", ["Tutte le Materie (Misto)"] + materie_esistenti)
            
            if st.button("🚀 INIZIA IL TEST", use_container_width=True):
                domande_filtrate = st.session_state.db if materia_quiz == "Tutte le Materie (Misto)" else [q for q in st.session_state.db if q["materia"] == materia_quiz]
                    
                if len(domande_filtrate) > 0:
                    st.session_state.shuffled_questions = random.sample(domande_filtrate, len(domande_filtrate))
                    st.session_state.current_idx = 0
                    st.session_state.score = 0
                    st.session_state.current_options = []
                    st.session_state.risposto = False
                    st.session_state.scelta_utente = None
                    st.session_state.quiz_started = True
                    st.rerun()
                else:
                    st.error("Non ci sono domande per questa materia!")
        else:
            st.info("👈 Il database è vuoto. Vai nell'Area Professore per inserire le domande.")

    else:
        total_q = len(st.session_state.shuffled_questions)
        curr_idx = st.session_state.current_idx
        
        if curr_idx < total_q:
            q_data = st.session_state.shuffled_questions[curr_idx]
            
            st.caption(f"📘 Materia: **{q_data['materia']}** | Domanda {curr_idx + 1} di {total_q}")
            st.progress(curr_idx / total_q)
            
            st.markdown(f"<div style='font-size: 1.2rem; margin-bottom: 1rem;'>", unsafe_allow_html=True)
            st.markdown(q_data["question"], unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if q_data.get("table_md"):
                st.markdown(q_data["table_md"], unsafe_allow_html=True)
            
            if not st.session_state.current_options:
                options = [q_data["correct"]] + q_data["wrongs"]
                random.shuffle(options)
                st.session_state.current_options = options
                
            if not st.session_state.risposto:
                st.markdown("<p style='font-size: 1.1rem; margin-bottom: 0.5rem; margin-top: 2rem;'>Seleziona la risposta:</p>", unsafe_allow_html=True)
                for opt in st.session_state.current_options:
                    if st.button(f"{opt}", use_container_width=True):
                        st.session_state.scelta_utente = opt 
                        if opt == q_data["correct"]:
                            st.session_state.score += 1
                        st.session_state.risposto = True
                        st.rerun() 
            else:
                st.write("### Esito:")
                for opt in st.session_state.current_options:
                    if opt == q_data["correct"]:
                        st.success(f"✔️ **{opt}**")
                    elif opt == st.session_state.scelta_utente:
                        st.error(f"❌ **{opt}**")
                    else:
                        st.markdown(f"<div style='padding: 0.8rem; color: #a0a0a0; border: 1px solid #333; border-radius: 0.5rem; margin-bottom: 1rem;'>⚪ {opt}</div>", unsafe_allow_html=True)
                
                if st.button("Prossima Domanda ➡️", type="primary"):
                    st.session_state.current_idx += 1
                    st.session_state.current_options = []
                    st.session_state.risposto = False
                    st.session_state.scelta_utente = None
                    st.rerun()
        else:
            st.balloons()
            st.success(f"🎉 Quiz Completato! Hai totalizzato {st.session_state.score} risposte esatte su {total_q}.")
            if st.button("🔄 Torna al menu principale"):
                st.session_state.quiz_started = False
                st.rerun()