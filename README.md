# Python Course LMS

A Learning Management System for Python courses built with Flask.

## Features

- User Registration and Authentication
- Course Management
- Assignment Submission
- Admin Dashboard
- Student Dashboard

## Deployment Instructions for Render

1. Create a new account on [Render](https://render.com)
2. Click on "New +" and select "Web Service"
3. Connect your GitHub repository
4. Fill in the following settings:
   - Name: python-course-lms (or your preferred name)
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Click "Create Web Service"

## Environment Variables

Add the following environment variables in Render:
- `SECRET_KEY`: A random secret key for Flask
- `DATABASE_URL`: Your database URL (Render will provide this automatically)
