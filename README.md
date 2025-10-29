# 🧬 Legacy - Geneweb Modernization Project

The repository for the **Legacy Project**, a modernization of the historical **Geneweb** software.

<div id="pictureLegacy" style="display: flex;">  
  <img src="docs/images/pictureEpitech.png" alt="picture Epitech" width="136" height="136" style="margin-right: 50px;">  
  <img src="docs/images/logoGeneweb.jpeg" alt="picture Legacy" width="369" height="136" style="margin-right: 50px;">  
</div>  

---

## Table of contents

[The purpose of the project 👽](#purpose_project)<br />
[Project subject 📄](#subject_project)<br />
[Rules for conventional commits ➕](#conventionnal_commit)<br />
[Requirements 🔧](#requirements)<br />
[Usage 🧠](#usage)<br />
[Architecture 🏗️](#architecture)<br />
[Contributors 👋](#contributors)<br />
[License 🔑](#license)<br />

---

## <a id="purpose_project"></a> The purpose of the project 👽

**Legacy** is a modernization effort of the well-known genealogy software **Geneweb**, originally written in **OCaml**.
Our mission is to **analyze**, **refactor**, and **extend** the core of Geneweb by developing **Python-based tools** and services around it, without altering its core mechanisms.

The project focuses on:

* Understanding Geneweb’s internal logic and data structure.
* Building a **modern Python layer** for analysis, automation, and new features.
* Ensuring **code quality**, **test coverage**, and **security** through modern DevOps practices.
* Producing detailed **documentation** to ensure maintainability and future scalability.

Ultimately, Legacy bridges **heritage software engineering** and **modern software architecture**.

---

## <a id="subject_project"></a> Project subject 📄

[Change the past, test the present, secure the future!](https://intra.epitech.eu/module/2025/G-ING-900/PAR-9-1/acti-705069/project/file/G-ING-900_legacy.pdf)

The goal: to bring legacy software into the modern era, following the best standards in **Python development**, **security**, and **QA**.

---

## <a id="conventionnal_commit"></a> Rules for conventional commits ➕

See the document describing our commit message conventions:
👉 [Conventional Commit Rules](docs/conventionnalCommit.md)

---

## <a id="requirements"></a> Requirements 🔧

You need:

* **Python 3.10+**
* **Poetry** (or `pip` for manual dependency installation)
* **SQLite3** (used as a lightweight local database)
* (Optional) **Geneweb (OCaml)** for data comparison and migration testing

### Install dependencies

```bash
poetry install
# or
pip install -r requirements.txt
```

---

## <a id="usage"></a> Usage 🧠

To run the project:

```bash
python3 -m src
```

You can also run specific modules:

```bash
python3 -m src.database
python3 -m src.parser
```

For debugging or development, set the environment variable:

```bash
export PYTHONPATH=src
```

---

## <a id="architecture"></a> Architecture 🏗️

```
Legacy-Project/
├── docs/
├── examples_files/
├── LICENSE
├── README.md
├── requirements.txt
├── src/
│   ├── consang/
│   │   ├── cousin_degree/
│   ├── models/
│   │   ├── family/
│   │   └── person/
│   ├── parsers/
│   │   ├── ged/
│   │   │   └── mixins/
│   │   ├── gw/
│   └── sosa/
├── tests/
│   ├── consang/
│   ├── fixtures/
│   │   ├── consang/
│   │   │   ├── cousin_degrees/
│   │   │   ├── full/
│   │   └── sosa/
│   ├── parsers/
│   │   ├── ged/
│   │   └── gw/
│   └── sosa/
└── tools/
```

---

## <a id="contributors"></a> Contributors 👋

| [<img src="https://github.com/Steci.png?size=85" width=85><br><sub>Léa Guillemard</sub>](https://github.com/Steci) | [<img src="https://github.com/Criticat02.png?size=85" width=85><br><sub>Alessandro Tosi</sub>](https://github.com/Criticat02) | [<img src="https://github.com/laurentjiang.png?size=85" width=85><br><sub>Laurent Jiang</sub>](https://github.com/laurentjiang) | [<img src="https://github.com/Pierrelouisleroy.png?size=85" width=85><br><sub>Pierre-Louis Leroy</sub>](https://github.com/Pierrelouisleroy) | [<img src="https://github.com/Tomi-Tom.png?size=85" width=85><br><sub>Tom Bariteau Peter</sub>](https://github.com/Tomi-Tom) |
| :----------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------: |

📫
[lea.guillemard@epitech.eu](mailto:lea.guillemard@epitech.eu)
[alessandro.tosi@epitech.eu](mailto:alessandro.tosi@epitech.eu)
[laurent.jiang@epitech.eu](mailto:laurent.jiang@epitech.eu)
[pierre-louis.leroy@epitech.eu](mailto:pierre-louis.leroy@epitech.eu)
[tom.bariteau-peter@epitech.eu](mailto:tom.bariteau-peter@epitech.eu)

---

## <a id="license"></a> License 🔑

This project is licensed under the [MIT License](LICENSE).
s