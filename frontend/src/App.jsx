import React from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

export default function App() {
  const path = window.location.pathname;

  if (path === '/register') {
    return <Register />;
  }

  if (path === '/dashboard') {
    return <Dashboard />;
  }

  // Default to Login view
  return <Login />;
}
