import { Flower2 } from 'lucide-react';

interface FlowerLogoProps {
  className?: string;
}

const FlowerLogo = ({ className = 'w-16 h-16 text-primary' }: FlowerLogoProps) => (
  <div className={`${className} flex items-center justify-center`}>
    <Flower2 className="w-3/4 h-3/4" />
  </div>
);

export default FlowerLogo;