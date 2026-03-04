# Atome AI Customer Service Bot

This project implements an AI Customer Service Bot with RAG, Tool Use, and Meta-Agent capabilities.

## Features

1.  **Service Bot (Part 1)**:
    *   **RAG**: Answers questions from Atome Help Center.
    *   **Tools**: Checks application status and transaction status (Mocked).
    *   **Auto-fix**: Users can report mistakes, and the bot automatically adds new rules to its guidelines to fix itself.

2.  **Meta-Agent (Part 2)**:
    *   **Manager Instruction**: Managers can give natural language instructions (e.g., "Be more polite", "If user asks X, say Y") to update the bot's behavior.
    *   **Dynamic Config**: Knowledge Base URL and Guidelines are configurable via UI.

## Setup & Run

1.  **Prerequisites**:
    *   Python 3.8+
    *   Node.js 16+
    *   OpenAI API Key

2.  **Configuration**:
    *   Open `atome-bot/backend/.env`
    *   Paste your OpenAI API Key: `OPENAI_API_KEY=sk-......`

3.  **Run**:
    ```bash
    chmod +x start.sh
    ./start.sh
    ```
    *   Backend: http://localhost:8000
    *   Frontend: http://localhost:5173

## Project Structure

*   `backend/`: FastAPI + LangChain + ChromaDB
    *   `app/agent.py`: Service Bot Logic
    *   `app/manager.py`: Meta-Agent Logic
    *   `app/crawler.py`: Web Crawler
*   `frontend/`: React + Tailwind + Lucide

## Usage Guide

1.  **Chat**: Type your questions in the main chat window.
    *   Try: "What is Atome card?" (RAG)
    *   Try: "Check my application status for user 12345" (Tool)
    *   Try: "Why did my transaction 999 fail?" (Tool)
2.  **Report Mistake**: 
    *   Click "Report Mistake" under a bot response.
    *   Enter the correct behavior.
    *   Watch the "Current Guidelines" in the sidebar update automatically.
3.  **Manager Instruction**:
    *   In the sidebar, type an instruction like "Always end responses with 'Have a nice day!'".
    *   Click "Apply Instruction" and see the bot's behavior change.
