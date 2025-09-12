import React, { useState } from "react";
import { Plus, Send } from "lucide-react";

interface SimpleChatEditorProps {
  onSubmit: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
  onFileUpload?: () => void;
  allowFileUploadWhenDisabled?: boolean;
}

export const SimpleChatEditor: React.FC<SimpleChatEditorProps> = ({
  onSubmit,
  disabled = false,
  placeholder = "Connect data and start chatting!",
  onFileUpload,
  allowFileUploadWhenDisabled = true,
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
    <div className="relative w-full">
      {/* Modern Chat Input Container */}
      <div className="relative flex items-center w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500/50">
        
        {/* Plus Button */}
        <button
          type="button"
          onClick={() => {
            console.log('Plus button clicked!');
            onFileUpload?.();
          }}
          className={`flex items-center justify-center w-10 h-10 m-2 rounded-xl transition-all duration-200 group ${
            disabled && !allowFileUploadWhenDisabled
              ? 'bg-gray-50 dark:bg-gray-800 cursor-not-allowed opacity-50'
              : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 hover:scale-105 cursor-pointer'
          }`}
          disabled={disabled && !allowFileUploadWhenDisabled}
          title="Upload CSV file"
        >
          <Plus className={`w-5 h-5 transition-colors ${
            disabled && !allowFileUploadWhenDisabled
              ? 'text-gray-400 dark:text-gray-500'
              : 'text-gray-600 dark:text-gray-400 group-hover:text-gray-800 dark:group-hover:text-gray-200'
          }`} />
        </button>

        {/* Input Field */}
        <div className="flex-1 px-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full min-h-12 max-h-32 py-3 px-2 bg-transparent border-none focus:outline-none resize-none text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 text-sm leading-relaxed"
            rows={1}
            style={{
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
            }}
          />
        </div>


        {/* Send Button */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          className="flex items-center justify-center w-10 h-10 m-2 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
        >
          <Send className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </button>
      </div>

      {/* Subtle gradient overlay for extra modern look */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-transparent to-purple-500/5 rounded-2xl pointer-events-none" />
    </div>
  );
};
