import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const Signup = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const signupResponse = await axios.post('http://127.0.0.1:5000/api/signup', { username, password });
      console.log('Signup response:', signupResponse.data);

      const loginResponse = await axios.post('http://127.0.0.1:5000/api/login', { username, password });
      console.log('Login response:', loginResponse.data);

      const { token } = loginResponse.data;
      login(token);
      navigate('/dashboard');
    } catch (err) {
      console.error('Signup error:', err.response ? err.response.data : err.message);
      setError(`Failed to sign up: ${err.response ? err.response.data.error : err.message}`);
    }
  };

  return (
    <div>
      <h2>Sign Up</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Username:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Sign Up</button>
      </form>
      <p>Already have an account? <Link to="/login">Login</Link></p>
    </div>
  );
};

export default Signup;