import React, { useEffect } from 'react';

export default function Dashboard() {
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      // If not logged in, kick back to login page
      window.location.href = '/login';
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  return (
    <div style={{ padding: '3rem', fontFamily: 'sans-serif' }}>
      <h1>CreatorPilot AI Dashboard</h1>
      <p>Welcome! You are successfully connected to your secure backend session.</p>
      <button 
        onClick={handleLogout} 
        style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#dc2626', color: '#fff', border: 'none', cursor: 'pointer' }}
      >
        Logout
      </button>
    </div>
  );
}