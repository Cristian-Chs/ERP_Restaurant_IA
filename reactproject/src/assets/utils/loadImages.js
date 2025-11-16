// src/assets/utils/loadImages.js (CORREGIDO)

// Importa todas las imágenes de la carpeta ../images
const images = import.meta.glob('../images/*.{jpg,jpeg,png,svg}', { eager: true });

const parsedImages = {};
for (const path in images) {
  // Extrae el nombre del archivo sin extensión (ej: 'sushi' de 'sushi.jpg')
  const filename = path.split('/').pop().split('.')[0];
  
  // 🚨 CRÍTICO: Normalizar a minúsculas y quitar acentos para la clave
  const normalizedName = filename.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  
  parsedImages[normalizedName] = images[path].default;
}

export default parsedImages;