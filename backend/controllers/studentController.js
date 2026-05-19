const pool = require('../config/db');

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

module.exports = { getStudents, getStudentById, createStudent, updateStudent, deleteStudent };