import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import csv
import re
import unicodedata
from datetime import date

# Definiere die Liste der Nutzer (passe das an dein Team an!)
users = ['Maximilian Gansky','Daniel Gißibl', 'Marc Summer', 'Adrian Sollereder', 'Severin Stangl', 'Maximilian Brünn', 'Maximilian Chemnitz', 'Simon Huber', 'Michael Hüllmantl', 'Christoph Kögst', 'Iheb Marzougui', 'Marco Osendorfer', 'Michael Schreiber', 'Roshan Thakur', 'Aysel Yavuz']  # Hier deine echten Namen eintragen

# Datei für Daten (CSV)
DATA_FILE = 'zeiterfassung.csv'

# Lade Daten, falls Datei existiert.
# Use semicolon as the canonical separator to avoid issues when descriptions contain commas.
if os.path.exists(DATA_FILE):
    # Try reading as semicolon-separated first (our preferred format)
    try:
        df = pd.read_csv(DATA_FILE, sep=';', encoding='utf-8')
        # If expected columns are missing, try reading with comma separator and then normalize.
        if not set(['Name', 'Datum', 'Stunden', 'Beschreibung']).issubset(df.columns):
            df = pd.read_csv(DATA_FILE, sep=',', encoding='utf-8')
            # normalize to semicolon-separated file for future runs
            df.to_csv(DATA_FILE, index=False, sep=';', encoding='utf-8', quoting=csv.QUOTE_MINIMAL)
    except Exception:
        # Last resort: try comma-separated and normalize
        df = pd.read_csv(DATA_FILE, sep=',', encoding='utf-8', engine='python')
        df.to_csv(DATA_FILE, index=False, sep=';', encoding='utf-8', quoting=csv.QUOTE_MINIMAL)
else:
    df = pd.DataFrame(columns=['Name', 'Datum', 'Stunden', 'Beschreibung'])

# Streamlit App
st.title('Uni-Team Zeiterfassung')


def sanitize_text(s: str) -> str:
    """Remove emojis and control characters from a string.

    Keeps common letters, numbers, punctuation and whitespace. Removes
    characters from known emoji Unicode ranges and ASCII control chars.
    """
    if s is None:
        return ''
    # Normalize to NFC
    s = unicodedata.normalize('NFC', str(s))

    # Remove ASCII control characters
    s = re.sub(r"[\x00-\x1F\x7F]", '', s)

    # Remove common emoji ranges
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"  # dingbats
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    s = emoji_pattern.sub('', s)

    # Collapse multiple whitespace/newlines into single space
    s = re.sub(r"\s+", ' ', s).strip()
    return s

# Formular für neuen Eintrag
with st.form(key='eintrag_form'):
    st.subheader('Eintrag hinzufügen')
    name = st.selectbox('Wähle deinen Namen', users)  # Dropdown-Menü
    start_date = date(2025, 10, 1)  # 1. Oktober 2025
    end_date = date(2026, 1, 26)  # 26. Januar 2026
    datum = st.date_input('Datum', min_value=start_date, max_value=end_date)
    stunden = st.number_input('Stunden', min_value=0.0, max_value=24.0, step=0.5)
    beschreibung = st.text_area('Was hast du gearbeitet?')
    submit = st.form_submit_button('Eintragen')

    if submit:
        if name and datum and stunden is not None:
            # Sanitize description before saving
            orig_beschreibung = beschreibung
            safe_beschreibung = sanitize_text(beschreibung)
            if safe_beschreibung != (orig_beschreibung or ''):
                st.info('Die Beschreibung wurde bereinigt: Emojis oder Steuerzeichen wurden entfernt.')

            new_entry = pd.DataFrame({'Name': [name], 'Datum': [datum], 'Stunden': [stunden], 'Beschreibung': [safe_beschreibung]})
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

    # Gesamtstunden und Limit (Progress)
    total_hours = float(df['Stunden'].sum())
    limit_hours = 192.0

    # Layout: links Balkendiagramm, rechts Kuchendiagramm (Progress)
    col1, col2 = st.columns([3, 1])

    # --- Balkendiagramm (links) ---
    with col1:
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        # Dark background for figure and axes
        fig1.patch.set_facecolor('black')
        ax1.set_facecolor('black')

        # Plot bars
        summary.plot(kind='bar', ax=ax1, color='skyblue')

        # Make labels, ticks and spines visible on dark background
        ax1.set_ylabel('Gesamte Stunden', color='white')
        ax1.set_xlabel('Name', color='white')
        for label in ax1.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')
            label.set_color('white')
        for label in ax1.get_yticklabels():
            label.set_color('white')
        for spine in ax1.spines.values():
            spine.set_color('white')

        st.pyplot(fig1)

    # --- Kuchendiagramm / Progress (rechts) ---
    with col2:
        # If total is within limit, show remaining; if over, show overshoot
        if total_hours <= limit_hours:
            slices = [total_hours, limit_hours - total_hours]
            labels = [f'Erfasst ({total_hours:.1f}h)', f'Verbleibend ({limit_hours - total_hours:.1f}h)']
            colors = ['skyblue', 'grey']
        else:
            slices = [limit_hours, total_hours - limit_hours]
            labels = [f'Limit ({limit_hours:.1f}h)', f'Überschuss ({total_hours - limit_hours:.1f}h)']
            colors = ['skyblue', 'salmon']

        fig2, ax2 = plt.subplots(figsize=(4, 4))
        fig2.patch.set_facecolor('black')
        ax2.set_facecolor('black')

        wedges, texts, autotexts = ax2.pie(
            slices,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f"{pct:.1f}%",
            startangle=90,
            textprops={'color': 'white'}
        )
        # Make wedge edges visible on dark background
        for w in wedges:
            w.set_edgecolor('black')

        ax2.axis('equal')
        ax2.set_title(f'Fortschritt (von {limit_hours:.0f}h)', color='white')

        # Center text with absolute hours
        ax2.text(0, 0, f'{total_hours:.1f}h\ninsgesamt', ha='center', va='center', color='white', fontsize=10)


        st.pyplot(fig2)
