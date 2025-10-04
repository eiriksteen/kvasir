'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface ErrorBannerProps {
  error: string;
  onClose: () => void;
}

export default function ErrorBanner({ 
  error, 
  onClose
}: ErrorBannerProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const maxLength = 100;
  const shouldTruncate = error.length > maxLength;
  const displayText = isExpanded ? error : error.slice(0, maxLength) + (shouldTruncate ? '...' : '');

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  const handleClose = () => {
    setIsVisible(false);
    onClose();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed top-4 right-4 w-[300px] z-[9999] bg-red-500 text-white p-3 rounded-lg shadow-lg">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium break-words">
            {displayText}
          </div>
          {shouldTruncate && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs underline mt-1 hover:text-red-100 transition-colors"
            >
              {isExpanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
        <button
          onClick={handleClose}
          className="flex-shrink-0 p-1 hover:bg-red-600 rounded transition-colors"
          aria-label="Close error banner"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  );
}