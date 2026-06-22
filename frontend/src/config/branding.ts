export const branding = {
  organization: 'Kerala Prisons & Correctional Services',
  productLine: 'CCTV Event Detection',
  unitLabel: 'Station Surveillance Unit',
  stationCode: import.meta.env.VITE_STATION_CODE || 'PHQ-001',
  stationName: import.meta.env.VITE_STATION_NAME || 'Prisons Headquarters',
  installationId: import.meta.env.VITE_INSTALLATION_ID || 'INST-001',
  masterDashboardHint: 'Data syncs to the Master Dashboard at headquarters',
}

export function getPageSubtitle() {
  return `${branding.productLine} — ${branding.unitLabel}`
}

export function getStationTitle() {
  return `${branding.stationName} (${branding.stationCode})`
}
