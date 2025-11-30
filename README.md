# Biosense-ecorewards

♻️ EcoRewards — AI Waste Segregation System

🚀 AI-powered waste classification using a deep learning model + FastAPI backend + reward points gamification system.
Classify waste images into Biodegradable or Non-Biodegradable, track recycling impact, and earn eco points.


✨ Features
Feature	Description
🔐 Secure Login & Signup	JWT Authentication (Register once & login from anywhere)
🧠 Waste Image Classification	AI model predicts waste type with confidence score
🏆 Reward System	Users earn eco points for every classification
📊 User Stats Dashboard	Tracks total classifications, streak, bio vs non-bio
🕒 Classification History	Last 20 classifications saved in database
🌐 Cloud Deployable	One-link access from any system, anytime
📱 Fully Responsive UI	Modern and mobile-friendly interface
🧠 Technology Stack
🔹 Machine Learning

TensorFlow

Pretrained CNN (biosense_classifier.h5)

Image Preprocessing + Softmax predictions

🔹 Backend

FastAPI

SQLite + SQLAlchemy ORM

JWT Authentication (python-jose)

Passlib hashed password security

🔹 Frontend

HTML, CSS, JavaScript

Dynamic UI updates with Fetch API

Drag & Drop image upload

🔹 Deployment

GitHub + Render Web Service

TensorFlow CPU optimized for cloud

🏗️ Project Structure
.
├── main.py
├── database.py
├── requirements.txt
├── models/
│   ├── biosense_classifier.h5
│   └── class_names.json
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    └── index.html

🔐 Authentication Workflow

User logs in → Receives JWT Token →
Each authorized call sends:

Authorization: Bearer <TOKEN_HERE>


Token validates user session on every request.

🎯 Points System Logic
Waste Type	Example	Points Earned
Biodegradable	Food, paper, leaves	+5 Points
Non-Biodegradable	Plastic, cans, e-waste	+10 Points

Points update instantly and stored in DB ✔

🔌 API Endpoints
Method	Endpoint	Description
POST	/register	Create new user
POST	/login	Authenticate user & return token
GET	/me	Fetch user profile / stats
POST	/predict	Classify uploaded waste image
POST	/update-points	Save points + history
GET	/history	Fetch recent 20 classifications

