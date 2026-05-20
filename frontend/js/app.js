const API_URL = 'http://student-alb-531848088.us-east-1.elb.amazonaws.com';
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
fetchStudents();