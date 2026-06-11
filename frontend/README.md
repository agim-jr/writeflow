cat > README.md << 'ENDOFFILE'

# WriteFlow - AI-Powered Writing Platform

A modern web application that helps writers stay focused and productive with AI coaching, real-time analytics, and community features.

## Features

### Core Writing Experience

- Multiple Writing Modes - Timed Sessions (25/45 min), Sprint Mode, Focus Mode
- Real-time Analytics - Word count, WPM tracking, writing streaks
- Auto-save and Export - TXT, Markdown, HTML formats
- Clean, Distraction-Free UI - Built with React and Tailwind CSS

### AI Writing Coach

- Real-time Motivation via WebSocket connection
- Writer's Block Detection with personalized nudges
- Milestone Celebrations when hitting goals
- Adaptive Coaching Styles (Cheerleader, Taskmaster, Philosopher, Comedian)
- Rule-based AI algorithm for intelligent coaching

### Analytics and Progress

- Writing Streaks tracking
- Performance Metrics (WPM, pauses, edits)
- Session History with detailed statistics
- Daily Goals (250 words minimum)

### Community Features

- Share Your Work (one post per day after 250 words)
- Like and Comment on others' posts
- Motivational Feed of fellow writers

## Tech Stack

Frontend:

- React 18 with React Router
- Tailwind CSS for styling
- Lucide React icons
- Recharts for data visualization
- WebSocket for real-time features

Backend:

- FastAPI (Python 3.11+)
- PostgreSQL database
- SQLAlchemy ORM
- JWT authentication
- Rule-based AI coaching algorithm
- WebSocket support

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database configuration

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --port 8000
```
