import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', // URL backend
  timeout: 20000, // Thời gian chờ tối đa
});

export default api;