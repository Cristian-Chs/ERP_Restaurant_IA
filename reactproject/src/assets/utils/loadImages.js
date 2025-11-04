// loadImages.js (usando Vite)
const images = import.meta.glob('../images/*.{jpg,jpeg,png,svg}', { eager: true });

const parsedImages = {};
for (const path in images) {
  const name = path.split('/').pop().split('.')[0];
  parsedImages[name] = images[path].default;
}

export default parsedImages;
