const functions = require('firebase-functions');
const admin = require('firebase-admin');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { spawn } = require('child_process');

admin.initializeApp();

// This express app will proxy requests to your Flask app
const app = express();

// Start the Flask server when the function initializes
let flaskProcess = null;
const startFlaskServer = () => {
  if (flaskProcess) return;
  console.log('Starting Flask server...');
  
  // Start the Flask process from main.py
  flaskProcess = spawn('python', ['main.py']);
  
  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask stdout: ${data}`);
  });
  
  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask stderr: ${data}`);
  });
  
  flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
    flaskProcess = null;
  });
  
  // Give Flask a moment to start up
  return new Promise((resolve) => setTimeout(resolve, 2000));
};

// Middleware to ensure Flask is running before proxying requests
app.use(async (req, res, next) => {
  if (!flaskProcess) {
    try {
      await startFlaskServer();
    } catch (error) {
      console.error('Failed to start Flask server:', error);
      res.status(500).send('Internal Server Error - Could not start Flask');
      return;
    }
  }
  next();
});

// Proxy all requests to the Flask server
const flaskProxy = createProxyMiddleware({
  target: 'http://localhost:5000',
  changeOrigin: true,
  ws: true,
  pathRewrite: path => path,
  onProxyReq: (proxyReq, req, res) => {
    // Add any headers or modify the request if needed
    proxyReq.setHeader('X-Firebase-Forwarded', 'true');
  },
  onError: (err, req, res) => {
    console.error('Proxy error:', err);
    res.status(500).send('Proxy Error - Flask server may not be responding');
  }
});

// Use the proxy for all routes
app.use('/', flaskProxy);

// Export the Firebase Cloud Function
exports.app = functions.https.onRequest(app);