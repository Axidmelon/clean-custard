import { BlockNoteEditor, PartialBlock } from "@blocknote/core";
import { BlockNoteViewRaw, useCreateBlockNote } from "@blocknote/react";
import "@blocknote/core/fonts/inter.css";
import "@blocknote/react/style.css";

// BlockNote configuration for our application
export const createBlockNoteEditor = (initialContent?: PartialBlock[]) => {
  return BlockNoteEditor.create({
    initialContent: initialContent || [
      {
        type: "paragraph",
        content: "Ask a question about your data...",
      },
    ],
    // Enable table blocks
    blockSpecs: {
      // We'll add custom table block specs here
    },
  });
};

// Utility function to convert BlockNote content to plain text
export const blockNoteToPlainText = (blocks: PartialBlock[]): string => {
  return blocks
    .map((block) => {
      if (block.type === "paragraph") {
        return block.content?.map((item) => 
          typeof item === "string" ? item : item.text || ""
        ).join("") || "";
      }
      if (block.type === "table") {
        // Convert table to readable text format
        return "Table content";
      }
      return "";
    })
    .join("\n")
    .trim();
};

// Utility function to convert CSV data to BlockNote table blocks
export const csvToBlockNoteTable = (headers: string[], rows: string[][]): PartialBlock => {
  return {
    type: "table",
    content: [
      // Header row
      {
        type: "tableRow",
        content: headers.map(header => ({
          type: "tableCell",
          content: [
            {
              type: "paragraph",
              content: header,
            },
          ],
        })),
      },
      // Data rows
      ...rows.map(row => ({
        type: "tableRow",
        content: row.map(cell => ({
          type: "tableCell",
          content: [
            {
              type: "paragraph",
              content: cell || "empty",
            },
          ],
        })),
      })),
    ],
  };
};

export { BlockNoteViewRaw, useCreateBlockNote };
