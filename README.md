# URL Shortener with Firebase Hosting

This is a URL shortener application built with Flask and Firebase Hosting.

## Features

- Shorten long URLs to easy-to-share formats
- Track recently shortened URLs
- Copy shortened URLs with one click
- Responsive design that works on all devices

## Firebase Deployment Instructions

1. Install Firebase CLI tools:
   ```
   npm install -g firebase-tools
   ```

2. Log in to Firebase:
   ```
   firebase login
   ```

3. Initialize Firebase (if not already done):
   ```
   firebase init
   ```
   - Select "Hosting" and "Functions" features
   - Select or create a Firebase project
   - Follow the setup prompts

4. Deploy to Firebase:
   ```
   firebase deploy
   ```

## Project Structure

- `/functions` - Contains Firebase Cloud Functions implementation
- `/public` - Contains static files for Firebase Hosting
- `firebase.json` - Firebase configuration
- `.firebaserc` - Firebase project configuration

## Development

To run the application locally:

1. Install required dependencies:
   ```
   pip install -r functions/requirements.txt
   ```

2. Start the Firebase emulator:
   ```
   firebase emulators:start
   ```

## Technologies Used

- Flask - Python web framework
- Firebase Hosting - Web hosting
- Firebase Cloud Functions - Serverless functions
- Bootstrap - Frontend framework