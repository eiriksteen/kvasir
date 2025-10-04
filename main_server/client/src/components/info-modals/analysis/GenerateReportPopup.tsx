'use client';

import { useState, useEffect } from 'react';
import { X, FileText, Code, Download } from 'lucide-react';
import { AnalysisObjectSmall } from '@/types/analysis';
import { useAnalysisObject } from '@/hooks/useAnalysis';

interface GenerateReportPopupProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: AnalysisObjectSmall;
}

export default function GenerateReportPopup({
  isOpen,
  onClose,
  analysis,
}: GenerateReportPopupProps) {
  const [filename, setFilename] = useState(analysis.name);
  const [includeCode, setIncludeCode] = useState(true);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  const { generateReport } = useAnalysisObject(analysis.projectId, analysis.id);

  // Reset form when popup opens
  useEffect(() => {
    if (isOpen) {
      setFilename(analysis.name);
      setIncludeCode(true);
      setIsGeneratingReport(false);
    }
  }, [isOpen, analysis.name]);

  // Handle escape key to close popup
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape, { capture: true });
    return () => document.removeEventListener('keydown', handleEscape, { capture: true });
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!filename.trim()) return;
    
    setIsGeneratingReport(true);
    try {
      await generateReport({
        analysisObjectId: analysis.id,
        generateReportRequest: {
          filename: filename.trim(),
          includeCode: includeCode
        }
      });
      onClose();
    } catch (error) {
      console.error('Error generating report:', error);
      // TODO: Add error handling UI
    } finally {
      setIsGeneratingReport(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-[#1a1625] border border-purple-900/30 rounded-lg p-6 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <FileText size={20} className="text-purple-400" />
            </div>
            <h3 className="text-lg font-medium text-white">Generate Report</h3>
          </div>
          <button 
            onClick={onClose}
            className="text-zinc-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-zinc-800/50"
          >
            <X size={20} />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Filename Input */}
          <div className="space-y-2">
            <label htmlFor="filename" className="block text-sm font-medium text-zinc-300">
              Report Filename
            </label>
            <input
              type="text"
              id="filename"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="Enter report filename..."
              className="w-full px-3 py-2 bg-zinc-900/50 border border-zinc-700/50 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-colors"
              required
              disabled={isGeneratingReport}
            />
            <p className="text-xs text-zinc-500">
              The report will be saved with this filename
            </p>
          </div>

          {/* Include Code Toggle */}
          <div className="flex items-center justify-between p-3 bg-zinc-900/30 border border-zinc-700/30 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-1.5 bg-blue-500/20 rounded-lg">
                <Code size={16} className="text-blue-400" />
              </div>
              <div>
                <label htmlFor="includeCode" className="block text-sm font-medium text-zinc-300">
                  Include Python Code
                </label>
                <p className="text-xs text-zinc-500">
                  Include the generated Python code in the report
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id="includeCode"
                checked={includeCode}
                onChange={(e) => setIncludeCode(e.target.checked)}
                className="sr-only peer"
                disabled={isGeneratingReport}
              />
              <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600 disabled:opacity-50"></div>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isGeneratingReport}
              className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!filename.trim() || isGeneratingReport}
              className="px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isGeneratingReport ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Generating...
                </>
              ) : (
                <>
                  <Download size={16} />
                  Generate Report
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}