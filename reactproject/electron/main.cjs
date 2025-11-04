const path = require('path');
const { app, BrowserWindow } = require('electron');

function createWindow () {
  const win = new BrowserWindow({
    width: 1080,
    height: 720,
    frame: true,
    webPreferences: {
      contextIsolation: true,
      
    }
  });   

  win.setMenu(null)

  win.loadURL('http://localhost:5173'); // React dev server
}

app.whenReady().then(createWindow);
