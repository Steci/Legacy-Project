# 🧬 Legacy — Geneweb Modernization Project

> Bringing the historical **Geneweb** software into the modern Python ecosystem.

<div align="center">
  <img src="docs/images/pictureEpitech.png" width="136" height="136" alt="Epitech" style="margin-right: 20px;">
  <img src="docs/images/logoGeneweb.jpeg" width="369" height="136" alt="Geneweb Modernization">
</div>

---

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📜 Table of Contents

* [Purpose 👽](#purpose)
* [Project Subject 📄](#project-subject)
* [Conventional Commits ➕](#conventional-commits)
* [Requirements 🔧](#requirements)
* [Usage 🧠](#usage)
* [Docker 🐳](#docker)
* [Architecture 🏗️](#architecture)
* [Contributors 👋](#contributors)
* [License 🔑](#license)

---

## <a id="purpose"></a> 👽 Purpose

**Legacy** is a modernization of the historical **Geneweb** genealogy software (originally in OCaml).
It aims to **analyze**, **refactor**, and **extend** Geneweb’s core through **Python-based modules and tooling**, ensuring future scalability while preserving legacy logic.

### Core Objectives

* 🧩 Understand and document Geneweb’s architecture
* 🐍 Build a **Python layer** for data analysis, migration, and automation
* 🧪 Apply **DevOps & QA best practices** (testing, CI/CD, security)
* 📚 Provide clear, maintainable **technical documentation**

---

## <a id="project-subject"></a> 📄 Project Subject

> “Change the past, test the present, secure the future!”

This project reimagines legacy software under **modern software engineering** principles — focusing on:

* Refactoring and data validation
* Secure Python tooling
* Cross-language integration (OCaml ↔ Python)

📘 [Read the official Epitech project brief](https://intra.epitech.eu/module/2025/G-ING-900/PAR-9-1/acti-705069/project/file/G-ING-900_legacy.pdf)

---

## <a id="conventional-commits"></a> ➕ Conventional Commits

Follow our [commit rules](docs/conventionnalCommit.md):
`<type>(<scope>): <description>`

Examples:

```
feat(parser): add GEDCOM date normalization
fix(database): correct null foreign key on Family
```

---

## <a id="requirements"></a> 🔧 Requirements

* **Python 3.10+**
* **Poetry** *(recommended)* or `pip`
* **SQLite3**
* *(Optional)* **Geneweb (OCaml)** for data testing/migration

### Install Dependencies

```bash
poetry install
# or
pip install -r requirements.txt
```

---

## <a id="usage"></a> 🧠 Usage

### Run the project

```bash
./run.sh
```

---

## <a id="docker"></a> 🐳 Docker Support

You can run Legacy inside a container for consistent environments.

### Build the image

```bash
docker build -t legacy-project .
```

### Run it

```bash
docker run -it --rm -p 5000:5000 legacy-project
```

> Modify `CMD` in the Dockerfile if you use `run.sh` or a specific entrypoint.

---

## <a id="architecture"></a> 🏗️ Architecture

```
Legacy-Project/
├── app.py                     # Main web or API entrypoint (Flask/FastAPI)
├── run.sh                     # Helper script for running the app
├── Dockerfile                 # Docker configuration for deployment
├── requirements.txt            # Python dependencies
├── CODE_OF_CONDUCT.md          # Contribution conduct rules
├── LICENSE                     # MIT License
├── README.md
├── docs/                       # Project documentation
│   ├── conventionnalCommit.md  # Commit message rules
│   ├── signedCommit.md         # Commit signature requirements
│   ├── research/               # Reports on research topics
│   └── images/                 # Documentation visuals
├── examples_files/             # Genealogical example data for testing
├── lang/                       # Legacy Geneweb language data
├── src/                        # Core source code
│   │
│   ├── consang/                # Consanguinity analysis
│   │   └── cousin_degree/
│   │
│   ├── db/                     # Database drivers and storage backends
│   │
│   ├── models/                 # Core genealogical entities
│   │   ├── family/
│   │   └── person/
│   │
│   ├── parsers/                # File format parsers (Geneweb & GEDCOM)
│   │   ├── ged/
│   │   └── gw/
│   │
│   ├── search_engine/          # API and logic for genealogical data search
│   │
│   └── sosa/                   # Sosa–Stradonitz number system (ancestry indexing)
├── static/                     # Static assets for the web interface
│   ├── css/
│   ├── js/
│   ├── images/
│   └── webfonts/
├── templates/                  # HTML and legacy Geneweb text templates
│   └── templm/                 # Legacy templating system
├── tests/                      # Unit and integration tests
│   ├── consang/
│   ├── parsers/
│   ├── search_engine/
│   ├── sosa/
│   └── fixtures/               # JSON and reference data for tests
│       ├── consang/
│       └── sosa/
├── tools/                      # Developer utilities and regeneration scripts
└── test_app.py                 # Integration tests for the web layer
```

---

## <a id="contributors"></a> 👋 Contributors

| [<img src="https://github.com/Steci.png?size=85" width=85><br><sub>Léa Guillemard</sub>](https://github.com/Steci) | [<img src="https://github.com/Criticat02.png?size=85" width=85><br><sub>Alessandro Tosi</sub>](https://github.com/Criticat02) | [<img src="https://github.com/laurentjiang.png?size=85" width=85><br><sub>Laurent Jiang</sub>](https://github.com/laurentjiang) | [<img src="https://github.com/Pierrelouisleroy.png?size=85" width=85><br><sub>Pierre-Louis Leroy</sub>](https://github.com/Pierrelouisleroy) | [<img src="https://github.com/Tomi-Tom.png?size=85" width=85><br><sub>Tom Bariteau Peter</sub>](https://github.com/Tomi-Tom) |
| :----------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------: |

📫 Contact us:
[lea.guillemard@epitech.eu](mailto:lea.guillemard@epitech.eu) •
[alessandro.tosi@epitech.eu](mailto:alessandro.tosi@epitech.eu) •
[laurent.jiang@epitech.eu](mailto:laurent.jiang@epitech.eu) •
[pierre-louis.leroy@epitech.eu](mailto:pierre-louis.leroy@epitech.eu) •
[tom.bariteau-peter@epitech.eu](mailto:tom.bariteau-peter@epitech.eu)

---

## <a id="license"></a> 🔑 License

Distributed under the [MIT License](LICENSE).
