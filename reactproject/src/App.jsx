import './index.css';

import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Presentacion from './components/Presentacion';
import Menu from './components/menu';
import AuroraBackground from './components/AuroraBackground';
import Login from './pages/Login';
import AdminPanel from './pages/AdminPanel';
import Register from './pages/Register';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
      <Route path="/" element={<Presentacion />} />  ← ✅ login como página principal
      <Route path="/Login" element={<Login />} />
      <Route path="/menu" element={<Menu />} />
      <Route path="/admin" element={<AdminPanel />} />
      <Route path="/register" element={<Register/>} />

</Routes>

    </AnimatePresence>
  );
}

function App() {
  return (
    <Router>
      <AuroraBackground 
    //colorStops={["#3A29FF", "#FF94B4", "#FF3232"]}
    colorStops={["#f6ff00", "#0008ff", "#FF3232"]}
    blend={0.0}
    amplitude={1.0}
    speed={0.5}
    
      />
      <AnimatedRoutes />
    </Router>
  );
}

export default App;

