import os

base_dir = r"c:\Users\wwwja\Downloads\New folder\student-management-app"

files = {
    "backend/package.json": """{
  "name": "student-management-backend",
  "version": "1.0.0",
  "description": "Backend API for Student Management App",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express": "^4.18.2",
    "jsonwebtoken": "^9.0.2",
    "mysql2": "^3.6.1",
    "morgan": "^1.10.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}""",

    "backend/server.js": """const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const dotenv = require('dotenv');
const userRoutes = require('./routes/userRoutes');
const studentRoutes = require('./routes/studentRoutes');
const { errorHandler } = require('./middleware/errorMiddleware');

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Routes
app.use('/api/users', userRoutes);
app.use('/api/students', studentRoutes);

// Error Handling Middleware
app.use(errorHandler);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});""",

    "backend/config/db.js": """const mysql = require('mysql2/promise');
const dotenv = require('dotenv');

dotenv.config();

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'student_db',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

module.exports = pool;""",

    "backend/middleware/authMiddleware.js": """const jwt = require('jsonwebtoken');

const protect = (req, res, next) => {
  let token;
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    try {
      token = req.headers.authorization.split(' ')[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET || 'secret');
      req.user = decoded;
      next();
    } catch (error) {
      res.status(401).json({ message: 'Not authorized, token failed' });
    }
  }

  if (!token) {
    res.status(401).json({ message: 'Not authorized, no token' });
  }
};

module.exports = { protect };""",

    "backend/middleware/errorMiddleware.js": """const errorHandler = (err, req, res, next) => {
  const statusCode = res.statusCode ? res.statusCode : 500;
  res.status(statusCode).json({
    message: err.message,
    stack: process.env.NODE_ENV === 'production' ? null : err.stack,
  });
};

module.exports = { errorHandler };""",

    "backend/routes/userRoutes.js": """const express = require('express');
const router = express.Router();
const { registerUser, loginUser } = require('../controllers/userController');

router.post('/register', registerUser);
router.post('/login', loginUser);

module.exports = router;""",

    "backend/routes/studentRoutes.js": """const express = require('express');
const router = express.Router();
const { getStudents, getStudentById, createStudent, updateStudent, deleteStudent } = require('../controllers/studentController');
const { protect } = require('../middleware/authMiddleware');

router.route('/')
  .get(protect, getStudents)
  .post(protect, createStudent);

router.route('/:id')
  .get(protect, getStudentById)
  .put(protect, updateStudent)
  .delete(protect, deleteStudent);

module.exports = router;""",

    "backend/controllers/userController.js": """const pool = require('../config/db');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const generateToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET || 'secret', { expiresIn: '30d' });
};

const registerUser = async (req, res) => {
  const { username, email, password } = req.body;
  if (!username || !email || !password) {
    return res.status(400).json({ message: 'Please add all fields' });
  }

  try {
    const [existing] = await pool.execute('SELECT * FROM users WHERE email = ? OR username = ?', [email, username]);
    if (existing.length > 0) {
      return res.status(400).json({ message: 'User already exists' });
    }

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const [result] = await pool.execute(
      'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
      [username, email, hashedPassword]
    );

    res.status(201).json({
      id: result.insertId,
      username,
      email,
      token: generateToken(result.insertId)
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

const loginUser = async (req, res) => {
  const { email, password } = req.body;
  try {
    const [users] = await pool.execute('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (isMatch) {
      res.json({
        id: user.id,
        username: user.username,
        email: user.email,
        token: generateToken(user.id)
      });
    } else {
      res.status(400).json({ message: 'Invalid credentials' });
    }
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

module.exports = { registerUser, loginUser };""",

    "backend/controllers/studentController.js": """const pool = require('../config/db');

const logActivity = async (userId, action, details) => {
    try {
        await pool.execute('INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)', [userId, action, details]);
    } catch(e) {
        console.error('Log failed', e);
    }
};

const getStudents = async (req, res) => {
  try {
    const { search } = req.query;
    let query = 'SELECT * FROM students';
    let params = [];
    
    if (search) {
      query += ' WHERE student_name LIKE ? OR student_qual LIKE ?';
      params = [`%${search}%`, `%${search}%`];
    }
    
    const [rows] = await pool.execute(query, params);
    res.json(rows);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

const getStudentById = async (req, res) => {
  try {
    const [rows] = await pool.execute('SELECT * FROM students WHERE student_id = ?', [req.params.id]);
    if (rows.length === 0) return res.status(404).json({ message: 'Student not found' });
    res.json(rows[0]);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

const createStudent = async (req, res) => {
  const { student_name, student_addr, student_age, student_qual, student_percent, student_year_passed } = req.body;
  if (!student_name || !student_addr || !student_age || !student_qual || !student_percent || !student_year_passed) {
    return res.status(400).json({ message: 'Please provide all fields' });
  }

  try {
    const [result] = await pool.execute(
      'INSERT INTO students (student_name, student_addr, student_age, student_qual, student_percent, student_year_passed) VALUES (?, ?, ?, ?, ?, ?)',
      [student_name, student_addr, student_age, student_qual, student_percent, student_year_passed]
    );
    await logActivity(req.user.id, 'CREATE_STUDENT', `Created student ${student_name}`);
    res.status(201).json({ id: result.insertId, ...req.body });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

const updateStudent = async (req, res) => {
  const { student_name, student_addr, student_age, student_qual, student_percent, student_year_passed } = req.body;
  
  try {
    const [result] = await pool.execute(
      'UPDATE students SET student_name=?, student_addr=?, student_age=?, student_qual=?, student_percent=?, student_year_passed=? WHERE student_id=?',
      [student_name, student_addr, student_age, student_qual, student_percent, student_year_passed, req.params.id]
    );
    if (result.affectedRows === 0) return res.status(404).json({ message: 'Student not found' });
    
    await logActivity(req.user.id, 'UPDATE_STUDENT', `Updated student ID ${req.params.id}`);
    res.json({ id: req.params.id, ...req.body });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

const deleteStudent = async (req, res) => {
  try {
    const [result] = await pool.execute('DELETE FROM students WHERE student_id = ?', [req.params.id]);
    if (result.affectedRows === 0) return res.status(404).json({ message: 'Student not found' });
    
    await logActivity(req.user.id, 'DELETE_STUDENT', `Deleted student ID ${req.params.id}`);
    res.json({ message: 'Student removed' });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

module.exports = { getStudents, getStudentById, createStudent, updateStudent, deleteStudent };""",

    "backend/database/schema.sql": """CREATE DATABASE IF NOT EXISTS student_db;
USE student_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    student_addr TEXT NOT NULL,
    student_age INT NOT NULL,
    student_qual VARCHAR(100) NOT NULL,
    student_percent DECIMAL(5,2) NOT NULL,
    student_year_passed INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);""",

    "backend/.env.example": """PORT=5000
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=student_db
JWT_SECRET=your_jwt_secret_key_here
NODE_ENV=development""",

    "backend/Dockerfile": """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5000
CMD ["node", "server.js"]""",

    "frontend/index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Manager Cloud | Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
</head>
<body class="auth-bg">
    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="auth-card glassmorphism p-5 rounded-4 shadow-lg">
            <div class="text-center mb-4">
                <i class="fa-brands fa-aws fa-3x text-primary mb-3"></i>
                <h2 class="fw-bold">Cloud Dashboard</h2>
                <p class="text-muted">Sign in to manage students</p>
            </div>
            
            <div id="alertBox" class="alert d-none" role="alert"></div>

            <ul class="nav nav-pills nav-justified mb-3" id="pills-tab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="pills-login-tab" data-bs-toggle="pill" data-bs-target="#pills-login" type="button" role="tab">Login</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="pills-register-tab" data-bs-toggle="pill" data-bs-target="#pills-register" type="button" role="tab">Register</button>
                </li>
            </ul>
            
            <div class="tab-content" id="pills-tabContent">
                <!-- Login Form -->
                <div class="tab-pane fade show active" id="pills-login" role="tabpanel">
                    <form id="loginForm">
                        <div class="form-floating mb-3">
                            <input type="email" class="form-control" id="loginEmail" placeholder="name@example.com" required>
                            <label for="loginEmail">Email address</label>
                        </div>
                        <div class="form-floating mb-4">
                            <input type="password" class="form-control" id="loginPassword" placeholder="Password" required>
                            <label for="loginPassword">Password</label>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-2 fw-bold btn-animate">Sign In <i class="fa-solid fa-arrow-right ms-2"></i></button>
                    </form>
                </div>
                <!-- Register Form -->
                <div class="tab-pane fade" id="pills-register" role="tabpanel">
                    <form id="registerForm">
                        <div class="form-floating mb-3">
                            <input type="text" class="form-control" id="regUsername" placeholder="Username" required>
                            <label for="regUsername">Username</label>
                        </div>
                        <div class="form-floating mb-3">
                            <input type="email" class="form-control" id="regEmail" placeholder="name@example.com" required>
                            <label for="regEmail">Email address</label>
                        </div>
                        <div class="form-floating mb-4">
                            <input type="password" class="form-control" id="regPassword" placeholder="Password" required>
                            <label for="regPassword">Password</label>
                        </div>
                        <button type="submit" class="btn btn-success w-100 py-2 fw-bold btn-animate">Create Account</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/auth.js"></script>
</body>
</html>""",

    "frontend/dashboard.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard | Student Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
</head>
<body class="dashboard-bg dark-mode-enabled">
    <div class="d-flex" id="wrapper">
        <!-- Sidebar -->
        <div class="sidebar glassmorphism-sidebar" id="sidebar-wrapper">
            <div class="sidebar-heading text-center py-4 fs-4 fw-bold border-bottom border-secondary text-white">
                <i class="fa-brands fa-aws text-warning"></i> EduCloud
            </div>
            <div class="list-group list-group-flush my-3">
                <a href="#" class="list-group-item list-group-item-action bg-transparent text-white active"><i class="fas fa-tachometer-alt me-2"></i> Dashboard</a>
                <a href="#" class="list-group-item list-group-item-action bg-transparent text-white fw-bold"><i class="fas fa-users me-2"></i> Students</a>
                <a href="#" class="list-group-item list-group-item-action bg-transparent text-white fw-bold"><i class="fas fa-chart-line me-2"></i> Analytics</a>
                <a href="#" class="list-group-item list-group-item-action bg-transparent text-white fw-bold"><i class="fas fa-cog me-2"></i> Settings</a>
                <a href="#" id="logoutBtn" class="list-group-item list-group-item-action bg-transparent text-danger fw-bold mt-5"><i class="fas fa-power-off me-2"></i> Logout</a>
            </div>
        </div>
        
        <!-- Page Content -->
        <div id="page-content-wrapper" class="w-100">
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark py-3 px-4 shadow-sm border-bottom border-secondary">
                <div class="d-flex align-items-center">
                    <i class="fas fa-align-left fs-4 me-3 text-white" id="menu-toggle" style="cursor:pointer;"></i>
                    <h2 class="fs-4 m-0 text-white fw-bold">Student Management</h2>
                </div>
                <div class="ms-auto d-flex align-items-center">
                    <span class="text-white me-3 fw-semibold" id="userWelcome">Welcome, User</span>
                    <img src="https://ui-avatars.com/api/?name=User&background=0D8ABC&color=fff" alt="Profile" class="rounded-circle shadow-sm" width="40">
                </div>
            </nav>

            <div class="container-fluid px-4 py-5">
                <div class="row g-4 mb-4">
                    <div class="col-md-3">
                        <div class="card stat-card shadow-sm border-0 bg-primary text-white glass-card">
                            <div class="card-body">
                                <h5 class="card-title fw-semibold">Total Students</h5>
                                <h2 class="display-4 fw-bold" id="totalStudents">0</h2>
                                <p class="mb-0 text-white-50"><i class="fas fa-arrow-up text-success"></i> Real-time DB count</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card shadow border-0 bg-dark text-white glass-card">
                    <div class="card-header bg-transparent border-bottom border-secondary d-flex justify-content-between align-items-center py-3">
                        <h4 class="mb-0 fw-bold">Students Database</h4>
                        <div class="d-flex gap-2">
                            <input type="text" id="searchInput" class="form-control bg-dark text-white border-secondary" placeholder="Search students...">
                            <button class="btn btn-warning fw-bold text-dark" data-bs-toggle="modal" data-bs-target="#studentModal" id="addBtn"><i class="fas fa-plus"></i> Add New</button>
                        </div>
                    </div>
                    <div class="card-body table-responsive">
                        <table class="table table-dark table-hover align-middle custom-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Address</th>
                                    <th>Age</th>
                                    <th>Qualification</th>
                                    <th>Percentage</th>
                                    <th>Passed Year</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="studentTableBody">
                                <!-- Data populated by JS -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Student Modal (Add/Edit) -->
    <div class="modal fade" id="studentModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-dark text-white border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title fw-bold" id="modalTitle">Add Student</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="studentForm">
                        <input type="hidden" id="studentId">
                        <div class="form-floating mb-3">
                            <input type="text" class="form-control" id="sName" placeholder="Name" required>
                            <label for="sName">Full Name</label>
                        </div>
                        <div class="form-floating mb-3">
                            <input type="text" class="form-control" id="sAddr" placeholder="Address" required>
                            <label for="sAddr">Address</label>
                        </div>
                        <div class="row g-2 mb-3">
                            <div class="col-md-6 form-floating">
                                <input type="number" class="form-control" id="sAge" placeholder="Age" required min="10" max="100">
                                <label for="sAge" class="ms-1">Age</label>
                            </div>
                            <div class="col-md-6 form-floating">
                                <input type="text" class="form-control" id="sQual" placeholder="Qualification" required>
                                <label for="sQual" class="ms-1">Qualification</label>
                            </div>
                        </div>
                        <div class="row g-2 mb-4">
                            <div class="col-md-6 form-floating">
                                <input type="number" step="0.01" class="form-control" id="sPercent" placeholder="Percentage" required min="0" max="100">
                                <label for="sPercent" class="ms-1">Percentage</label>
                            </div>
                            <div class="col-md-6 form-floating">
                                <input type="number" class="form-control" id="sYear" placeholder="Year Passed" required min="1900" max="2100">
                                <label for="sYear" class="ms-1">Year Passed</label>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-warning w-100 py-2 fw-bold text-dark btn-animate">Save Student Record</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/app.js"></script>
</body>
</html>""",

    "frontend/css/style.css": """:root {
    --primary-color: #00a8ff;
    --secondary-color: #fbc531;
    --dark-bg: #121212;
    --dark-surface: #1e272e;
    --text-main: #f5f6fa;
}

body {
    font-family: 'Inter', sans-serif;
}

.auth-bg {
    background: linear-gradient(135deg, #1e272e 0%, #2f3640 100%);
    min-height: 100vh;
}

.dashboard-bg {
    background-color: var(--dark-bg);
}

.glassmorphism {
    background: rgba(30, 39, 46, 0.7);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-main);
}

.glassmorphism-sidebar {
    background: rgba(18, 18, 18, 0.95);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.auth-card {
    width: 100%;
    max-width: 450px;
}

/* Sidebar */
#wrapper {
    overflow-x: hidden;
}

#sidebar-wrapper {
    min-height: 100vh;
    width: 250px;
    transition: margin .25s ease-out;
}

#sidebar-wrapper .list-group-item {
    border: none;
    padding: 1rem 1.5rem;
    transition: all 0.3s;
}

#sidebar-wrapper .list-group-item:hover,
#sidebar-wrapper .list-group-item.active {
    background-color: rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px;
    margin: 0 10px;
}

#page-content-wrapper {
    min-width: 100vw;
}

@media (min-width: 768px) {
    #sidebar-wrapper {
        margin-left: 0;
    }
    #page-content-wrapper {
        min-width: 0;
        width: 100%;
    }
    #wrapper.toggled #sidebar-wrapper {
        margin-left: -250px;
    }
}

.glass-card {
    background: rgba(30, 39, 46, 0.6) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}

.custom-table th {
    background-color: rgba(0, 0, 0, 0.2);
    color: var(--secondary-color);
    font-weight: 600;
    border-color: rgba(255, 255, 255, 0.05);
}

.custom-table td {
    border-color: rgba(255, 255, 255, 0.05);
}

.custom-table tbody tr {
    transition: all 0.2s;
}

.custom-table tbody tr:hover {
    background-color: rgba(255, 255, 255, 0.05);
    transform: scale(1.01);
}

.btn-animate {
    transition: transform 0.2s;
}

.btn-animate:hover {
    transform: translateY(-2px);
}

.form-floating > label {
    color: #a4b0be;
}
.form-floating > .form-control {
    background-color: rgba(0,0,0,0.2);
    border-color: rgba(255,255,255,0.1);
    color: white;
}
.form-floating > .form-control:focus {
    background-color: rgba(0,0,0,0.4);
    color: white;
    box-shadow: 0 0 0 0.25rem rgba(0,168,255,0.25);
    border-color: rgba(0,168,255,0.5);
}

/* Fix for Webkit autofill in dark mode */
input:-webkit-autofill,
input:-webkit-autofill:hover, 
input:-webkit-autofill:focus, 
input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 30px #2f3640 inset !important;
    -webkit-text-fill-color: white !important;
}""",

    "frontend/js/auth.js": """const API_URL = 'http://localhost:5000/api';

const alertBox = document.getElementById('alertBox');
const showAlert = (msg, type) => {
    alertBox.className = `alert alert-${type}`;
    alertBox.textContent = msg;
    alertBox.classList.remove('d-none');
    setTimeout(() => alertBox.classList.add('d-none'), 3000);
};

if(localStorage.getItem('token')) {
    window.location.href = 'dashboard.html';
}

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('username', data.username);
            window.location.href = 'dashboard.html';
        } else {
            showAlert(data.message || 'Login failed', 'danger');
        }
    } catch (err) {
        showAlert('Network error', 'danger');
    }
});

document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    try {
        const res = await fetch(`${API_URL}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('username', data.username);
            window.location.href = 'dashboard.html';
        } else {
            showAlert(data.message || 'Registration failed', 'danger');
        }
    } catch (err) {
        showAlert('Network error', 'danger');
    }
});""",

    "frontend/js/app.js": """const API_URL = 'http://localhost:5000/api';
const token = localStorage.getItem('token');
const username = localStorage.getItem('username');

if (!token) {
    window.location.href = 'index.html';
}

document.getElementById('userWelcome').textContent = `Welcome, ${username}`;

// Set avatar dynamically
document.querySelector('img[alt="Profile"]').src = `https://ui-avatars.com/api/?name=${username}&background=0D8ABC&color=fff&rounded=true`;

document.getElementById('menu-toggle').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('wrapper').classList.toggle('toggled');
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = 'index.html';
});

const studentModal = new bootstrap.Modal(document.getElementById('studentModal'));
const studentForm = document.getElementById('studentForm');
let isEditing = false;

const fetchStudents = async (searchQuery = '') => {
    try {
        const url = searchQuery ? `${API_URL}/students?search=${searchQuery}` : `${API_URL}/students`;
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.status === 401) {
            localStorage.clear();
            window.location.href = 'index.html';
            return;
        }

        const data = await res.json();
        renderTable(data);
        document.getElementById('totalStudents').textContent = data.length;
    } catch (err) {
        console.error('Error fetching students:', err);
    }
};

const renderTable = (students) => {
    const tbody = document.getElementById('studentTableBody');
    tbody.innerHTML = '';
    
    students.forEach(student => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="text-secondary">#${student.student_id}</td>
            <td class="fw-bold">${student.student_name}</td>
            <td>${student.student_addr}</td>
            <td>${student.student_age}</td>
            <td><span class="badge bg-primary px-2 py-1 rounded-pill">${student.student_qual}</span></td>
            <td>${student.student_percent}%</td>
            <td>${student.student_year_passed}</td>
            <td>
                <button class="btn btn-sm btn-outline-info me-1" onclick="editStudent(${student.student_id})"><i class="fas fa-edit"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteStudent(${student.student_id})"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
};

document.getElementById('addBtn').addEventListener('click', () => {
    isEditing = false;
    document.getElementById('modalTitle').textContent = 'Add New Student';
    studentForm.reset();
    document.getElementById('studentId').value = '';
});

studentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const studentData = {
        student_name: document.getElementById('sName').value,
        student_addr: document.getElementById('sAddr').value,
        student_age: document.getElementById('sAge').value,
        student_qual: document.getElementById('sQual').value,
        student_percent: document.getElementById('sPercent').value,
        student_year_passed: document.getElementById('sYear').value
    };

    const id = document.getElementById('studentId').value;
    const url = isEditing ? `${API_URL}/students/${id}` : `${API_URL}/students`;
    const method = isEditing ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(studentData)
        });
        
        if (res.ok) {
            studentModal.hide();
            fetchStudents();
        } else {
            alert('Operation failed');
        }
    } catch (err) {
        console.error(err);
    }
});

window.editStudent = async (id) => {
    try {
        const res = await fetch(`${API_URL}/students/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const student = await res.json();
        
        isEditing = true;
        document.getElementById('modalTitle').textContent = 'Edit Student';
        document.getElementById('studentId').value = student.student_id;
        document.getElementById('sName').value = student.student_name;
        document.getElementById('sAddr').value = student.student_addr;
        document.getElementById('sAge').value = student.student_age;
        document.getElementById('sQual').value = student.student_qual;
        document.getElementById('sPercent').value = student.student_percent;
        document.getElementById('sYear').value = student.student_year_passed;
        
        studentModal.show();
    } catch (err) {
        console.error(err);
    }
};

window.deleteStudent = async (id) => {
    if(confirm('Are you sure you want to delete this student record?')) {
        try {
            await fetch(`${API_URL}/students/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            fetchStudents();
        } catch(err) {
            console.error(err);
        }
    }
};

let searchTimeout;
document.getElementById('searchInput').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        fetchStudents(e.target.value);
    }, 500);
});

// Initial load
fetchStudents();""",

    "frontend/Dockerfile": """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]""",

    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: student_mysql
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: student_db
    ports:
      - "3306:3306"
    volumes:
      - ./backend/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
      - db_data:/var/lib/mysql
    networks:
      - student_network

  backend:
    build: ./backend
    container_name: student_backend
    environment:
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=rootpassword
      - DB_NAME=student_db
      - JWT_SECRET=super_secret_jwt_key
      - PORT=5000
    ports:
      - "5000:5000"
    depends_on:
      - db
    networks:
      - student_network

  frontend:
    build: ./frontend
    container_name: student_frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - student_network

networks:
  student_network:
    driver: bridge

volumes:
  db_data:""",

    "aws-lambda/activity-logger.js": """// AWS Lambda Function: Activity Logger via API Gateway / SQS / Direct Invocation
// Connects to RDS MySQL to log events

const mysql = require('mysql2/promise');

exports.handler = async (event) => {
    // Expected event structure: { user_id, action, details }
    
    const dbConfig = {
        host: process.env.DB_HOST,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
    };
    
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        
        let logsToInsert = [];
        
        // Handle SQS batch events if triggered by SQS
        if (event.Records) {
            for (const record of event.Records) {
                const body = JSON.parse(record.body);
                logsToInsert.push([body.user_id, body.action, body.details]);
            }
        } else {
            // Direct invocation
            logsToInsert.push([event.user_id, event.action, event.details]);
        }
        
        for (const log of logsToInsert) {
            await connection.execute(
                'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
                log
            );
        }
        
        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Activity logged successfully' }),
        };
    } catch (error) {
        console.error('Error logging activity:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message }),
        };
    } finally {
        if (connection) {
            await connection.end();
        }
    }
};""",

    "README.md": """# Student Management Web Application (Cloud-Native)

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
Please refer to `aws-deployment-guide.md` for complete AWS cloud infrastructure setup instructions.""",

    "aws-deployment-guide.md": """# AWS Deployment Guide

This guide explains how to deploy the Student Management Application onto AWS following enterprise best practices.

## Architecture Overview
- **VPC:** 1 Public Subnet (ALB, Frontend EC2), 2 Private Subnets (Backend EC2, RDS Database).
- **Compute:** EC2 instances managed by an Auto Scaling Group (ASG).
- **Database:** AWS RDS for MySQL (Multi-AZ for high availability).
- **Load Balancing:** Application Load Balancer (ALB) routing HTTP/HTTPS traffic.
- **Serverless:** AWS Lambda for asynchronous logging (integrated with API Gateway or SQS).
- **Storage:** S3 for storing profile pictures (if implemented in future).

## Step-by-Step Deployment

### 1. Networking (VPC Setup)
1. Navigate to VPC Dashboard -> Create VPC.
2. Use the "VPC and more" wizard to create a VPC with public and private subnets, along with a NAT Gateway (for backend internet access) and an Internet Gateway.

### 2. Database (AWS RDS)
1. Go to RDS Dashboard -> Create database.
2. Select **MySQL**.
3. Choose the Free Tier or Production template.
4. Set credentials (e.g., `admin` / `rootpassword`).
5. Place the DB in the **Private Subnet** of your VPC.
6. Make sure the security group allows inbound traffic on port 3306 from your Backend EC2 Security Group.
7. Connect to RDS using an EC2 jump server or MySQL Workbench and run the `schema.sql` script to create tables.

### 3. Compute & Scaling (EC2 & ASG)
1. **Launch Template:** Create a launch template for the Backend API.
   - AMI: Ubuntu 22.04 LTS or Amazon Linux 2023.
   - User Data script to install Node.js, clone repository, run `npm install`, and start server using PM2.
   - Assign a role with CloudWatch access.
2. **Auto Scaling Group:** Create an ASG using the template, targeting the private subnets. Set desired capacity to 2.
3. **Application Load Balancer (ALB):** Create an ALB in the public subnets. Route traffic to the Backend ASG Target Group.

### 4. Frontend Deployment (Options)
- **Option A (S3 + CloudFront):** Host the static `/frontend` files in an S3 bucket and distribute via CloudFront CDN. Update `API_URL` in `app.js` to point to the ALB DNS name.
- **Option B (EC2 with Nginx):** Deploy a separate EC2 instance in the public subnet running Nginx. Copy frontend files to `/usr/share/nginx/html`.

### 5. Serverless Logging (AWS Lambda)
1. Go to Lambda Dashboard -> Create Function.
2. Choose Node.js 18.x.
3. Paste the code from `aws-lambda/activity-logger.js`.
4. Add environment variables for RDS connection (`DB_HOST`, `DB_USER`, etc.).
5. Ensure the Lambda function's Execution Role has VPC access and RDS connect permissions.

### 6. DNS and SSL (Route 53 & ACM)
1. Request a public SSL certificate in AWS Certificate Manager (ACM).
2. Create an Alias record in Route 53 pointing your custom domain (e.g., `api.example.com`) to the ALB.

## CI/CD Pipeline (GitHub Actions or AWS CodePipeline)
To automate this, configure a pipeline to:
1. Build Docker images.
2. Push to Amazon ECR.
3. Trigger an EC2 Auto Scaling instance refresh or ECS service update."""
}

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath.replace('/', os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Successfully generated all {len(files)} files.")
