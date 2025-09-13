import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, Info } from 'lucide-react';

interface ServiceExplanationProps {
  aiRouting?: {
    service_used: string;
    reasoning: string;
    confidence: number;
  };
  isLoading?: boolean;
}

const ServiceExplanation: React.FC<ServiceExplanationProps> = ({ 
  aiRouting, 
  isLoading = false 
}) => {
  if (isLoading) {
    return (
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <div>
            <div className="font-medium text-blue-700">AI is analyzing your question...</div>
            <div className="text-sm text-blue-600">Determining the best service for your query</div>
          </div>
        </div>
      </Card>
    );
  }

  if (!aiRouting) return null;

  const getServiceIcon = (service: string) => {
    switch (service) {
      case 'csv_to_sql_converter': return '🗃️';
      case 'data_analysis_service': return '📊';
      case 'database': return '🗄️';
      default: return '🤖';
    }
  };

  const getServiceName = (service: string) => {
    switch (service) {
      case 'csv_to_sql_converter': return 'CSV to SQL Converter';
      case 'data_analysis_service': return 'Data Analysis Service';
      case 'database': return 'Database Service';
      default: return 'Unknown Service';
    }
  };

  const getServiceDescription = (service: string) => {
    switch (service) {
      case 'csv_to_sql_converter': return 'SQL queries on CSV data (fast, familiar SQL syntax)';
      case 'data_analysis_service': return 'Pandas operations on CSV data (powerful statistical analysis)';
      case 'database': return 'Real-time database queries (production data)';
      default: return 'AI-selected service';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800 border-green-200';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-red-100 text-red-800 border-red-200';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckCircle className="h-4 w-4" />;
    if (confidence >= 0.6) return <AlertCircle className="h-4 w-4" />;
    return <Info className="h-4 w-4" />;
  };

  return (
    <Card className="p-4 bg-blue-50 border-blue-200">
      <div className="flex items-start gap-3">
        <div className="text-2xl">{getServiceIcon(aiRouting.service_used)}</div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-blue-700">AI Selected:</span>
            <span className="font-semibold text-blue-800">
              {getServiceName(aiRouting.service_used)}
            </span>
            <Badge 
              variant="secondary" 
              className={`text-xs ${getConfidenceColor(aiRouting.confidence)}`}
            >
              <span className="mr-1">{getConfidenceIcon(aiRouting.confidence)}</span>
              {Math.round(aiRouting.confidence * 100)}% confidence
            </Badge>
          </div>
          
          <div className="text-sm text-gray-600 mb-2">
            {getServiceDescription(aiRouting.service_used)}
          </div>
          
          <div className="text-sm text-gray-700 bg-white p-2 rounded border">
            <span className="font-medium">AI Reasoning:</span> {aiRouting.reasoning}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ServiceExplanation;
