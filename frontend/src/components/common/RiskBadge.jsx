import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, ShieldAlert, CheckCircle2 } from 'lucide-react';

const SIZE_VARIANTS = {
  xs: 'px-1.5 py-0.5 text-[8px] gap-1',
  sm: 'px-2 py-0.5 text-[9px] gap-1.5',
  md: 'px-2.5 py-1 text-[10px] gap-2',
  lg: 'px-3.5 py-1.5 text-xs gap-2.5 font-bold'
};

const ICON_SIZES = {
  xs: 'w-2.5 h-2.5',
  sm: 'w-3 h-3',
  md: 'w-3.5 h-3.5',
  lg: 'w-4 h-4'
};

export function RiskBadge({
  level = 'LOW',
  score = null,
  label = null,
  showIcon = true,
  size = 'md',
  pulse = false,
  className = ''
}) {
  const normLevel = (level || 'LOW').toString().toUpperCase().trim();

  let badgeConfig = {
    classes: 'bg-[#18C7A0]/10 text-[#18C7A0] border-[#18C7A0]/35 shadow-[0_0_8px_rgba(24,199,160,0.15)]',
    icon: ShieldCheck,
    defaultLabel: 'SAFE (LOW RISK)',
    isHazard: false
  };

  if (normLevel === 'EXTREME') {
    badgeConfig = {
      classes: 'bg-[#FF5C5C]/25 text-[#FF5C5C] border-[#FF5C5C] shadow-[0_0_15px_rgba(255,92,92,0.4)] font-black animate-pulse',
      icon: AlertOctagon,
      defaultLabel: 'EXTREME HAZARD',
      isHazard: true
    };
  } else if (normLevel === 'HIGH' || normLevel === 'DANGER' || normLevel === 'RESTRICTED') {
    badgeConfig = {
      classes: 'bg-[#FF5C5C]/12 text-[#FF5C5C] border-[#FF5C5C]/40 shadow-[0_0_10px_rgba(255,92,92,0.2)] font-bold',
      icon: AlertOctagon,
      defaultLabel: normLevel === 'RESTRICTED' ? 'RESTRICTED ZONE' : 'HIGH RISK',
      isHazard: true
    };
  } else if (normLevel === 'MODERATE' || normLevel === 'CAUTION' || normLevel === 'WARNING' || normLevel === 'ALERT') {
    badgeConfig = {
      classes: 'bg-[#FFB547]/12 text-[#FFB547] border-[#FFB547]/40 shadow-[0_0_10px_rgba(255,181,71,0.2)] font-bold',
      icon: AlertTriangle,
      defaultLabel: normLevel === 'WARNING' ? 'WEATHER WARNING' : normLevel === 'ALERT' ? 'SVAS ALERT' : 'MODERATE RISK',
      isHazard: false
    };
  } else if (normLevel === 'CLEAR' || normLevel === 'OPTIMAL' || normLevel === 'SAFE' || normLevel === 'LOW') {
    badgeConfig = {
      classes: 'bg-[#18C7A0]/10 text-[#18C7A0] border-[#18C7A0]/35 shadow-[0_0_8px_rgba(24,199,160,0.15)] font-bold',
      icon: ShieldCheck,
      defaultLabel: normLevel === 'CLEAR' ? 'GEOFENCE CLEAR' : 'SAFE (LOW RISK)',
      isHazard: false
    };
  }

  const Icon = badgeConfig.icon;
  const sizeClass = SIZE_VARIANTS[size] || SIZE_VARIANTS.md;
  const iconSizeClass = ICON_SIZES[size] || ICON_SIZES.md;
  const shouldPulse = pulse || (normLevel === 'EXTREME');

  return (
    <span 
      className={`inline-flex items-center rounded-full border font-mono uppercase tracking-wider transition-all select-none ${sizeClass} ${badgeConfig.classes} ${shouldPulse ? 'animate-pulse' : ''} ${className}`}
    >
      {showIcon && <Icon className={`${iconSizeClass} shrink-0`} />}
      <span>{label || badgeConfig.defaultLabel}</span>
      {score != null && (
        <span className="opacity-80 font-normal pl-0.5 border-l border-current/30 ml-0.5">
          {score}
        </span>
      )}
    </span>
  );
}

export default RiskBadge;
