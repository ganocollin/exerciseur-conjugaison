# app.py (version corrigée v2.1)
import streamlit as st
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt
import unicodedata
import time

st.set_page_config(page_title="Exerciseur — Présent (v2.1)", layout="centered")

# ---------------------
# Utilitaires
# ---------------------
def norm(s):
    """Nettoie et simplifie une chaîne pour comparaison tolérante."""
    if not s:
        return ""
    s = s.strip().lower()
    s = s.replace("’", "'").replace("`", "'")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = " ".join(s.split())
    s = s.replace("j'", "je ")
    pronoms = ["je ", "tu ", "il ", "elle ", "on ", "nous ", "vous ", "ils ", "elles "]
    for p in pronoms:
        if s.startswith(p):
            s = s[len(p):]
            break
    return s

def is_correct(user, correct):
    return norm(user) == norm(correct)

def minutes_to_seconds(label):
    return {"5 minutes": 5*60, "10 minutes": 10*60, "15 minutes": 15*60, "Pas de limite": None}[label]

# ---------------------
# Données : 24 verbes
# ---------------------
CORRECT = {
    "être": ["je suis","tu es","il est","nous sommes","vous êtes","ils sont"],
    "avoir": ["j'ai","tu as","il a","nous avons","vous avez","ils ont"],
    "aimer": ["j'aime","tu aimes","il aime","nous aimons","vous aimez","ils aiment"],
    "aller": ["je vais","tu vas","il va","nous allons","vous allez","ils vont"],
    "choisir": ["je choisis","tu choisis","il choisit","nous choisissons","vous choisissez","ils choisissent"],
    "manger": ["je mange","tu manges","il mange","nous mangeons","vous mangez","ils mangent"],
    "faire": ["je fais","tu fais","il fait","nous faisons","vous faites","ils font"],
    "vouloir": ["je veux","tu veux","il veut","nous voulons","vous voulez","ils veulent"],
    "commencer": ["je commence","tu commences","il commence","nous commençons","vous commencez","ils commencent"],
    "dire": ["je dis","tu dis","il dit","nous disons","vous dites","ils disent"],
    "pouvoir": ["je peux","tu peux","il peut","nous pouvons","vous pouvez","ils peuvent"],
    "s'appeler": ["je m'appelle","tu t'appelles","il s'appelle","nous nous appelons","vous vous appelez","ils s'appellent"],
    "prendre": ["je prends","tu prends","il prend","nous prenons","vous prenez","ils prennent"],
    "lire": ["je lis","tu lis","il lit","nous lisons","vous lisez","ils lisent"],
    "écrire": ["j'écris","tu écris","il écrit","nous écrivons","vous écrivez","ils écrivent"],
    "devoir": ["je dois","tu dois","il doit","nous devons","vous devez","ils doivent"],
    "voir": ["je vois","tu vois","il voit","nous voyons","vous voyez","ils voient"],
    "boire": ["je bois","tu bois","il boit","nous buvons","vous buvez","ils boivent"],
    "partir": ["je pars","tu pars","il part","nous partons","vous partez","ils partent"],
    "connaitre": ["je connais","tu connais","il connaît","nous connaissons","vous connaissez","ils connaissent"],
    "savoir": ["je sais","tu sais","il sait","nous savons","vous savez","ils savent"],
    "mettre": ["je mets","tu mets","il met","nous mettons","vous mettez","ils mettent"],
    "venir": ["je viens","tu viens","il vient","nous venons","vous venez","ils viennent"],
    "entendre": ["j'entends","tu entends","il entend","nous entendons","vous entendez","ils entendent"],
}

ALL_VERBS = list(CORRECT.keys())
PRONOMS = ["je", "tu", "il/elle/on", "nous", "vous", "ils/elles"]

# ---------------------
# Interface : identification + choix
# ---------------------
st.title("🧠 Exerciseur de conjugaison (v2.1)")

nom_eleve = st.text_input("Entre ton prénom :", "")
if not nom_eleve:
    st.warning("👉 Entre ton prénom pour commencer.")
    st.stop()
nom_eleve = nom_eleve.strip()

# temps de travail
st.markdown("**Temps de travail**")
temps_travail = st.radio("Choisis ton temps :", ["5 minutes", "10 minutes", "15 minutes", "Pas de limite"], index=3)

# contrat de travail
st.markdown("**Contrat : choisis les verbes sur lesquels tu veux travailler**")
if st.checkbox("Tous les verbes"):
    verbes_contrat = ALL_VERBS.copy()
else:
    verbes_contrat = st.multiselect("Sélectionne les verbes :", options=ALL_VERBS, default=ALL_VERBS[:4])

if not verbes_contrat:
    st.warning("👉 Choisis au moins un verbe.")
    st.stop()

# boutons
col1, col2 = st.columns([1, 1])
with col1:
    start_btn = st.button("▶️ Commencer l'exercice")
with col2:
    st.button("🔄 Réinitialiser l'interface", on_click=lambda: st.session_state.clear())

# ---------------------
# Minuteur / état
# ---------------------
if "started" not in st.session_state:
    st.session_state.started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "duration" not in st.session_state:
    st.session_state.duration = None
if "reset_id" not in st.session_state:
    st.session_state.reset_id = 0

if start_btn:
    st.session_state.started = True
    st.session_state.reset_id += 1
    st.session_state.duration = minutes_to_seconds(temps_travail)
    st.session_state.start_time = time.time()

# affichage minuteur
if st.session_state.started:
    dur = st.session_state.duration
    if dur:
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, dur - elapsed)
        mins, secs = divmod(int(remaining), 60)
        st.metric("⏱️ Temps restant", f"{mins:02d}:{secs:02d}")
        if remaining <= 0:
            st.session_state.started = False
            st.session_state.auto_finish = True
            st.success("⏰ Temps écoulé ! Passage à la correction...")
    else:
        st.info("Temps illimité — clique sur 'Corriger et enregistrer' quand tu as fini.")
        st.session_state.auto_finish = False
else:
    st.session_state.auto_finish = False

# ---------------------
# Champs d'exercice
# ---------------------
st.markdown("---")
st.header("Conjugue les verbes du contrat")

user_answers = {}
for verb in verbes_contrat:
    st.subheader(verb.capitalize())
    cols = st.columns(6)
    for i, pron in enumerate(PRONOMS):
        key = f"{nom_eleve}_{verb}_{i}_r{st.session_state.reset_id}"
        if key not in st.session_state:
            st.session_state[key] = ""
        val = cols[i].text_input(
            f"{verb}_{i}",
            label_visibility="collapsed",
            placeholder=pron,
            key=key,
        )
        user_answers[(verb, i)] = st.session_state[key]

submit = st.button("Corriger et enregistrer")

# ---------------------
# Correction (manuelle ou automatique)
# ---------------------
do_compute = submit or st.session_state.get("auto_finish", False)

if do_compute:
    per_verb_scores = {}
    details = {}
    for verb in ALL_VERBS:
        if verb in verbes_contrat:
            correct_forms = CORRECT[verb]
            correct_count = 0
            user_forms = []
            per_pron = []
            for i, corr in enumerate(correct_forms):
                user_input = user_answers.get((verb, i), "")
                user_forms.append(user_input)
                ok = is_correct(user_input, corr)
                per_pron.append(ok)
                if ok:
                    correct_count += 1
            pct = round((correct_count / len(correct_forms)) * 100)
            per_verb_scores[verb] = pct
            details[verb] = {"user": user_forms, "per_pron": per_pron}
        else:
            per_verb_scores[verb] = "HC"
            details[verb] = {"user": ["HC"]*6, "per_pron": [False]*6}

    # scores synthétiques
    contract_scores = [per_verb_scores[v] for v in verbes_contrat if isinstance(per_verb_scores[v], (int,float))]
    score_contrat = round(sum(contract_scores) / len(contract_scores)) if contract_scores else 0
    global_scores = [s if isinstance(s,(int,float)) else 0 for s in per_verb_scores.values()]
    score_global = round(sum(global_scores) / len(global_scores))

    # affichage synthèse
    st.header("Résultats")
    col_a, col_b = st.columns(2)
    col_a.metric("Score sur le contrat", f"{score_contrat} %")
    col_b.metric("Score global (24 verbes)", f"{score_global} %")

    # --- Détails avec ✅ ❌
    st.subheader("📘 Détails des conjugaisons")
    for verb in verbes_contrat:
        st.markdown(f"### {verb.capitalize()}")
        df_rows = []
        for i, pron in enumerate(PRONOMS):
            corr = CORRECT[verb][i]
            userv = user_answers.get((verb, i), "") or "—"
            ok = "✅" if is_correct(userv, corr) else "❌"
            df_rows.append((pron, userv, corr, ok))
        df = pd.DataFrame(df_rows, columns=["Pronom", "Réponse élève", "Réponse attendue", "OK"])
        st.table(df)

    # --- Enregistrement
    fichier_suivi = f"suivi_{nom_eleve.lower().strip()}.csv"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "date": now,
        "temps_choisi": temps_travail,
        "contrat": ";".join(verbes_contrat),
        "score_contrat": score_contrat,
        "score_global": score_global,
    }
    for verb in ALL_VERBS:
        row[verb] = per_verb_scores[verb]
    if os.path.exists(fichier_suivi):
        df_hist = pd.read_csv(fichier_suivi)
        df_hist = pd.concat([df_hist, pd.DataFrame([row])], ignore_index=True)
    else:
        df_hist = pd.DataFrame([row])
    df_hist.to_csv(fichier_suivi, index=False)
    st.success("Résultats enregistrés ✅")
    st.markdown("---")

    # --- Graphique
    st.header("Progression (historique)")
    df_hist['date_parsed'] = pd.to_datetime(df_hist['date'])
    df_plot = df_hist.set_index('date_parsed')[['score_contrat', 'score_global']].astype(float)
    st.line_chart(df_plot)
    with open(fichier_suivi, "rb") as f:
        st.download_button("📥 Télécharger l'historique (CSV)", data=f, file_name=fichier_suivi)

else:
    st.info("👉 Complète l'exercice puis clique sur **Corriger et enregistrer** pour voir les résultats.")

# ---------------------
# Notes
# ---------------------
st.markdown("""
---
**Remarques :**
- Les verbes hors contrat sont marqués `HC` dans le fichier.
- Le graphique montre le % sur le contrat et le % global.
- Le minuteur se met en pause automatique à la fin du temps imparti.
""")
