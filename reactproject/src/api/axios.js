// src/api/axios.js
import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.PROD ? '/api' : 'http://localhost:8000/api',
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  
  // ✅ Añade el prefijo 'Bearer '
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config; // Siempre retorna la configuración
}, (error) => {
  return Promise.reject(error);
});

export default API;