const path = require('path');
const { app, BrowserWindow } = require('electron');

const createWindow = () => {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "Sabores 4 - Menú",
    webPreferences: {
      contextIsolation: true,
    }
  });

  win.setMenu(null);
  win.loadURL('http://localhost:5173');
}

app.whenReady().then(createWindow);
