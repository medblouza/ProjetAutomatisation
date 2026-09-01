import React from 'react';

export const Input = React.forwardRef(({
  className = '',
  type = 'text',
  label,
  error,
  id,
  ...props
}, ref) => {
  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-xs font-semibold text-muted-foreground select-none uppercase tracking-wider">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={id}
        type={type}
        className={`w-full px-4 py-3 rounded-xl border border-input bg-card text-foreground text-sm transition-all placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50 ${
          error ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : ''
        } ${className}`}
        {...props}
      />
      {error && (
        <span className="text-xs text-destructive font-medium mt-0.5">
          {error}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';
export default Input;
