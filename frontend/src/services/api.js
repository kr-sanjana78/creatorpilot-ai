import axios from 'axios';

const api = axios.create({
  baseURL: 'https://creatorpilot-backend-70xt.onrender.com',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;