import React from "react";
import { cn } from "@/lib/utils";

interface RichTextDisplayProps {
  content: string;
  className?: string;
  variant?: "default" | "error" | "success" | "info";
}

export const RichTextDisplay: React.FC<RichTextDisplayProps> = ({
  content,
  className,
  variant = "default",
}) => {
  // Parse content for basic formatting
  const parseContent = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, index) => {
      // Handle bullet points
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return (
          <div key={index} className="flex items-start gap-2 mb-1">
            <span className="text-muted-foreground mt-1">•</span>
            <span className="flex-1">{line.trim().substring(2)}</span>
          </div>
        );
      }
      
      // Handle numbered lists
      if (/^\d+\.\s/.test(line.trim())) {
        return (
          <div key={index} className="flex items-start gap-2 mb-1">
            <span className="text-muted-foreground mt-1">{line.trim().split('.')[0]}.</span>
            <span className="flex-1">{line.trim().substring(line.trim().indexOf('.') + 1).trim()}</span>
          </div>
        );
      }
      
      // Handle headings (lines that are all caps or start with #)
      if (line.trim().toUpperCase() === line.trim() && line.trim().length > 3) {
        return (
          <h2 key={index} className="text-lg font-bold text-foreground mb-2 mt-3 first:mt-0">
            {line.trim()}
          </h2>
        );
      }
      
      if (line.trim().startsWith('#')) {
        const level = line.match(/^#+/)?.[0].length || 1;
        const text = line.replace(/^#+\s*/, '');
        const HeadingTag = `h${Math.min(level, 6)}` as keyof JSX.IntrinsicElements;
        return (
          <HeadingTag key={index} className={cn(
            "font-bold text-foreground mb-2 mt-3 first:mt-0",
            level === 1 && "text-xl",
            level === 2 && "text-lg", 
            level === 3 && "text-base"
          )}>
            {text}
          </HeadingTag>
        );
      }
      
      // Handle bold text (**text** or __text__)
      if (line.includes('**') || line.includes('__')) {
        const parts = line.split(/(\*\*.*?\*\*|__.*?__)/);
        return (
          <p key={index} className="mb-2">
            {parts.map((part, partIndex) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={partIndex}>{part.slice(2, -2)}</strong>;
              }
              if (part.startsWith('__') && part.endsWith('__')) {
                return <strong key={partIndex}>{part.slice(2, -2)}</strong>;
              }
              return part;
            })}
          </p>
        );
      }
      
      // Handle italic text (*text* or _text_)
      if (line.includes('*') || line.includes('_')) {
        const parts = line.split(/(\*.*?\*|_.*?_)/);
        return (
          <p key={index} className="mb-2">
            {parts.map((part, partIndex) => {
              if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
                return <em key={partIndex}>{part.slice(1, -1)}</em>;
              }
              if (part.startsWith('_') && part.endsWith('_') && !part.startsWith('__')) {
                return <em key={partIndex}>{part.slice(1, -1)}</em>;
              }
              return part;
            })}
          </p>
        );
      }
      
      // Regular paragraphs
      if (line.trim()) {
        return (
          <p key={index} className="mb-2 text-foreground">
            {line}
          </p>
        );
      }
      
      // Empty lines
      return <div key={index} className="mb-2" />;
    });
  };

  const variantStyles = {
    default: "",
    error: "text-red-600",
    success: "text-green-600", 
    info: "text-blue-600"
  };

  return (
    <div className={cn(
      "py-2",
      variantStyles[variant],
      className
    )}>
      <div className="prose prose-sm max-w-none">
        {parseContent(content)}
      </div>
    </div>
  );
};
