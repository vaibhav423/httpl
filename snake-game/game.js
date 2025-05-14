class SnakeGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.startBtn = document.getElementById('startBtn');
        this.scoreElement = document.getElementById('score');
        this.highScoreElement = document.getElementById('highScore');
        this.timerElement = document.getElementById('timer');
        this.themeBtn = document.getElementById('themeBtn');
        this.particles = [];
        
        // Set canvas size
        this.canvas.width = 400;
        this.canvas.height = 400;
        
        // Game settings
        this.gridSize = 20;
        this.snake = [];
        this.food = {};
        this.direction = 'right';
        this.nextDirection = 'right';
        this.score = 0;
        this.highScore = parseInt(localStorage.getItem('snakeHighScore')) || 0;
        this.gameLoop = null;
        this.speed = 150;
        this.foodPulse = 0;
        
        this.highScoreElement.textContent = this.highScore;
        // Timer properties
        this.startTime = 0;
        this.elapsedTime = 0;
        this.timerInterval = null;
        
        this.setupEventListeners();
        this.setupThemeToggle();
    }

    setupThemeToggle() {
        this.themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('snakeGameTheme', newTheme);
            this.themeBtn.textContent = newTheme === 'dark' ? '🌙' : '☀️';
        });

        // Set initial button text
        const currentTheme = document.documentElement.getAttribute('data-theme');
        this.themeBtn.textContent = currentTheme === 'dark' ? '🌙' : '☀️';
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startGame());
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
    }

    formatTime(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    updateTimer() {
        const currentTime = Date.now();
        this.elapsedTime = currentTime - this.startTime;
        this.timerElement.textContent = this.formatTime(this.elapsedTime);
    }

    startGame() {
        // Reset game state
        this.startTime = Date.now();
        this.elapsedTime = 0;
        this.timerElement.textContent = '00:00';
        
        // Clear previous timer if exists
        if (this.timerInterval) clearInterval(this.timerInterval);
        
        // Start timer
        this.timerInterval = setInterval(() => this.updateTimer(), 1000);
        
        this.snake = [
            { x: 5, y: 5 },
            { x: 4, y: 5 },
            { x: 3, y: 5 }
        ];
        this.direction = 'right';
        this.nextDirection = 'right';
        this.score = 0;
        this.scoreElement.textContent = this.score;
        this.particles = [];
        this.generateFood();
        
        // Clear previous game loop if exists
        if (this.gameLoop) clearInterval(this.gameLoop);
        
        // Start game loop
        this.gameLoop = setInterval(() => this.update(), this.speed);
        
        // Update button state
        this.startBtn.textContent = 'Restart Game';
    }

    createParticles(x, y) {
        for (let i = 0; i < 10; i++) {
            this.particles.push({
                x: x * this.gridSize + this.gridSize / 2,
                y: y * this.gridSize + this.gridSize / 2,
                vx: (Math.random() - 0.5) * 8,
                vy: (Math.random() - 0.5) * 8,
                alpha: 1,
                color: '#00ff88'
            });
        }
    }

    updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.alpha -= 0.02;

            if (particle.alpha <= 0) {
                this.particles.splice(i, 1);
            }
        }
    }

    drawParticles() {
        this.particles.forEach(particle => {
            this.ctx.save();
            this.ctx.globalAlpha = particle.alpha;
            this.ctx.fillStyle = particle.color;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, 3, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
        });
    }

    generateFood() {
        let position;
        do {
            position = {
                x: Math.floor(Math.random() * (this.canvas.width / this.gridSize)),
                y: Math.floor(Math.random() * (this.canvas.height / this.gridSize))
            };
        } while (this.snake.some(segment => segment.x === position.x && segment.y === position.y));
        
        this.food = position;
        this.foodPulse = 0;
    }

    handleKeyPress(e) {
        const keyMap = {
            'ArrowUp': 'up',
            'ArrowDown': 'down',
            'ArrowLeft': 'left',
            'ArrowRight': 'right'
        };

        const newDirection = keyMap[e.key];
        if (!newDirection) return;

        const opposites = {
            'up': 'down',
            'down': 'up',
            'left': 'right',
            'right': 'left'
        };

        // Remove active class from all keys
        document.querySelectorAll('.key').forEach(key => key.classList.remove('active'));
        
        // Add active class to pressed key
        const arrowMap = {
            'up': '↑',
            'down': '↓',
            'left': '←',
            'right': '→'
        };
        const keyElement = Array.from(document.querySelectorAll('.key')).find(
            key => key.textContent === arrowMap[newDirection]
        );
        if (keyElement) {
            keyElement.classList.add('active');
            setTimeout(() => keyElement.classList.remove('active'), 150);
        }

        if (opposites[newDirection] !== this.direction) {
            this.nextDirection = newDirection;
        }
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startGame());
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        // Add touch/click events for arrow keys
        document.querySelectorAll('.key').forEach(key => {
            key.addEventListener('click', () => {
                const directionMap = {
                    '↑': 'ArrowUp',
                    '↓': 'ArrowDown',
                    '←': 'ArrowLeft',
                    '→': 'ArrowRight'
                };
                const event = new KeyboardEvent('keydown', {
                    key: directionMap[key.textContent]
                });
                this.handleKeyPress(event);
            });

            // Add touch events for mobile
            key.addEventListener('touchstart', (e) => {
                e.preventDefault();
                const directionMap = {
                    '↑': 'ArrowUp',
                    '↓': 'ArrowDown',
                    '←': 'ArrowLeft',
                    '→': 'ArrowRight'
                };
                const event = new KeyboardEvent('keydown', {
                    key: directionMap[key.textContent]
                });
                this.handleKeyPress(event);
            });
        });
    }

    update() {
        // Update snake direction
        this.direction = this.nextDirection;

        // Calculate new head position
        const head = { ...this.snake[0] };
        switch (this.direction) {
            case 'up': head.y--; break;
            case 'down': head.y++; break;
            case 'left': head.x--; break;
            case 'right': head.x++; break;
        }

        // Check for collisions
        if (this.checkCollision(head)) {
            this.gameOver();
            return;
        }

        // Add new head
        this.snake.unshift(head);

        // Check if food is eaten
        if (head.x === this.food.x && head.y === this.food.y) {
            this.score += 10;
            this.scoreElement.textContent = this.score;
            
            // Update high score
            if (this.score > this.highScore) {
                this.highScore = this.score;
                this.highScoreElement.textContent = this.highScore;
                localStorage.setItem('snakeHighScore', this.highScore);
                this.highScoreElement.classList.add('pulse');
                setTimeout(() => this.highScoreElement.classList.remove('pulse'), 1000);
            }

            // Create particles at food location
            this.createParticles(this.food.x, this.food.y);
            
            this.generateFood();
            // Increase speed slightly
            if (this.speed > 50) {
                clearInterval(this.gameLoop);
                this.speed -= 5;
                this.gameLoop = setInterval(() => this.update(), this.speed);
            }
        } else {
            // Remove tail if no food eaten
            this.snake.pop();
        }

        this.draw();
    }

    checkCollision(head) {
        // Wall collision
        if (head.x < 0 || head.x >= this.canvas.width / this.gridSize ||
            head.y < 0 || head.y >= this.canvas.height / this.gridSize) {
            return true;
        }

        // Self collision
        return this.snake.some(segment => segment.x === head.x && segment.y === head.y);
    }

    gameOver() {
        clearInterval(this.gameLoop);
        clearInterval(this.timerInterval);
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = '#FF0000';
        this.ctx.font = '30px Arial';
        this.ctx.fillText('Game Over!', this.canvas.width/2 - 70, this.canvas.height/2);
        
        // Display final score
        this.ctx.font = '20px Arial';
        this.ctx.fillStyle = '#fff';
        this.ctx.fillText(`Final Score: ${this.score}`, this.canvas.width/2 - 60, this.canvas.height/2 + 40);
        this.ctx.fillText(`Time: ${this.formatTime(this.elapsedTime)}`, this.canvas.width/2 - 60, this.canvas.height/2 + 70);
        
        this.startBtn.textContent = 'Play Again';
    }

    draw() {
        // Clear canvas
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw particles
        this.updateParticles();
        this.drawParticles();

        // Draw snake
        this.snake.forEach((segment, index) => {
        const colors = getComputedStyle(document.documentElement);
        const gradient = this.ctx.createLinearGradient(
            segment.x * this.gridSize,
            segment.y * this.gridSize,
            (segment.x + 1) * this.gridSize,
            (segment.y + 1) * this.gridSize
        );
        
        if (index === 0) {
            // Head color
            gradient.addColorStop(0, colors.getPropertyValue('--snake-head').trim());
            gradient.addColorStop(1, colors.getPropertyValue('--snake-body').trim());
        } else {
            // Body color
            gradient.addColorStop(0, colors.getPropertyValue('--snake-body').trim());
            gradient.addColorStop(1, colors.getPropertyValue('--accent-secondary').trim());
        }

            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(
                segment.x * this.gridSize,
                segment.y * this.gridSize,
                this.gridSize - 1,
                this.gridSize - 1
            );
        });

        // Update and draw food with pulsing effect
        this.foodPulse = (this.foodPulse + 0.1) % (Math.PI * 2);
        const pulseSize = 1 + Math.sin(this.foodPulse) * 0.2;

        const foodGradient = this.ctx.createRadialGradient(
            (this.food.x + 0.5) * this.gridSize,
            (this.food.y + 0.5) * this.gridSize,
            0,
            (this.food.x + 0.5) * this.gridSize,
            (this.food.y + 0.5) * this.gridSize,
            (this.gridSize/2) * pulseSize
        );
        const colors = getComputedStyle(document.documentElement);
        foodGradient.addColorStop(0, colors.getPropertyValue('--food-primary').trim());
        foodGradient.addColorStop(1, colors.getPropertyValue('--food-secondary').trim());
        
        this.ctx.fillStyle = foodGradient;
        this.ctx.beginPath();
        this.ctx.arc(
            (this.food.x + 0.5) * this.gridSize,
            (this.food.y + 0.5) * this.gridSize,
            (this.gridSize/2 - 1) * pulseSize,
            0,
            Math.PI * 2
        );
        this.ctx.fill();

        // Draw food glow effect
        this.ctx.shadowBlur = 15;
        this.ctx.shadowColor = getComputedStyle(document.documentElement).getPropertyValue('--food-primary').trim();
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
    }
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SnakeGame();
});
