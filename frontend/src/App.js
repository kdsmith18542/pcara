import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Repositories from './pages/Repositories';
import Analysis from './pages/Analysis';
import Login from './pages/Login';
import Register from './pages/Register';
import { AuthProvider, useAuth } from './services/AuthContext';

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Box sx={{ flexGrow: 1 }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <Navbar />
              <Box component="main" sx={{ p: 3 }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/repositories" element={<Repositories />} />
                  <Route path="/analysis/:jobId" element={<Analysis />} />
                </Routes>
              </Box>
            </ProtectedRoute>
          } />
        </Routes>
      </Box>
    </AuthProvider>
  );
}

export default App;