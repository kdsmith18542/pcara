import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Box,
  Chip
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import api from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState({
    totalRepositories: 0,
    totalAnalyses: 0,
    recentAnalyses: []
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // This would be actual API calls
      setStats({
        totalRepositories: 3,
        totalAnalyses: 12,
        recentAnalyses: [
          {
            id: 1,
            repository: 'my-python-project',
            status: 'completed',
            date: '2025-07-13',
            languages: ['Python']
          },
          {
            id: 2,
            repository: 'web-app',
            status: 'running',
            date: '2025-07-13',
            languages: ['JavaScript', 'Python']
          }
        ]
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const chartData = [
    { name: 'Python', files: 45, complexity: 23 },
    { name: 'JavaScript', files: 32, complexity: 18 },
    { name: 'C#', files: 28, complexity: 15 },
    { name: 'Go', files: 12, complexity: 8 }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Repositories
              </Typography>
              <Typography variant="h4">
                {stats.totalRepositories}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Analyses
              </Typography>
              <Typography variant="h4">
                {stats.totalAnalyses}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Jobs
              </Typography>
              <Typography variant="h4">
                {stats.recentAnalyses.filter(a => a.status === 'running').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Language Analysis Overview
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="files" fill="#8884d8" name="Files" />
                  <Bar dataKey="complexity" fill="#82ca9d" name="Avg Complexity" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Recent Analyses */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Analyses
              </Typography>
              {stats.recentAnalyses.map((analysis) => (
                <Box key={analysis.id} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Typography variant="subtitle2">
                    {analysis.repository}
                  </Typography>
                  <Box sx={{ mt: 1, mb: 1 }}>
                    <Chip 
                      label={analysis.status} 
                      size="small" 
                      color={getStatusColor(analysis.status)}
                    />
                  </Box>
                  <Typography variant="caption" color="textSecondary">
                    {analysis.languages.join(', ')} • {analysis.date}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;