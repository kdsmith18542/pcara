import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

function Repositories() {
  const [repositories, setRepositories] = useState([]);
  const [open, setOpen] = useState(false);
  const [newRepo, setNewRepo] = useState({
    name: '',
    url: '',
    description: ''
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchRepositories();
  }, []);

  const fetchRepositories = async () => {
    try {
      const response = await api.get('/repositories');
      setRepositories(response.data);
    } catch (error) {
      console.error('Error fetching repositories:', error);
      // Mock data for development
      setRepositories([
        {
          id: 1,
          name: 'my-python-project',
          url: 'https://github.com/user/my-python-project',
          description: 'A sample Python project',
          created_at: '2025-07-10T10:00:00Z'
        }
      ]);
    }
  };

  const handleAddRepository = async () => {
    try {
      await api.post('/repositories', newRepo);
      setOpen(false);
      setNewRepo({ name: '', url: '', description: '' });
      fetchRepositories();
    } catch (error) {
      console.error('Error adding repository:', error);
    }
  };

  const [analysisDialog, setAnalysisDialog] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [analysisConfig, setAnalysisConfig] = useState({
    languages: ['python'],
    analysis_types: ['syntax_analysis', 'dependency_analysis', 'complexity_analysis']
  });

  const availableLanguages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript/TypeScript' },
    { value: 'csharp', label: 'C#' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' }
  ];

  const availableAnalysisTypes = [
    { value: 'syntax_analysis', label: 'Syntax Analysis' },
    { value: 'dependency_analysis', label: 'Dependency Analysis' },
    { value: 'complexity_analysis', label: 'Complexity Analysis' },
    { value: 'security_analysis', label: 'Security Analysis' },
    { value: 'architecture_analysis', label: 'Architecture Analysis' }
  ];

  const handleStartAnalysis = (repositoryId) => {
    setSelectedRepo(repositoryId);
    setAnalysisDialog(true);
  };

  const handleRunAnalysis = async () => {
    try {
      const response = await api.post('/analysis', {
        repository_id: selectedRepo,
        languages: analysisConfig.languages,
        analysis_types: analysisConfig.analysis_types
      });
      
      setAnalysisDialog(false);
      navigate(`/analysis/${response.data.job_id}`);
    } catch (error) {
      console.error('Error starting analysis:', error);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Repositories
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
        >
          Add Repository
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {repositories.map((repo) => (
              <TableRow key={repo.id}>
                <TableCell>{repo.name}</TableCell>
                <TableCell>
                  <Chip label={repo.url} size="small" variant="outlined" />
                </TableCell>
                <TableCell>{repo.description}</TableCell>
                <TableCell>
                  {new Date(repo.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <IconButton
                    color="primary"
                    onClick={() => handleStartAnalysis(repo.id)}
                    title="Start Analysis"
                  >
                    <PlayIcon />
                  </IconButton>
                  <IconButton
                    color="secondary"
                    title="View Details"
                  >
                    <ViewIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add Repository Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Repository</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Repository Name"
            fullWidth
            variant="outlined"
            value={newRepo.name}
            onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Repository URL"
            fullWidth
            variant="outlined"
            value={newRepo.url}
            onChange={(e) => setNewRepo({ ...newRepo, url: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newRepo.description}
            onChange={(e) => setNewRepo({ ...newRepo, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleAddRepository} variant="contained">
            Add Repository
          </Button>
        </DialogActions>
      </Dialog>

      {/* Analysis Configuration Dialog */}
      <Dialog open={analysisDialog} onClose={() => setAnalysisDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Analysis</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Languages</InputLabel>
            <Select
              multiple
              value={analysisConfig.languages}
              onChange={(e) => setAnalysisConfig({...analysisConfig, languages: e.target.value})}
              input={<OutlinedInput label="Languages" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={availableLanguages.find(l => l.value === value)?.label} size="small" />
                  ))}
                </Box>
              )}
            >
              {availableLanguages.map((language) => (
                <MenuItem key={language.value} value={language.value}>
                  <Checkbox checked={analysisConfig.languages.indexOf(language.value) > -1} />
                  <ListItemText primary={language.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth margin="normal">
            <InputLabel>Analysis Types</InputLabel>
            <Select
              multiple
              value={analysisConfig.analysis_types}
              onChange={(e) => setAnalysisConfig({...analysisConfig, analysis_types: e.target.value})}
              input={<OutlinedInput label="Analysis Types" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={availableAnalysisTypes.find(a => a.value === value)?.label} size="small" />
                  ))}
                </Box>
              )}
            >
              {availableAnalysisTypes.map((analysisType) => (
                <MenuItem key={analysisType.value} value={analysisType.value}>
                  <Checkbox checked={analysisConfig.analysis_types.indexOf(analysisType.value) > -1} />
                  <ListItemText primary={analysisType.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {analysisConfig.languages.length > 1 && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="body2" color="info.dark">
                🔍 Polyglot Analysis Enabled: Multiple languages detected. 
                PCARA will perform cross-language dependency analysis to identify 
                inter-language communication patterns and architectural insights.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialog(false)}>Cancel</Button>
          <Button onClick={handleRunAnalysis} variant="contained">
            Start Analysis
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default Repositories;