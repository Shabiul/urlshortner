const functions = require('firebase-functions');
const { spawn } = require('child_process');

// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

exports.app = functions.https.onRequest((request, response) => {
  // Point to your Python script
  const process = spawn('python', ['app.py', request.path, request.method, JSON.stringify(request.body)]);
  
  process.stdout.on('data', (data) => {
    console.log(`stdout: ${data}`);
    response.status(200).send(data);
  });
  
  process.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
    response.status(500).send(data);
  });
  
  process.on('close', (code) => {
    console.log(`child process exited with code ${code}`);
  });
});