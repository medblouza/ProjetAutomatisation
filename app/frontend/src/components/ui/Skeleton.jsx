import React from 'react';

export const Skeleton = ({ className = '', ...props }) => {
  return (
    <div
      className={`animate-pulse rounded-md bg-muted/70 ${className}`}
      {...props}
    />
  );
};

export const SkeletonCard = () => {
  return (
    <div className="border border-border rounded-2xl p-6 space-y-4 bg-card shadow-sm">
      <Skeleton className="h-4 w-2/5 rounded" />
      <Skeleton className="h-8 w-4/5 rounded-lg" />
      <div className="space-y-2 pt-2">
        <Skeleton className="h-3 w-full rounded" />
        <Skeleton className="h-3 w-5/6 rounded" />
      </div>
    </div>
  );
};

export const SkeletonList = ({ count = 3 }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, idx) => (
        <div key={idx} className="flex items-center space-x-4 p-4 rounded-xl border border-border bg-card">
          <Skeleton className="h-10 w-10 rounded-full shrink-0" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-4 w-1/4 rounded" />
            <Skeleton className="h-3 w-3/4 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
};
export default Skeleton;
