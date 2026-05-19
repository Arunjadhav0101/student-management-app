# Student Management Web Application (Cloud-Native)

A full-stack modern Student Management application designed for deployment on AWS. This project includes a RESTful Node.js API, a MySQL database schema, and a modern, responsive HTML/CSS/JS frontend styled with Bootstrap.

## Features
- **User Authentication:** JWT-based secure login and registration.
- **CRUD Operations:** Manage student records seamlessly.
- **Search & Filter:** Instantly find students.
- **Modern UI:** Responsive, glassmorphism-inspired dark mode dashboard.
- **Containerized:** Docker Compose support for local development.

## Tech Stack
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Backend:** Node.js, Express.js
- **Database:** MySQL
- **Cloud Readiness:** Docker, AWS EC2, RDS, Lambda

## Getting Started (Local Development)

### Prerequisites
- Docker and Docker Compose installed.

### Run with Docker
1. Clone the repository and navigate to the project directory.
2. Run: `docker-compose up --build -d`
3. Access the frontend at `http://localhost`
4. The backend API is available at `http://localhost:5000`
5. Default Database schema will be automatically created on the first run.

## API Documentation
- `POST /api/users/register` - Register a new user
- `POST /api/users/login` - Authenticate user
- `GET /api/students` - Get all students (Requires Auth)
- `POST /api/students` - Add a student (Requires Auth)
- `PUT /api/students/:id` - Edit a student (Requires Auth)
- `DELETE /api/students/:id` - Delete a student (Requires Auth)

## Deployment
Please refer to `aws-deployment-guide.md` for complete AWS cloud infrastructure setup instructions.