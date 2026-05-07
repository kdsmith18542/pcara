import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Box,
  Grid,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import api from '../services/api';

function Analysis() {
  const { jobId } = useParams();
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalysisData();
    const interval = setInterval(fetchAnalysisData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [jobId]);

  const fetchAnalysisData = async () => {
    try {
      const response = await api.get(`/analysis/${jobId}`);
      setAnalysisData(response.data);
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        setLoading(false);
      }
    } catch (error) {
      console.error('Error fetching analysis data:', error);
      // Mock data for development
      setAnalysisData({
        job_id: jobId,
        status: 'completed',
        progress: 100,
        started_at: '2025-07-13T10:00:00Z',
        completed_at: '2025-07-13T10:05:00Z',
        results: {
          language: 'python',
          files_analyzed: 25,
          analysis_results: {
            syntax_analysis: {
              total_files: 25,
              valid_files: 24,
              syntax_errors: [],
              file_stats: {}
            },
            complexity_analysis: {
              total_complexity: 156,
              high_complexity_functions: [
                { file: 'main.py', function: 'process_data', complexity: 15 },
                { file: 'utils.py', function: 'transform', complexity: 12 }
              ]
            },
            dependency_analysis: {
              total_dependencies: 45,
              dependency_graph: {}
            }
          }
        }
      });
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  const complexityData = [
    { name: 'Low (1-5)', value: 18, color: '#00C49F' },
    { name: 'Medium (6-10)', value: 5, color: '#FFBB28' },
    { name: 'High (11+)', value: 2, color: '#FF8042' }
  ];

  if (!analysisData) {
    return (
      <Container>
        <Typography>Loading analysis data...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Analysis Results
      </Typography>
      
      <Grid container spacing={3}>
        {/* Status Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job Status
              </Typography>
              <Chip 
                label={analysisData.status} 
                color={getStatusColor(analysisData.status)}
                sx={{ mb: 2 }}
              />
              {analysisData.status === 'running' && (
                <LinearProgress variant="determinate" value={analysisData.progress} />
              )}
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Progress: {analysisData.progress}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Summary Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Summary
              </Typography>
              <Typography>
                Files Analyzed: {analysisData.results?.files_analyzed || 0}
              </Typography>
              <Typography>
                Language: {analysisData.results?.language || 'N/A'}
              </Typography>
              <Typography>
                Started: {new Date(analysisData.started_at).toLocaleString()}
              </Typography>
              {analysisData.completed_at && (
                <Typography>
                  Completed: {new Date(analysisData.completed_at).toLocaleString()}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Complexity Chart */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Complexity Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={complexityData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label
                  >
                    {complexityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Results */}
        {analysisData.results && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Detailed Analysis Results
                </Typography>
                
                {/* High Complexity Functions */}
                {analysisData.results.analysis_results?.complexity_analysis?.high_complexity_functions && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>High Complexity Functions</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      {analysisData.results.analysis_results.complexity_analysis.high_complexity_functions.map((func, index) => (
                        <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'background.paper', border: '1px solid #e0e0e0' }}>
                          <Typography variant="subtitle2">{func.function}</Typography>
                          <Typography variant="body2" color="textSecondary">
                            File: {func.file} | Complexity: {func.complexity}
                          </Typography>
                        </Box>
                      ))}
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Syntax Analysis */}
                {analysisData.results.analysis_results?.syntax_analysis && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>Syntax Analysis</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography>
                        Valid Files: {analysisData.results.analysis_results.syntax_analysis.valid_files} / {analysisData.results.analysis_results.syntax_analysis.total_files}
                      </Typography>
                      {analysisData.results.analysis_results.syntax_analysis.syntax_errors.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" color="error">Syntax Errors:</Typography>
                          {analysisData.results.analysis_results.syntax_analysis.syntax_errors.map((error, index) => (
                            <Typography key={index} variant="body2" color="error">
                              {error.file}:{error.line} - {error.message}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}

export default Analysis;