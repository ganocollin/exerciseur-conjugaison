
import streamlit as st
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Exerciseur — Présent de l'indicatif", layout="centered")

# --- Utilities ---
import unicodedata

def norm(s):
    """Nettoie et simplifie une chaîne pour comparer deux conjugaisons de manière tolérante."""
    if not s:
        return ""
    # Supprime espaces en trop et passe en minuscules
    s = s.strip().lower()
    # Normalise les apostrophes et les accents
    s = s.replace("’", "'").replace("`", "'")
    s = unicodedata.normalize("NFD", s)  # décompose les lettres accentuées
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # retire les accents
    # Supprime les espaces doubles
    s = " ".join(s.split())

    # Tolère les variantes de "je"/"j'"
    s = s.replace("j'", "je ")

    # Supprime le pronom sujet s'il est présent (pour tolérer "suis" = "je suis")
    pronoms = ["je ", "tu ", "il ", "elle ", "on ", "nous ", "vous ", "ils ", "elles "]
    for p in pronoms:
        if s.startswith(p):
            s = s[len(p):]
            break

    return s

def is_correct(user, correct):
    return norm(user) == norm(correct)

# Correct conjugations (présent de l'indicatif)
CORRECT = {
    "Être": ["je suis", "tu es", "il est", "nous sommes", "vous êtes", "ils sont"],
    "Avoir": ["j'ai", "tu as", "il a", "nous avons", "vous avez", "ils ont"],
    "Aller": ["je vais", "tu vas", "il va", "nous allons", "vous allez", "ils vont"],
    "Parler": ["je parle", "tu parles", "il parle", "nous parlons", "vous parlez", "ils parlent"],
}

PRONOMS = ["je", "tu", "il/elle/on", "nous", "vous", "ils/elles"]

DATA_FILE = "suivi_conjugaison_streamlit.csv"

# --- UI ---
st.title("Exerciseur — Présent de l'indicatif (4 verbes)")
st.write("L'élève saisit les six formes du présent pour chaque verbe. L'app corrige, calcule les % et enregistre les résultats.")

col1, col2 = st.columns([2,1])

with col1:
    st.header("Conjugue :")
    user_answers = {}
   # bouton pour recommencer — incrémente un compteur dans session_state
if "reset_id" not in st.session_state:
    st.session_state.reset_id = 0

def do_reset():
    st.session_state.reset_id += 1

st.button("🔄 Nouvel exercice", on_click=do_reset)

st.header("Conjugue :")
user_answers = {}
for verb in CORRECT.keys():
    st.subheader(verb)
    cols = st.columns(6)
    for i, pron in enumerate(PRONOMS):
        # clé unique = verb_pron_resetid : change à chaque reset
        key = f"{verb}_{i}_r{st.session_state.reset_id}"
        placeholder = cols[i].text_input(
            f"{verb}_{i}",                    # label (unique text id, pas la key)
            label_visibility="collapsed",
            placeholder=pron,
            key=key
        )
        user_answers[(verb, i)] = placeholder

submit = st.button("Corriger et enregistrer")

# --- Correction ---
if submit:
    results = {}
    details = {}
    for verb, correct_forms in CORRECT.items():
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
        results[verb] = pct
        details[verb] = {"user": user_forms, "per_pron": per_pron}

    average = round(sum(results.values()) / len(results))

    # Show results
    st.header("Résultats")
    cols = st.columns(len(results))
    for i, (verb, pct) in enumerate(results.items()):
        with cols[i]:
            st.metric(label=verb, value=f"{pct} %")

    st.write(f"**Moyenne générale : {average} %**")

    # Show detailed feedback per verb
    for verb, info in details.items():
        st.subheader(f"Détails — {verb}")
        df_rows = []
        for i, pron in enumerate(PRONOMS):
            corr = CORRECT[verb][i]
            userv = info["user"][i] or "—"
            ok = "✅" if info["per_pron"][i] else "❌"
            df_rows.append((pron, userv, corr, ok))
        df = pd.DataFrame(df_rows, columns=["Pronom", "Réponse élève", "Réponse attendue", "OK"])
        st.table(df)

    # Save results line to CSV (date, verb percentages, average)
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {"date": date}
    for verb, pct in results.items():
        row[verb] = pct
    row["moyenne"] = average

    if os.path.exists(DATA_FILE):
        df_hist = pd.read_csv(DATA_FILE)
        df_hist = pd.concat([df_hist, pd.DataFrame([row])], ignore_index=True)

    else:
        df_hist = pd.DataFrame([row])
    df_hist.to_csv(DATA_FILE, index=False)

    st.success("Résultats enregistrés ✅")
    st.markdown("---")

# --- Progression ---
st.header("Progression (historique)")
if os.path.exists(DATA_FILE):
    df_hist = pd.read_csv(DATA_FILE)
    df_hist['date_short'] = pd.to_datetime(df_hist['date']).dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(df_hist)

    # Plot using matplotlib for clearer control
    fig, ax = plt.subplots(figsize=(8,4))
    for verb in CORRECT.keys():
        if verb in df_hist.columns:
            ax.plot(pd.to_datetime(df_hist['date']), df_hist[verb], marker='o', label=verb)
    ax.set_ylabel("Score (%)")
    ax.set_xlabel("Date")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.4)
    st.pyplot(fig)

    # Download link for CSV
    with open(DATA_FILE, "rb") as f:
        st.download_button("Télécharger l'historique (CSV)", data=f, file_name=DATA_FILE)
else:
    st.info("Aucun historique trouvé. Après la première correction, les résultats apparaîtront ici.")

st.markdown("""
---
**Remarques / tolérances** :\n
- L'application normalise les espaces et la casse; elle accepte `j'` et `je` forms.
- Pour étendre l'app : ajouter d'autres temps ou verbes est simple (modifier le dictionnaire CORRECT).
""")
