import React, { useState } from "react";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { FileSpreadsheet, BarChart3, ChevronDown, ChevronUp } from "lucide-react";

interface CsvData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

interface SimpleDataTableProps {
  csvData: CsvData;
  maxPreviewRows?: number;
  filename?: string;
}

export const SimpleDataTable: React.FC<SimpleDataTableProps> = ({
  csvData,
  maxPreviewRows = 50,
  filename,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const displayedRows = csvData.rows.slice(0, maxPreviewRows);
  const hasMoreRows = csvData.totalRows > maxPreviewRows;

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="w-full space-y-2">
      {/* Header Card */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
        <div className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <FileSpreadsheet className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {filename || 'Data Preview'}
                </h3>
              </div>
            </div>
            <button
              onClick={toggleCollapse}
              className="p-1.5 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors duration-200"
              aria-label={isCollapsed ? "Expand table" : "Collapse table"}
            >
              {isCollapsed ? (
                <ChevronDown className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              ) : (
                <ChevronUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              )}
            </button>
          </div>
        </div>
      </Card>

      {/* Modern Table - Collapsible */}
      <div 
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isCollapsed ? 'max-h-0 opacity-0' : 'max-h-96 opacity-100'
        }`}
      >
        <Card className="overflow-hidden border-0 shadow-lg bg-white dark:bg-gray-900">
          <div className="relative">
            {/* Gradient overlay for modern look */}
            <div className="absolute inset-0 bg-gradient-to-br from-white via-blue-50/30 to-indigo-50/30 dark:from-gray-900 dark:via-blue-950/10 dark:to-indigo-950/10 pointer-events-none" />
            
            <div className="relative max-h-64 overflow-auto">
              <Table className="w-full">
                <TableHeader className="sticky top-0 z-10">
                  <TableRow className="border-b border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
                    {csvData.headers.map((header, index) => (
                      <TableHead 
                        key={index} 
                        className="px-3 py-2 text-left font-medium text-gray-700 dark:text-gray-300 min-w-32"
                      >
                        <div className="flex items-center gap-1">
                          <div className="p-0.5 bg-blue-100 dark:bg-blue-900/40 rounded">
                            <BarChart3 className="w-2.5 h-2.5 text-blue-600 dark:text-blue-400" />
                          </div>
                          <span className="truncate text-xs font-medium" title={header}>
                            {header}
                          </span>
                        </div>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayedRows.map((row, rowIndex) => (
                    <TableRow 
                      key={rowIndex} 
                      className="border-b border-gray-100 dark:border-gray-800 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-indigo-50/50 dark:hover:from-blue-950/20 dark:hover:to-indigo-950/20 transition-all duration-200"
                    >
                      {row.map((cell, cellIndex) => (
                        <TableCell 
                          key={cellIndex} 
                          className="px-3 py-2 text-xs min-w-32 hover:bg-white/50 dark:hover:bg-gray-800/50 transition-colors duration-200"
                        >
                          <div className="flex items-center">
                            {cell ? (
                              <span 
                                className="truncate text-gray-700 dark:text-gray-300" 
                                title={cell}
                              >
                                {cell}
                              </span>
                            ) : (
                              <span className="text-gray-400 dark:text-gray-500 italic text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
                                empty
                              </span>
                            )}
                          </div>
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </Card>
      </div>

    </div>
  );
};
