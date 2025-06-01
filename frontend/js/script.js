// Quiz state
let currentQuestion = 0;
let score = 0;
let timer;
let timeSpent = 0;
let questions = [];

// DOM Elements
const authSection = document.getElementById('auth-section');
const quizSection = document.getElementById('quiz-section');
const quizContainer = document.getElementById('quiz-container');
const leaderboardContainer = document.getElementById('leaderboard-container');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');

// Auth Functions
function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.add('hidden'));
    
    document.querySelector(`[onclick="showTab('${tab}')"]`).classList.add('active');
    document.getElementById(`${tab}-form`).classList.remove('hidden');
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = loginForm.querySelector('input[type="email"]').value;
    const password = loginForm.querySelector('input[type="password"]').value;

    try {
        const response = await fetch('http://localhost:5000/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            showQuizSection();
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        alert('Login failed. Please try again.');
    }
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = registerForm.querySelector('input[type="text"]').value;
    const email = registerForm.querySelector('input[type="email"]').value;
    const password = registerForm.querySelectorAll('input[type="password"]')[0].value;
    const confirmPassword = registerForm.querySelectorAll('input[type="password"]')[1].value;

    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
        if (response.ok) {
            alert('Registration successful! Please login.');
            showTab('login');
            registerForm.reset();
        } else {
            alert(data.message || 'Registration failed');
        }
    } catch (error) {
        alert('Registration failed. Please try again.');
    }
});

// Quiz Functions
async function startQuiz() {
    try {
        const response = await fetch('http://localhost:5000/api/questions', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        
        questions = await response.json();
        currentQuestion = 0;
        score = 0;
        timeSpent = 0;
        
        document.getElementById('score').textContent = score;
        startTimer();
        showQuestion();
        
        quizContainer.classList.remove('hidden');
        leaderboardContainer.classList.add('hidden');
    } catch (error) {
        alert('Failed to load questions. Please try again.');
    }
}

function showQuestion() {
    const question = questions[currentQuestion];
    document.getElementById('question-text').textContent = question.text;
    
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    question.options.forEach((option, index) => {
        const button = document.createElement('button');
        button.className = 'option';
        button.textContent = option;
        button.onclick = () => selectOption(index);
        optionsContainer.appendChild(button);
    });
    
    document.getElementById('next-btn').classList.toggle('hidden', currentQuestion === questions.length - 1);
    document.getElementById('submit-btn').classList.toggle('hidden', currentQuestion !== questions.length - 1);
}

function selectOption(index) {
    document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
    document.querySelectorAll('.option')[index].classList.add('selected');
}

function nextQuestion() {
    const selected = document.querySelector('.option.selected');
    if (!selected) {
        alert('Please select an answer');
        return;
    }
    
    if (questions[currentQuestion].correct === Array.from(document.querySelectorAll('.option')).indexOf(selected)) {
        score++;
        document.getElementById('score').textContent = score;
    }
    
    currentQuestion++;
    if (currentQuestion < questions.length) {
        showQuestion();
    }
}

async function submitQuiz() {
    const selected = document.querySelector('.option.selected');
    if (!selected) {
        alert('Please select an answer');
        return;
    }
    
    // Check last answer
    if (questions[currentQuestion].correct === Array.from(document.querySelectorAll('.option')).indexOf(selected)) {
        score++;
        document.getElementById('score').textContent = score;
    }
    
    clearInterval(timer);
    
    try {
        await fetch('http://localhost:5000/api/submit-quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                score,
                time: timeSpent,
                total_questions: questions.length
            })
        });
        
        alert(`Quiz completed!\nScore: ${score}/${questions.length}\nTime: ${formatTime(timeSpent)}`);
        showLeaderboard();
    } catch (error) {
        alert('Failed to submit quiz. Please try again.');
    }
}

// Timer Functions
function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => {
        timeSpent++;
        document.getElementById('time').textContent = formatTime(timeSpent);
    }, 1000);
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Leaderboard Functions
async function showLeaderboard() {
    try {
        const response = await fetch('http://localhost:5000/api/leaderboard', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        
        const leaderboard = await response.json();
        const tbody = document.getElementById('leaderboard-body');
        tbody.innerHTML = '';
        
        leaderboard.forEach((entry, index) => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = index + 1;
            row.insertCell(1).textContent = entry.username;
            row.insertCell(2).textContent = `${entry.score}/${entry.total_questions}`;
            row.insertCell(3).textContent = formatTime(entry.time);
        });
        
        quizContainer.classList.add('hidden');
        leaderboardContainer.classList.remove('hidden');
    } catch (error) {
        alert('Failed to load leaderboard. Please try again.');
    }
}

function hideLeaderboard() {
    leaderboardContainer.classList.add('hidden');
    quizContainer.classList.add('hidden');
}

// Navigation Functions
function showQuizSection() {
    authSection.classList.add('hidden');
    quizSection.classList.remove('hidden');
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    location.reload();
}

// Check if user is already logged in
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        showQuizSection();
    }
}); 