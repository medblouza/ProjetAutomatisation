import React from 'react';

export const Badge = ({
  className = '',
  variant = 'default',
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold select-none border transition-colors duration-200';
  
  const variants = {
    default: 'bg-primary/10 border-primary/20 text-primary-foreground dark:text-primary',
    secondary: 'bg-secondary border-border text-secondary-foreground',
    success: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-400',
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400',
    error: 'bg-rose-500/10 border-rose-500/20 text-rose-700 dark:text-rose-400',
    outline: 'bg-transparent border-border text-foreground',
  };

  return (
    <span
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
