import React from "react";
import { BlockNoteViewRaw, useCreateBlockNote } from "@blocknote/react";
import { csvToBlockNoteTable } from "@/lib/blocknote-config";

interface CsvData {
  headers: string[];
  rows: string[][];
  totalRows: number;
}

interface DataTableProps {
  csvData: CsvData;
  maxPreviewRows?: number;
}

export const DataTable: React.FC<DataTableProps> = ({
  csvData,
  maxPreviewRows = 50,
}) => {
  // Convert CSV data to BlockNote table format
  const tableBlock = csvToBlockNoteTable(
    csvData.headers,
    csvData.rows.slice(0, maxPreviewRows)
  );

  const editor = useCreateBlockNote({
    initialContent: [tableBlock],
    editable: false, // Make it read-only for data display
  });

  return (
    <div className="w-full overflow-hidden">
      <div className="text-sm text-muted-foreground mb-3">
        Showing preview of {csvData.totalRows} rows with {csvData.headers.length} columns
      </div>
      
      <div className="border rounded-lg bg-background w-full overflow-hidden">
        <div className="max-h-80 overflow-auto">
          <BlockNoteViewRaw
            editor={editor}
            editable={false}
            className="w-full"
            theme="light"
          />
        </div>
        
        {csvData.totalRows > maxPreviewRows && (
          <div className="p-3 bg-muted/30 text-center text-sm text-muted-foreground border-t">
            Showing first {maxPreviewRows} rows of {csvData.totalRows} total rows
          </div>
        )}
      </div>
    </div>
  );
};
