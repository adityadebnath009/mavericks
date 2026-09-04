export const getSeverityBand = (score) => {
  if (score <= 20) return { risk: 'SAFE', color: '#18C7A0' };
  if (score <= 50) return { risk: 'MODERATE', color: '#FFB547' };
  if (score <= 75) return { risk: 'HIGH', color: '#FF5C5C' };
  return { risk: 'EXTREME', color: '#FF5C5C' };
};

export const SEVERITY_BANDS = {
  SAFE: { min: 0, max: 20, color: '#18C7A0', label: 'SAFE' },
  MODERATE: { min: 21, max: 50, color: '#FFB547', label: 'MODERATE' },
  HIGH: { min: 51, max: 75, color: '#FF5C5C', label: 'HIGH' },
  EXTREME: { min: 76, max: 100, color: '#FF5C5C', label: 'EXTREME' }
};
