<div align="center">

# Anonymous Polling System

![last-commit](https://img.shields.io/github/last-commit/MahadAjmal586/Anonymous-Polling-System?style=flat&logo=git&logoColor=white&color=00c853)
![repo-top-language](https://img.shields.io/github/languages/top/MahadAjmal586/Anonymous-Polling-System?style=flat&color=00c853)
![repo-language-count](https://img.shields.io/github/languages/count/MahadAjmal586/Anonymous-Polling-System?style=flat&color=00c853)

**Built with:**

![Python](https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-0000f0.svg?style=flat&logo=websocket&logoColor=white)

<br>

A lightweight, real-time, **anonymous polling application** where anyone can create polls, vote instantly, and see live results — **no login, no database required**.

</div>

## Table of Contents

- [Project Description](#project-description)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Project Structure](#project-structure)

---

## Project Description

This project is a simple yet powerful **anonymous polling system** built for quick, real-time opinion collection.  
Users can create polls with multiple options, share them via unique IDs/links, vote anonymously, watch results update live through WebSockets, and creators can close polls when needed.

Perfect for classrooms, events, quick surveys, or fun group decisions — zero authentication, zero persistence.

## Tech Stack

- **Backend:** Python, FastAPI, WebSockets  
- **Frontend:** HTML, CSS, JavaScript (served from `frontend/` folder)  
- **No database** — fully in-memory / stateless design  
- **Server:** Uvicorn (ASGI)

## Key Features

- Fully anonymous — no login or registration needed  
- Create polls with custom question and multiple choices  
- Real-time vote updates using WebSockets  
- Live result visualization (instantly reflected for all viewers)  
- Poll creators can close voting at any time  
- Share polls easily using unique poll IDs / links  
- Lightweight and fast (no database overhead)

## Project Structure

Anonymous-Polling-System/
│
├── frontend/              # Client-side HTML, CSS, JavaScript
├── main.py                # FastAPI application + WebSocket endpoints
├── requirments.txt        # Python dependencies (note: typo — should be requirements.txt)
├── pyproject.toml         # Project metadata (optional)
├── .dockerignore
├── .idea/                 # (IDE settings — gitignore recommended)
└── README.md

