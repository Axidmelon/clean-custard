import React, { useState } from "react";

interface SimpleChatEditorProps {
  onSubmit: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const SimpleChatEditor: React.FC<SimpleChatEditorProps> = ({
  onSubmit,
  disabled = false,
  placeholder = "Ask a question about your data...",
}) => {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSubmit(input.trim());
      setInput("");
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

      {/* Simple Text Input */}
      <div className="flex-1 min-h-12 border border-border rounded-lg overflow-hidden">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full h-12 px-4 py-3 bg-card border-none focus:outline-none resize-none"
          rows={1}
        />
      </div>

      {/* Send button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="flex items-center justify-center w-12 h-12 bg-primary hover:bg-primary-hover text-primary-foreground rounded-lg transition-colors disabled:opacity-50"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  );
};
