import React from "react";
import { UUID } from "crypto";
import { useTable } from "@/hooks/useTable";

interface TableWrapperProps {
  projectId: UUID;
  tablePath: string;
}

const TableWrapper = ({ 
  projectId, 
  tablePath 
}: TableWrapperProps) => {
  const { table, isLoading, isError } = useTable(
    projectId,
    tablePath
  );

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center text-zinc-500">
        Loading table...
      </div>
    );
  }

  if (isError || !table) {
    return (
      <div className="w-full h-full flex items-center justify-center text-red-500">
        Failed to load table
      </div>
    );
  }

  // Get all column names (excluding the index column)
  const columns = Object.keys(table.data).filter(col => col !== table.indexColumn);
  const indexData = table.data[table.indexColumn];

  console.log(table);
  console.log(indexData);
  console.log(columns);

  return (
    <div className="w-full overflow-x-auto">
      <table className="min-w-full border-collapse border border-gray-300 text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="border border-gray-300 px-3 py-2 text-left font-semibold">
              {table.indexColumn}
            </th>
            {columns.map((col) => (
              <th key={col} className="border border-gray-300 px-3 py-2 text-left font-semibold">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {indexData && indexData.map((_, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-50">
              <td className="border border-gray-300 px-3 py-2 font-medium">
                {indexData[rowIndex]}
              </td>
              {columns.map((col) => (
                <td key={col} className="border border-gray-300 px-3 py-2">
                  {table.data[col][rowIndex]?.toString() ?? ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TableWrapper;

