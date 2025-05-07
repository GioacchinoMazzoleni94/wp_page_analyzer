# WP Page Analyzer

Analizzatore completo di siti WordPress in locale, con frontend HTML/CSS/JS e backend Flask/Python.

---

## 📂 Struttura del progetto

```
wp_page_analyzer/
│
├── app.py # Server Flask principale
├── requirements.txt # Dipendenze Python
├── README.md # Guida all’uso (questo file)
├── .gitignore # File/dir da escludere da Git
│
├── reports/ # Report JSON salvati per dominio
│
├── templates/
│ └── index.html # Frontend HTML
│
└── static/
    ├── js/
    │   └── main.js # Logica client-side
    └── css/
        └── style.css # (opzionale) stili custom
```

---

## 🚀 Setup & Installazione

1.  **Clona il repository**

    ```bash
    git clone https://github.com/GioacchinoMazzoleni94/wp_page_analyzer.git
    cd wp_page_analyzer
    ```

2.  **Crea e attiva un virtual environment**

    ```bash
    python3 -m venv venv
    source venv/bin/activate    # macOS/Linux
    # Oppure per Windows:
    # venv\Scripts\activate
    ```

3.  **Installa le dipendenze**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Avvia l’app in locale**

    ```bash
    python app.py
    ```

5.  Apri il browser su `http://12.0.0.1:5000/`

---

## ⚙️ Utilizzo

Nella pagina web inserisci:

* URL del sito WordPress (es. `example.com`)
* Username e Password se l’API REST è protetta

Clicca **Avvia**.

Naviga tra le tab per visualizzare le analisi:

* **Overview:** Riepilogo generale e opzioni di esportazione (CSV, JSON, MD).
* **Performance, SEO, Accessibilità, Sicurezza:** Analisi specifiche.
* **Temi, Plugin, Utenti:** Dettagli su elementi del sito.
* **Report:** Carica o salva report di analisi in formato JSON.

---

## 🤝 Contribuire

Se desideri contribuire al progetto:

1.  Esegui il fork (biforcazione) di questo repository.
2.  Crea un nuovo branch per la tua feature:

    ```bash
    git checkout -b feature/mia-feature
    ```

3.  Apporta le tue modifiche e fai commit:

    ```bash
    git commit -am "Aggiunta mia feature"
    ```

4.  Esegui il push sul tuo fork e apri una Pull Request al repository originale.

---

## 📄 Licenza

Questo progetto è distribuito sotto la **MIT License**. Vedi il file `LICENSE` per maggiori dettagli.
