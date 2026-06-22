import React from 'react';
import {
  Button, FormControl, InputAdornment, InputLabel, MenuItem, Paper, Select, Stack, TextField,
} from '@mui/material';
import { Search, Clear } from '@mui/icons-material';
import { EVENT_TYPE_OPTIONS, SEVERITY_OPTIONS } from '../constants/eventTypes';
import { DEFAULT_LOG_FILTERS, LogFilters, hasActiveLogFilters } from '../utils/logFilters';

interface EventLogFiltersProps {
  filters: LogFilters;
  onChange: (filters: LogFilters) => void;
  cameras: string[];
}

const EventLogFilters: React.FC<EventLogFiltersProps> = ({ filters, onChange, cameras }) => {
  const update = (key: keyof LogFilters, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <Paper sx={{ p: 2, mb: 3, borderRadius: 1, border: '1px solid #DDDDDD' }} elevation={0}>
      <Stack spacing={2}>
        <TextField
          placeholder="Search event type, camera, or event ID..."
          size="small"
          fullWidth
          value={filters.search}
          onChange={(e) => update('search', e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start"><Search sx={{ fontSize: 20 }} /></InputAdornment>
            ),
          }}
        />
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <FormControl size="small" fullWidth>
            <InputLabel>Event Type</InputLabel>
            <Select
              label="Event Type"
              value={filters.eventType}
              onChange={(e) => update('eventType', e.target.value)}
            >
              <MenuItem value="">All event types</MenuItem>
              {EVENT_TYPE_OPTIONS.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" fullWidth>
            <InputLabel>Camera</InputLabel>
            <Select
              label="Camera"
              value={filters.camera}
              onChange={(e) => update('camera', e.target.value)}
            >
              <MenuItem value="">All cameras</MenuItem>
              {cameras.map((name) => (
                <MenuItem key={name} value={name}>{name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" fullWidth>
            <InputLabel>Severity</InputLabel>
            <Select
              label="Severity"
              value={filters.severity}
              onChange={(e) => update('severity', e.target.value)}
            >
              {SEVERITY_OPTIONS.map((opt) => (
                <MenuItem key={opt.value || 'all'} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }}>
          <TextField
            label="From date"
            type="date"
            size="small"
            fullWidth
            value={filters.fromDate}
            onChange={(e) => update('fromDate', e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To date"
            type="date"
            size="small"
            fullWidth
            value={filters.toDate}
            onChange={(e) => update('toDate', e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          {hasActiveLogFilters(filters) && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<Clear />}
              onClick={() => onChange({ ...DEFAULT_LOG_FILTERS })}
              sx={{ whiteSpace: 'nowrap', minWidth: 120 }}
            >
              Clear filters
            </Button>
          )}
        </Stack>
      </Stack>
    </Paper>
  );
};

export default EventLogFilters;
