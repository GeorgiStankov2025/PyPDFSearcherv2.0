# PyPDFSearcherv2.0

**An AI-Powered PDF Search, Analysis, and Report Generation Platform**

PyPDFSearcherv2.0 is a sophisticated backend application built with FastAPI that combines advanced PDF processing capabilities with AI-driven analysis using Google's Generative AI. The platform enables users to upload PDF documents, search through their content intelligently, maintain conversations about the documents, and generate automated reports with intelligent insights.

## 🎯 Overview

This is an API service designed to streamline document management and analysis workflows. It features JWT-based authentication, asynchronous database operations, email notifications, and intelligent conversation management around PDF documents.

### Key Capabilities

- **📄 Intelligent PDF Processing**: Upload, store, and index PDF documents for efficient retrieval
- **🔍 Advanced Search Functionality**: Full-text search with semantic understanding through AI
- **🤖 AI-Powered Conversations**: Interact with your documents through natural language conversations using Google's Generative AI
- **📊 Automated Report Generation**: Generate intelligent reports based on PDF content and user queries
- **👥 User Management**: Secure authentication with JWT tokens and role-based access control (admin/user)
- **✉️ Email Notifications**: Automated email service for notifications and updates
- **🗄️ Database Integration**: PostgreSQL backend with SQLAlchemy ORM and Alembic migrations

## 🚀 Technical Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI 0.129.0 |
| **Server** | Uvicorn 0.41.0 |
| **Database** | PostgreSQL with SQLAlchemy 2.0.46 |
| **Migrations** | Alembic 1.18.4 |
| **AI Integration** | Google Generative AI, LangChain |
| **Authentication** | JWT (python-jose), Argon2 |
| **Email Service** | FastAPI-Mail, aiosmtplib |
| **Async Support** | asyncpg, anyio |
| **Validation** | Pydantic 2.12.5 |
| **Testing** | pytest, pytest-asyncio |
| **Cloud Services** | Google Cloud Storage, BigQuery, Vertex AI |

## 📋 Requirements

- **Python**: 3.8+ (version specified in `.python-version`)
- **PostgreSQL**: 12+ for database backend
- **Google Cloud Account**: For AI features and cloud services
- **SMTP Server**: For email functionality
