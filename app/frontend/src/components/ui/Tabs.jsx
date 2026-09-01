import React from 'react';

export const Tabs = ({ value, onValueChange, className = '', children }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { value, onValueChange });
        }
        return child;
      })}
    </div>
  );
};

export const TabsList = ({ value, onValueChange, className = '', children }) => {
  return (
    <div className={`inline-flex items-center justify-start p-1 bg-secondary rounded-xl border border-border/80 ${className}`}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            active: value === child.props.value,
            onClick: () => onValueChange(child.props.value)
          });
        }
        return child;
      })}
    </div>
  );
};

export const TabsTrigger = ({ value, active, onClick, className = '', children, disabled }) => {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 focus:outline-none disabled:opacity-50 select-none ${
        active
          ? 'bg-card text-foreground shadow-sm font-bold border border-border/50'
          : 'text-muted-foreground hover:text-foreground hover:bg-card/30'
      } ${className}`}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({ value, activeValue, className = '', children }) => {
  const isSelected = value === activeValue;
  if (!isSelected) return null;
  
  return (
    <div className={`focus:outline-none animate-fade-in ${className}`}>
      {children}
    </div>
  );
};
