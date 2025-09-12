import React from "react";
import { BlockNoteViewRaw, useCreateBlockNote } from "@blocknote/react";
import { blockNoteToPlainText } from "@/lib/blocknote-config";

interface ChatEditorProps {
  onSubmit: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatEditor: React.FC<ChatEditorProps> = ({
  onSubmit,
  disabled = false,
  placeholder = "Ask a question about your data...",
}) => {
  const editor = useCreateBlockNote({
    initialContent: [
      {
        type: "paragraph",
        content: placeholder,
      },
    ],
  });

  const handleSubmit = () => {
    const content = editor.document;
    const plainText = blockNoteToPlainText(content);
    
    if (plainText.trim() && !disabled && plainText !== placeholder) {
      onSubmit(plainText);
      // Clear the editor after submission
      editor.replaceBlocks(editor.document, [
        {
          type: "paragraph",
          content: placeholder,
        },
      ]);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-3 w-full">
      {/* Plus button for file upload */}
      <button
        type="button"
        className="flex items-center justify-center w-12 h-12 border border-border rounded-lg bg-card hover:bg-accent hover:text-accent-foreground transition-colors"
        disabled={disabled}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>

      {/* BlockNote Editor */}
      <div className="flex-1 min-h-12 border border-border rounded-lg overflow-hidden">
        <BlockNoteViewRaw
          editor={editor}
          onKeyDown={handleKeyDown}
          className="min-h-12"
          theme="light"
          editable={true}
        />
      </div>

      {/* Send button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled}
        className="flex items-center justify-center w-12 h-12 bg-primary hover:bg-primary-hover text-primary-foreground rounded-lg transition-colors disabled:opacity-50"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  );
};
