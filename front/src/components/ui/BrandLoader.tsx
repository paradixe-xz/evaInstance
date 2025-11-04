import React from 'react';

interface BrandLoaderProps {
  size?: 'lg' | 'md' | 'sm';
  label?: string;
  className?: string;
}

const BrandLoader: React.FC<BrandLoaderProps> = ({ size = 'lg', label, className }) => {
  const tileSize = size === 'lg' ? 'h-20 w-20 rounded-2xl' : size === 'md' ? 'h-10 w-10 rounded-xl' : 'h-5 w-5 rounded-lg';
  const textSize = size === 'lg' ? 'text-4xl' : size === 'md' ? 'text-xl' : 'text-xs';
  const animate = size === 'sm' ? 'animate-pulse' : '';

  const tile = (
    <div className={`bg-gradient-to-br from-green-300 to-green-500 flex items-center justify-center shadow-sm ${tileSize} ${animate}`}>
      <span className={`text-white font-bold ${textSize}`}>E</span>
    </div>
  );

  if (label) {
    return (
      <div className={`flex items-center justify-center gap-3 ${className || ''}`}>
        {tile}
        <span className="text-slate-900 font-semibold">{label}</span>
      </div>
    );
  }

  return tile;
};

export default BrandLoader;