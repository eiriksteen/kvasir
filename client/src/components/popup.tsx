import React, { useEffect, useState } from 'react';

interface PopupProps {
  message: string;
  onClose?: () => void;
  type: "analysis" | "automation";
}

const Popup: React.FC<PopupProps> = ({ message, onClose, type }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      if (onClose) onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  const handleClose = () => {
    setIsVisible(false);
    if (onClose) onClose();
  };

  if (!isVisible) return null;

  const getBackgroundColor = () => {
    switch (type) {
      case "analysis":
        return "bg-purple-900/30 text-purple-300 border border-purple-800/50";
      case "automation":
        return "bg-blue-900/30 text-blue-300 border border-blue-800/50";
      default:
        return "bg-white text-gray-800";
    }
  };

  return (
    <div className={`fixed top-4 right-4 shadow-lg rounded-lg p-4 max-w-sm z-50 ${getBackgroundColor()}`}>
      <div className="flex justify-between items-start">
        <p>{message}</p>
        <button
          onClick={handleClose}
          className="ml-4 text-zinc-400 hover:text-white focus:outline-none"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default Popup;
