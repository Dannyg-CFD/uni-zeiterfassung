import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import date

# Definiere die Liste der Nutzer (passe das an dein Team an!)
users = ['Daniel Gißibl', 'Marc Summer', 'Adrian Sollereder', '']  # Hier deine echten Namen eintragen

# Datei für Daten (CSV)
DATA_FILE = 'zeiterfassung.csv'

# Lade Daten, falls Datei existiert
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=['Name', 'Datum', 'Stunden', 'Beschreibung'])

# Streamlit App
st.title('Uni-Team Zeiterfassung')

# Formular für neuen Eintrag
with st.form(key='eintrag_form'):
    st.subheader('Eintrag hinzufügen')
    name = st.selectbox('Wähle deinen Namen', users)  # Dropdown-Menü
    today = date.today()  # Heutiges Datum: 2025-10-03
    end_date = date(2026, 2, 28)  # Ende Februar 2026 (anpassen, falls nötig)
    datum = st.date_input('Datum', min_value=today, max_value=end_date)
    stunden = st.number_input('Stunden', min_value=0.0, max_value=24.0, step=0.5)
    beschreibung = st.text_area('Was hast du gearbeitet?')
    submit = st.form_submit_button('Eintragen')

    if submit:
        if name and datum and stunden:
            new_entry = pd.DataFrame({'Name': [name], 'Datum': [datum], 'Stunden': [stunden], 'Beschreibung': [beschreibung]})
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f'Eintrag für {name} am {datum} gespeichert!')
        else:
            st.error('Fülle alle Pflichtfelder aus (Name, Datum, Stunden)!')

# Alle Einträge anzeigen
st.subheader('Alle Einträge')
st.dataframe(df)

# Diagramme (Zusammenfassung)
if not df.empty:
    st.subheader('Zusammenfassung: Gesamte Stunden pro Person')
    summary = df.groupby('Name')['Stunden'].sum().sort_values(ascending=False)
    fig, ax = plt.subplots()
    summary.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_ylabel('Gesamte Stunden')
    ax.set_xlabel('Name')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig)