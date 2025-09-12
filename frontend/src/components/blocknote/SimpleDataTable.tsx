import React from "react";

interface CsvData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

interface SimpleDataTableProps {
  csvData: CsvData;
  maxPreviewRows?: number;
}

export const SimpleDataTable: React.FC<SimpleDataTableProps> = ({
  csvData,
  maxPreviewRows = 50,
}) => {
  return (
    <div className="w-full overflow-hidden">
      <div className="border border-gray-600 rounded-lg bg-background w-full overflow-hidden">
        <div className="max-h-80 overflow-auto scrollbar-hide">
          <div className="overflow-x-auto scrollbar-hide">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 bg-muted/50">
                <tr>
                  <th colSpan={csvData.headers.length} className="px-3 py-3 text-center font-semibold border-b border-gray-600 bg-muted/50">
                    <div className="flex items-center justify-center gap-2">
                      <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="text-lg font-semibold">Data Preview</span>
                    </div>
                  </th>
                </tr>
                <tr>
                  {csvData.headers.map((header, index) => (
                    <th key={index} className="px-3 py-2 text-left font-medium border-b border-r border-gray-600 bg-muted/50 last:border-r-0 min-w-32">
                      <div className="truncate" title={header}>
                        {header}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {csvData.rows.slice(0, maxPreviewRows).map((row, rowIndex) => (
                  <tr key={rowIndex} className="hover:bg-muted/20">
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="px-3 py-2 border-b border-r border-gray-600 last:border-r-0 min-w-32">
                        <div className="truncate" title={cell}>
                          {cell || <span className="text-muted-foreground italic">empty</span>}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
