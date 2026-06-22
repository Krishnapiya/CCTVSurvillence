export const EVENT_TYPE_LABELS: Record<string, string> = {
  fire: 'Fire Detection',
  smoke: 'Smoke Detection',
  intrusion: 'Human Detection',
  human_detection: 'Human Detection',
  mobile_usage: 'Mobile Phone Detection',
  bag: 'Bag Detection',
  bench: 'Bench Detection',
  fainting: 'Fainting Detection',
  fight: 'Fight Detection',
  smoking: 'Smoking Detection',
  suicide_risk: 'Suicide Risk',
  uniform_violation: 'Uniform Violation',
  projectile: 'Projectile',
};

export const EVENT_TYPE_OPTIONS = Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export const SEVERITY_OPTIONS = [
  { value: '', label: 'All severities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];
