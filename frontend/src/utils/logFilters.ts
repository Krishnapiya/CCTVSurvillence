export interface LogFilters {
  search: string;
  eventType: string;
  camera: string;
  severity: string;
  fromDate: string;
  toDate: string;
}

export const DEFAULT_LOG_FILTERS: LogFilters = {
  search: '',
  eventType: '',
  camera: '',
  severity: '',
  fromDate: '',
  toDate: '',
};

export function applyLogFilters(logs: any[], filters: LogFilters): any[] {
  return logs.filter((log) => {
    if (filters.search) {
      const q = filters.search.toLowerCase();
      const matches =
        log.event?.toLowerCase().includes(q) ||
        log.camera?.toLowerCase().includes(q) ||
        log.id?.toLowerCase().includes(q) ||
        log.eventType?.toLowerCase().includes(q);
      if (!matches) return false;
    }
    if (filters.eventType && log.eventType !== filters.eventType) return false;
    if (filters.camera && log.camera !== filters.camera) return false;
    if (filters.severity && log.severity !== filters.severity) return false;
    if (filters.fromDate) {
      const d = new Date(log.timestampRaw || log.timestamp);
      if (Number.isNaN(d.getTime()) || d < new Date(`${filters.fromDate}T00:00:00`)) return false;
    }
    if (filters.toDate) {
      const d = new Date(log.timestampRaw || log.timestamp);
      const end = new Date(`${filters.toDate}T23:59:59`);
      if (Number.isNaN(d.getTime()) || d > end) return false;
    }
    return true;
  });
}

export function hasActiveLogFilters(filters: LogFilters): boolean {
  return Object.values(filters).some((v) => Boolean(v));
}
