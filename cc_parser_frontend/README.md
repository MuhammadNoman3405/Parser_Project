# ⚙️ W++ Token Analyzer

A modern, web-based **Lexical Analyzer** built for the **CS-310 Compiler Construction** course at **UET Taxila**. This application processes source code written in the custom **W++** language, breaking it down into categorized tokens and providing detailed statistical insights through an interactive dashboard.

---

## 🚀 Features

- **🔍 Live Tokenization:** Instantly breaks W++ source code into Keywords, Identifiers, Literals, Constants, Operators, Punctuators, and Special Characters.
- **📊 Statistical Reports:** Generates a detailed overview of token frequency, unique types, category breakdown, and percentage distribution.
- **💎 Identifier & Literal Tracking:** Lists all unique identifiers, constants, and string literals with their frequency and exact line numbers.
- **🌊 Token Stream:** A visual stream view showing every token in order with its category and line reference.
- **📂 File Support:** Upload `.wpp` files directly into the analyzer or type/paste code manually.
- **🖨️ PDF Export:** Generate and download a complete analysis report as a PDF.

---

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
  - Fonts: Syne & JetBrains Mono (Google Fonts)
  - Modern dark-themed UI with glassmorphism and animated grid overlays
- **Backend:** Python 3, FastAPI, Uvicorn
  - Custom character-by-character lexical analyzer (no Regex)
  - REST API with `/analyze/code` and `/analyze/file` endpoints
- **Deployment:**
  - Frontend → GitHub Pages
  - Backend API → Vercel

---

## 🌐 Live Demo

- **Frontend:** [https://muhammadnoman3405.github.io/compiler_project_code/](https://muhammadnoman3405.github.io/compiler_project_code/)
- **Backend API:** [https://compiler-project-code.vercel.app](https://compiler-project-code.vercel.app)
- **Health Check:** [https://compiler-project-code.vercel.app/health](https://compiler-project-code.vercel.app/health)

---

## 💻 How to Run Locally

1. Clone the repository:
```bash
git clone https://github.com/MuhammadNoman3405/compiler_project_code.git
cd compiler_project_code
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
uvicorn API_Connect_point:app --reload --port 8000
```

4. Update `API_BASE_URL` in `Analyze.html`:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

5. Open `index.html` in any modern browser (Chrome, Edge, or Firefox).

---

## 📁 Project Structure

```
compiler_project_code/
├── main.py                  # Core lexical analyzer logic
├── API_Connect_point.py     # FastAPI backend server
├── index.html               # Landing page
├── Analyze.html             # Code input & upload page
├── Results.html             # Analysis results dashboard
├── requirements.txt         # Python dependencies
├── sample_test.wpp          # Sample W++ test file
└── README.md
```

---

## 🔤 W++ Language Token Categories

| Category | Examples |
|---|---|
| **Keywords** | `int`, `float`, `if`, `else`, `while`, `for`, `print`, `read`, `return` |
| **Identifiers** | Variable & function names |
| **Operators** | `=`, `+`, `-`, `*`, `/`, `>`, `<`, `==`, `!=`, `&&`, `\|\|` |
| **Punctuators** | `;`, `,`, `(`, `)`, `{`, `}` |
| **Constants** | Integer & float numeric values |
| **Literals** | String & character values |
| **Special Chars** | `#`, `$`, `@`, `:`, `?` |

---

## 👥 Development Team

| Name | Reg No |
|---|---|
| Muhammad Rayban | 23-CS-46 |
| Muhammad Noman | 23-CS-68 |
| Muhammad Junaid | 23-CS-66 |

---

## 🌐 Connect & Portfolio

- **Portfolio:** [Explore My Projects](https://my-portfolio-website-six-ashen.vercel.app)
- **LinkedIn:** [Muhammad Noman](https://www.linkedin.com/in/muhammad-noman-a219712b0/)

---

*Developed with ❤️ by Team 23-CS*  
*BSCS @ UET Taxila | CS-310 Compiler Construction | Spring 2026*
