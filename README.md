# 🚗 NHTSA Vehicle Safety Data Pipeline

A production-style data engineering project that ingests, processes, and models **vehicle safety data** from the National Highway Traffic Safety Administration (NHTSA) using a modern **ELT pipeline** and **Medallion Architecture**.

---

## 📌 Project Overview

This project demonstrates end-to-end data engineering skills by building a scalable pipeline that:

* Extracts data from **NHTSA public APIs**
* Stores raw data in a PostgreSQL database (Supabase)
* Transforms data through **Bronze → Silver → Gold layers**
* Produces analytics-ready datasets for dashboards and reporting
* Automates workflows using **GitHub Actions**

The goal is to simulate a **real-world production data pipeline** while remaining **low-cost or free to operate**.

---

## 🏗️ Architecture

```text
NHTSA API
   ↓
Python Ingestion Layer (GitHub Actions)
   ↓
Supabase (Postgres)

Bronze Layer (Raw JSON)
   ↓
Silver Layer (Cleaned & Structured)
   ↓
Gold Layer (Star Schema / Analytics)

   ↓
Power BI Dashboard / Portfolio Site
```

---

## 🧱 Medallion Architecture

### 🥉 Bronze Layer (Raw Data)

* Stores raw API responses (JSON)
* Append-only ingestion
* Minimal transformation
* Source of truth for auditing and reprocessing

### 🥈 Silver Layer (Cleaned Data)

* Normalized and validated data
* Schema enforcement using `pydantic`
* Deduplication and data quality checks

### 🥇 Gold Layer (Analytics-Ready)

* Dimensional modeling (star schema)
* Fact and dimension tables
* Optimized for reporting and dashboards

---

## 🧰 Tech Stack

**Languages & Libraries**

* Python 3.11+
* `httpx` (API requests)
* `pydantic` (data validation)
* `psycopg` / SQLAlchemy (Postgres access)

**Data & Storage**

* Supabase (PostgreSQL)

**DevOps & Automation**

* GitHub Actions (scheduled workflows)
* CI/CD pipelines for ingestion & transformation

**Testing & Quality**

* `pytest` (unit & integration tests)
* `pytest-cov` (coverage)
* `ruff` (linting)
* `mypy` (type checking)

**Visualization (Planned)**

* Power BI (dashboard integration)

---

## 📡 Data Sources

Primary data is sourced from:

* NHTSA Recalls API
* NHTSA Complaints API
* NHTSA Vehicle Safety datasets

These datasets include:

* Vehicle recalls
* Consumer complaints
* Manufacturer communications
* Safety investigations

---

## 📂 Project Structure

```text
portfolio-nhtsa/
│
├── src/
│   └── nhtsa_pipeline/
│       ├── clients/        # API clients
│       ├── ingestion/      # Bronze ingestion logic
│       ├── transforms/     # Silver & Gold transformations
│       ├── db/             # Database connections
│       ├── models/         # Pydantic schemas
│       └── config/         # Configuration
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── sql/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── .github/workflows/
│   └── ci.yml
│
├── README.md
└── pyproject.toml
```

---

## 🔄 Pipeline Workflow

### 1. Ingestion

* Scheduled GitHub Actions job
* Pulls data from NHTSA APIs
* Writes raw JSON to Bronze tables

### 2. Transformation

* Bronze → Silver: cleaning, normalization, validation
* Silver → Gold: dimensional modeling

### 3. Data Quality

* Schema validation with `pydantic`
* Test coverage on transformations
* CI pipeline enforces quality checks

---

## 🧪 Testing Strategy

This project follows a **test-driven development (TDD)** approach:

* Unit tests for API clients and transformations
* Mocked API responses for deterministic testing
* Integration tests for database interactions
* Code coverage tracking via CI pipeline

Example scenarios tested:

* API success and failure responses
* Rate limiting (HTTP 429)
* Invalid data handling
* Schema validation errors

---

## ⚙️ CI/CD Automation

GitHub Actions pipelines:

* ✅ Run tests and coverage checks
* ✅ Enforce linting and type safety
* 🔄 Scheduled data ingestion jobs
* 🔄 Automated transformations

---

## 📊 Planned Data Model (Gold Layer)

Example star schema:

```text
dim_vehicle
dim_manufacturer
dim_date

fact_recall
fact_complaint
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/portfolio-nhtsa.git
cd portfolio-nhtsa
```

### 2. Set up environment

```bash
cp .env.example .env
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Run tests

```bash
pytest
```

---

## 🌱 Future Enhancements

* Incremental data loading strategies
* Data versioning and lineage tracking
* Dashboard embedding in portfolio site
* API layer for serving processed data
* Cost monitoring and optimization
* Real-time ingestion capabilities

---

## 💡 Why This Project Matters

This project showcases:

* End-to-end data pipeline design
* Real-world data modeling (Medallion + Star Schema)
* CI/CD and automation
* Test-driven development practices
* Cloud-native architecture (low-cost)

---

## 📜 License

This project is licensed under the MIT License.

---

## 👤 Author

Built as part of a technical portfolio to demonstrate modern data engineering and analytics capabilities.
