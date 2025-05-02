# Data Center RAG Chatbot

A modular Python chatbot using Retrieval Augmented Generation (RAG) with Ollama/Gemma to answer questions about a SQLite database containing data-center information.

## Overview

This chatbot provides an interactive interface for querying information about data centers stored in a SQLite database. It uses RAG (Retrieval Augmented Generation) technology to combine information retrieval from both the database and a vector store with generative capabilities of the Gemma language model via Ollama.

## Features

- Interactive text-based conversational interface
- Database querying using natural language
- Automatic conversion of natural language to SQL queries
- Retrieval Augmented Generation (RAG) for combining database content with LLM capabilities
- Vector storage for semantic search of previously retrieved information
- Conversational context tracking for follow-up questions
- Support for direct SQL queries
- Handling of greetings and small talk

## Prerequisites

- Python 3.9+
- Ollama installed and running with the Gemma model
- Required Python packages:
  - langchain
  - sentence-transformers
  - faiss-cpu
  - pandas
  - numpy
  - sqlite3
  - requests

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/datacenter-rag-chatbot.git
cd datacenter-rag-chatbot
