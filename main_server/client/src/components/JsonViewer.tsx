import { ChevronDown, ChevronRight, LucideIcon } from 'lucide-react';
import { useState } from 'react';

interface JsonViewerProps {
  data: Record<string, unknown>;
  className?: string;
  title?: string;
  icon?: LucideIcon;
}

type JsonValue = unknown;
type JsonObject = Record<string, unknown>;
type JsonArray = unknown[];

function isObject(value: JsonValue): value is JsonObject {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isArray(value: JsonValue): value is JsonArray {
  return Array.isArray(value);
}

function formatValue(value: JsonValue): string {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (typeof value === 'string') return `"${value}"`;
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return String(value);
  if (isArray(value)) return `[${value.length} items]`;
  if (isObject(value)) return `{${Object.keys(value).length} keys}`;
  return String(value);
}

function getValueType(value: JsonValue): string {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (isArray(value)) return 'array';
  if (isObject(value)) return 'object';
  return typeof value;
}

interface JsonNodeProps {
  fieldKey: string;
  value: JsonValue;
  level: number;
  expandedKeys: Set<string>;
  onToggle: (key: string) => void;
}

function JsonNode({ fieldKey, value, level, expandedKeys, onToggle }: JsonNodeProps) {
  const fullKey = `${level}-${fieldKey}`;
  const isExpanded = expandedKeys.has(fullKey);
  const isObjectValue = isObject(value);
  const isArrayValue = isArray(value);
  const isExpandable = isObjectValue || isArrayValue;

  const handleClick = () => {
    if (isExpandable) {
      onToggle(fullKey);
    }
  };

  return (
    <div className="select-none">
      <div
        className={`flex items-start gap-1.5 py-1 px-1.5 rounded transition-colors ${
          isExpandable ? 'cursor-pointer hover:bg-gray-50' : ''
        }`}
        onClick={handleClick}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-gray-900 font-mono">{fieldKey}</span>
            <span className="text-[10px] px-1 py-0.5 bg-gray-200 rounded text-gray-600 font-mono">
              {getValueType(value)}
            </span>
            {!isExpandable && (
              <span className="text-xs text-gray-600 font-mono">{formatValue(value)}</span>
            )}
            {isExpandable && (
              <span className="text-xs text-gray-500">
                {isArrayValue ? `[${(value as JsonArray).length}]` : `{${Object.keys(value as JsonObject).length}}`}
              </span>
            )}
          </div>
        </div>
        
        {isExpandable && (
          <div className="flex items-center flex-shrink-0">
            {isExpanded ? (
              <ChevronDown size={12} className="text-gray-500" />
            ) : (
              <ChevronRight size={12} className="text-gray-500" />
            )}
          </div>
        )}
      </div>

      {isExpandable && isExpanded && (
        <div className="ml-3 mt-0.5 border-l border-gray-200 pl-2 space-y-0.5">
          {isArrayValue ? (
            (value as JsonArray).map((item, index) => (
              <JsonNode
                key={`${fullKey}-${index}`}
                fieldKey={`[${index}]`}
                value={item}
                level={level + 1}
                expandedKeys={expandedKeys}
                onToggle={onToggle}
              />
            ))
          ) : (
            Object.entries(value as JsonObject).map(([nestedKey, nestedValue]) => (
              <JsonNode
                key={`${fullKey}-${nestedKey}`}
                fieldKey={nestedKey}
                value={nestedValue}
                level={level + 1}
                expandedKeys={expandedKeys}
                onToggle={onToggle}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default function JsonViewer({ data, className = '', title, icon: Icon }: JsonViewerProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  const toggleKey = (key: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  return (
    <div className={`flex flex-col ${className}`}>
      {title && (
        <div className="flex items-center gap-3 mb-3 flex-shrink-0">
          {Icon && (
            <div className="p-2 bg-gray-500/20 rounded-lg">
              <Icon size={18} className="text-gray-600" />
            </div>
          )}
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              {title}
            </h3>
          </div>
        </div>
      )}
      <div className="overflow-auto flex-1 min-h-0">
        <div className="space-y-0.5">
          {Object.entries(data).map(([key, value]) => (
            <JsonNode
              key={key}
              fieldKey={key}
              value={value}
              level={0}
              expandedKeys={expandedKeys}
              onToggle={toggleKey}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

