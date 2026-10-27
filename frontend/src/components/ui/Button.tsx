/** Reusable Button component */
import { type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export function Button({ variant = 'primary', size = 'md', className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
        {
          'bg-forest text-white hover:bg-leaf focus:ring-forest': variant === 'primary',
          'bg-gold text-dark-text hover:bg-amber-500 focus:ring-gold': variant === 'secondary',
          'border-2 border-forest text-forest hover:bg-pale-green focus:ring-forest': variant === 'outline',
          'text-forest hover:bg-pale-green focus:ring-forest': variant === 'ghost',
          'bg-error text-white hover:bg-red-700 focus:ring-error': variant === 'danger',
        },
        {
          'px-3 py-1.5 text-sm': size === 'sm',
          'px-4 py-2 text-sm': size === 'md',
          'px-6 py-3 text-base': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
