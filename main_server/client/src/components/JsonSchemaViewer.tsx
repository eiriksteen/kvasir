import { ChevronDown, ChevronRight, LucideIcon } from 'lucide-react';
import { useState } from 'react';

interface JsonSchemaViewerProps {
  schema: Record<string, unknown>;
  className?: string;
  title?: string;
  icon?: LucideIcon;
  iconColor?: string;
}

type SchemaDefinition = {
  type?: string | string[];
  description?: string;
  properties?: Record<string, unknown>;
  items?: unknown;
  minimum?: number;
  maximum?: number;
  default?: unknown;
  enum?: unknown[];
  required?: string[];
  [key: string]: unknown;
};

function isSchemaDefinition(value: unknown): value is SchemaDefinition {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function formatSchemaValue(value: unknown): string {
  if (value === null) return 'null';
  if (value === undefined) return '';
  if (typeof value === 'string') return `"${value}"`;
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return String(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    return `[${value.map(v => formatSchemaValue(v)).join(', ')}]`;
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

function getSchemaType(schema: SchemaDefinition): string {
  if (schema.type) {
    if (Array.isArray(schema.type)) {
      return schema.type.join(' | ');
    }
    return schema.type;
  }
  return 'any';
}

function hasNestedContent(schema: SchemaDefinition): boolean {
  return (
    (schema.type === 'object' && schema.properties && Object.keys(schema.properties).length > 0) ||
    (schema.type === 'array' && schema.items !== undefined)
  );
}

interface SchemaPropertyProps {
  propertyName: string;
  schema: SchemaDefinition;
  level: number;
  expandedKeys: Set<string>;
  onToggle: (key: string) => void;
}

function SchemaProperty({ propertyName, schema, level, expandedKeys, onToggle }: SchemaPropertyProps) {
  const fullKey = `${level}-${propertyName}`;
  const isExpanded = expandedKeys.has(fullKey);
  const schemaType = getSchemaType(schema);
  const hasNested = hasNestedContent(schema);
  
  const handleClick = () => {
    if (hasNested) {
      onToggle(fullKey);
    }
  };

  // Collect metadata fields (everything except type, properties, items)
  const metadataFields: Array<[string, unknown]> = [];
  Object.entries(schema).forEach(([key, value]) => {
    if (key !== 'type' && key !== 'properties' && key !== 'items' && value !== undefined) {
      metadataFields.push([key, value]);
    }
  });

  return (
    <div className="select-none">
      <div
        className={`flex items-start gap-1.5 py-1 px-1.5 rounded transition-colors ${
          hasNested ? 'cursor-pointer hover:bg-gray-50' : ''
        }`}
        onClick={handleClick}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-medium text-gray-900 font-mono">{propertyName}</span>
            <span className="text-[10px] px-1 py-0.5 bg-gray-200 rounded text-gray-600 font-mono">
              {schemaType}
            </span>
            {metadataFields.map(([key, value]) => (
              <span key={key} className="text-xs text-gray-600 font-mono">
                {key}: {formatSchemaValue(value)}
              </span>
            ))}
          </div>
        </div>
        
        {hasNested && (
          <div className="flex items-center flex-shrink-0">
            {isExpanded ? (
              <ChevronDown size={12} className="text-gray-500" />
            ) : (
              <ChevronRight size={12} className="text-gray-500" />
            )}
          </div>
        )}
      </div>

      {hasNested && isExpanded && (
        <div className="ml-3 mt-0.5 border-l border-gray-200 pl-2 space-y-0.5">
          {schema.type === 'object' && schema.properties && 
            Object.entries(schema.properties).map(([nestedKey, nestedValue]) => {
              if (isSchemaDefinition(nestedValue)) {
                return (
                  <SchemaProperty
                    key={`${fullKey}-${nestedKey}`}
                    propertyName={nestedKey}
                    schema={nestedValue}
                    level={level + 1}
                    expandedKeys={expandedKeys}
                    onToggle={onToggle}
                  />
                );
              }
              return null;
            })
          }
          {schema.type === 'array' && schema.items && isSchemaDefinition(schema.items) ? (
            <div className="ml-2">
              <div className="text-xs text-gray-500 mb-1 font-mono">items:</div>
              <SchemaProperty
                propertyName=""
                schema={schema.items as SchemaDefinition}
                level={level + 1}
                expandedKeys={expandedKeys}
                onToggle={onToggle}
              />
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default function JsonSchemaViewer({ schema, className = '', title, icon: Icon, iconColor = '#840B08' }: JsonSchemaViewerProps) {
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
            <div 
              className="p-2 rounded-lg" 
              style={{ 
                backgroundColor: hexToRgba(iconColor, 0.2),
              }}
            >
              <Icon size={18} style={{ color: iconColor }} />
            </div>
          )}
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
      )}
      <div className="overflow-auto flex-1 min-h-0">
        <div className="space-y-0.5">
          {Object.entries(schema).map(([key, value]) => {
            if (isSchemaDefinition(value)) {
              return (
                <SchemaProperty
                  key={key}
                  propertyName={key}
                  schema={value}
                  level={0}
                  expandedKeys={expandedKeys}
                  onToggle={toggleKey}
                />
              );
            }
            return null;
          })}
        </div>
      </div>
    </div>
  );
}
