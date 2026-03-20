# ⚽ GlobalFootballVault Backend API

Production-ready **Django REST API backend** for a football-based platform supporting user management, subscriptions, raffles, ticketing, and secure payment workflows.

🌐 **Live Platform**: https://globalfootballvault.com/

🎨 Design & Product Flow (Figma)

Interactive UI/UX design and product flow for the system:

🔗 https://www.figma.com/design/xgmdqtgLxXJYb6weTmR271/samif6-%7C%7C-AI-Chatbot---Website-Development-Project?node-id=1-2&p=f&t=icXDbpRuj1UrinSC-0

---

## 📌 Overview

GlobalFootballVault is a modular backend system built using **Django 5.x** and **Django REST Framework**, designed for scalability and real-world deployment.

The system includes:

* Secure authentication (JWT)
* Subscription & ticketing modules
* Raffle system
* Payment integration (Stripe)
* Async task handling (Celery + Redis)
* Structured logging & environment-based configuration

👉 The backend powers the live production system:
**https://globalfootballvault.com/**

---

## 🧠 Core Capabilities

* 🔐 JWT Authentication (SimpleJWT)
* 👤 Custom User Model (`account.UserAuth`)
* 🎟️ Ticket Management System
* 🎁 Raffle System
* 💳 Stripe Payment Integration
* 📦 Subscription Handling
* 📧 Email System (SMTP)
* ⚡ Async Tasks (Celery + Redis)
* 📊 API Schema (drf-spectacular / Swagger)
* 🧾 Logging System (Rotating File Logs)

---

## 🏗️ Architecture Overview

```id="arch2"
Client (Web / Mobile)
        ↓
Live Frontend (globalfootballvault.com)
        ↓
Django REST API (DRF Backend)
        ↓
----------------------------------------
| Auth Layer (JWT + Custom User)        |
| Business Modules                      |
|   - Subscription                      |
|   - Tickets                           |
|   - Raffle                            |
| Payment Layer (Stripe API)            |
| Async Workers (Celery + Redis)        |
----------------------------------------
        ↓
Database (PostgreSQL via DATABASE_URL)
        ↓
External Services:
    - Stripe API
    - SMTP Email Server
    - Redis (Broker + Cache)
```

---

## ⚙️ Tech Stack

| Category      | Technology                  |
| ------------- | --------------------------- |
| Language      | Python 3.11                 |
| Framework     | Django 5.x                  |
| API Layer     | Django REST Framework       |
| Auth          | Simple JWT                  |
| Database      | PostgreSQL                  |
| Async Tasks   | Celery + Redis              |
| Payments      | Stripe API                  |
| API Docs      | drf-spectacular             |
| CORS Handling | django-cors-headers         |
| Logging       | Timed Rotating File Handler |

---

## 📁 Project Structure

```id="struct2"
SAMI6_FOOTBALL/
│
├── account/
├── subscription/
├── tickets/
├── raffle/
├── privacysafety/
│
├── core/
├── media/
├── static/
├── logs/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── README.md
```

---

## 🔐 Authentication Flow

1. User registers
2. JWT token issued (access + refresh)
3. Authenticated requests use Bearer token
4. Role-based access enforced

---

## 💳 Payment Flow (Stripe)

1. User initiates payment
2. Backend creates Stripe session
3. Payment completed via Stripe
4. Webhook confirms transaction
5. Database updated

---

## ⚡ Async Processing (Celery)

* Redis used as broker + backend
* Handles:

  * Email sending
  * Background jobs
  * Payment confirmation

---

## 🧾 Logging System

* Stored in `/logs/bugsfixing.log`
* Rotates daily
* Keeps last 7 days

---

## 🌐 Environment Configuration

Create `.env` file:

```env id="env2"
SECRET_KEY=your-secret-key
DEBUG=False

DATABASE_URL=postgres://user:password@host:port/dbname

EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password

STRIPE_SECRET_KEY=your-key
STRIPE_PUBLISHABLE_KEY=your-key
STRIPE_WEBHOOK_SECRET=your-secret
```

---

## 🚀 Installation & Setup

### Clone Repository

```bash id="cmd8"
git clone https://github.com/techbyabrar/globalfootballvault.git
cd SAMI6_FOOTBALL
```

### Setup Environment

```bash id="cmd9"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Project

```bash id="cmd10"
python manage.py migrate
python manage.py runserver
```

---

## 📡 API Documentation

Swagger UI available at:

```id="api2"
/api/schema/swagger-ui/
```

---

## 📸 Screenshots

Store images in:

```id="img2"
assets/images/
```

Example:

```md id="img3"
![Dashboard](assets/images/dashboard.png)
```

---

## 🧪 Future Improvements

* Docker production optimization
* API rate limiting
* Redis caching layer
* Microservices architecture
* AI integration (RAG systems)

---

## 🤝 Contribution

Pull requests are welcome.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Abrar (TechbyAbrar)**
Backend Engineer | Django | FastAPI | System Design


---
