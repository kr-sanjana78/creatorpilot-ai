import React, { useState } from 'react';
import api from '../services/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    console.log("=== LOGIN BUTTON CLICKED ===");
    setError('');
    
    try {
      console.log("Attempting to connect to backend with:", email);
      const response = await api.post('/api/auth/login', { email, password });
      console.log('Login successful response:', response.data);
      alert('Login successful!');
    } catch (err) {
      console.error("Login error details:", err);
      const errorMsg = err.response?.data?.detail || 'Could not connect to the backend server.';
      setError(errorMsg);
    }
  };

  return (
    <div style={{ padding: '50px', fontFamily: 'Arial' }}>
      <form onSubmit={handleLogin}>
        <h2>CreatorPilot AI - Login</h2>
        {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
        <div style={{ margin: '10px 0' }}>
          <input 
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            placeholder="test@creatorpilot.ai" 
            style={{ padding: '8px', width: '250px' }}
          />
        </div>
        <div style={{ margin: '10px 0' }}>
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            placeholder="Password" 
            style={{ padding: '8px', width: '250px' }}
          />
        </div>
        <button 
          type="submit" 
          style={{ padding: '10px 20px', background: 'blue', color: 'white', border: 'none', cursor: 'pointer' }}
        >
          Login
        </button>
      </form>
    </div>
  );
}