'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import ErrorBanner from '@/components/ErrorBanner';

interface ErrorContextType {
  error: string | null;
  showError: (message: string) => void;
  clearError: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

function ErrorProvider({ children }: { children: ReactNode }) {
  const [error, setError] = useState<string | null>(null);

  const showError = (message: string) => {
    setError(message);
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <ErrorContext.Provider value={{ error, showError, clearError }}>
      {children}
      {error && (
        <ErrorBanner 
          error={error}
          onClose={clearError}
        />
      )}
    </ErrorContext.Provider>
  );
}

export default function ErrorProviderWrapper({ children }: { children: React.ReactNode }) {
  return (
    <ErrorProvider>
      {children}
    </ErrorProvider>
  );
}

export function useError() {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
}