import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { format, parseISO, eachDayOfInterval, subDays } from 'date-fns';

const Dashboard = () => {
  const [scores, setScores] = useState([]);
  const [newScore, setNewScore] = useState({ date: format(new Date(), 'yyyy-MM-dd'), score: '' });
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchScores();
  }, []);

  const fetchScores = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/get_scores');
      setScores(response.data);
    } catch (error) {
      console.error('Error fetching scores:', error);
      if (error.response && error.response.status === 401) {
        logout();
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:5000/api/submit_score', newScore);
      setNewScore({ ...newScore, score: '' });
      fetchScores();
    } catch (error) {
      console.error('Error submitting score:', error);
      if (error.response && error.response.status === 401) {
        logout();
      }
    }
  };

  const renderHeatmap = () => {
    const endDate = new Date();
    const startDate = subDays(endDate, 364);
    const dates = eachDayOfInterval({ start: startDate, end: endDate });

    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(53, 1fr)', gap: '1px' }}>
        {dates.map(date => {
          const dateStr = format(date, 'yyyy-MM-dd');
          const score = scores.find(s => s.date === dateStr)?.score || 0;
          const intensity = score * 25; // Adjust color intensity based on score
          return (
            <div
              key={dateStr}
              style={{
                width: '10px',
                height: '10px',
                backgroundColor: score ? `rgb(0, ${intensity}, 0)` : '#ebedf0',
              }}
              title={`${dateStr}: ${score}`}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div>
      <h1>Welcome, {user?.username || 'User'}!</h1>
      <button onClick={logout}>Logout</button>

      <h2>Submit Today's Score</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="date"
          value={newScore.date}
          onChange={(e) => setNewScore({ ...newScore, date: e.target.value })}
          required
        />
        <input
          type="number"
          value={newScore.score}
          onChange={(e) => setNewScore({ ...newScore, score: e.target.value })}
          min="1"
          max="10"
          required
        />
        <button type="submit">Submit Score</button>
      </form>

      <h2>Your Productivity Heatmap</h2>
      {renderHeatmap()}
    </div>
  );
};

export default Dashboard;