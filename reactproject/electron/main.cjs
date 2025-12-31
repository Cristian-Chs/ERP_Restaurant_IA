const path = require('path');
const { app, BrowserWindow } = require('electron');

const createWindows = () => {
  // 1. Ventana Principal (Cliente)
  const winClient = new BrowserWindow({
    width: 1080,
    height: 720,
    title: "Cliente - Menú",
    webPreferences: {
      contextIsolation: true,
    }
  });

  winClient.setMenu(null);
  winClient.loadURL('http://localhost:5173');

  // 2. Ventana Cocina (Chef)
  const winKitchen = new BrowserWindow({
    width: 800,
    height: 600,
    x: 50, // Desplazada para que no se superpongan exacto
    y: 50,
    title: "Panel de Cocina",
    webPreferences: {
      contextIsolation: true,
    }
  });

  winKitchen.setMenu(null);
  winKitchen.loadURL('http://localhost:5173/kitchen-panel');
}

app.whenReady().then(createWindows);
