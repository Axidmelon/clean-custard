import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card } from '@/components/ui/card';

interface DataSourceSelectorProps {
  value: 'auto' | 'database' | 'data_analysis_service' | 'csv_to_sql_converter';
  onChange: (value: 'auto' | 'database' | 'data_analysis_service' | 'csv_to_sql_converter') => void;
  hasFile: boolean;
  hasConnection: boolean;
  disabled?: boolean;
}

const DataSourceSelector: React.FC<DataSourceSelectorProps> = ({
  value,
  onChange,
  hasFile,
  hasConnection,
  disabled = false
}) => {
  const options = [
    {
      value: 'auto',
      label: '🤖 AI Auto-Select',
      description: 'Let AI choose the best service',
      disabled: !hasFile && !hasConnection
    },
    {
      value: 'data_analysis_service',
      label: '📊 Data Analysis Service',
      description: 'Advanced data analysis with pandas',
      disabled: !hasFile
    },
    {
      value: 'csv_to_sql_converter',
      label: '🗃️ CSV to SQL Converter',
      description: 'SQL queries on CSV data',
      disabled: !hasFile
    },
    {
      value: 'database',
      label: '🗄️ Database',
      description: 'Real-time database queries',
      disabled: !hasConnection
    }
  ];

  const availableOptions = options.filter(option => !option.disabled);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">
        Data Source
      </label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select data source" />
        </SelectTrigger>
        <SelectContent>
          {availableOptions.map(option => (
            <SelectItem key={option.value} value={option.value}>
              <div className="flex flex-col">
                <span className="font-medium">{option.label}</span>
                <span className="text-sm text-muted-foreground">{option.description}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {/* Show disabled options as unavailable */}
      {options.filter(option => option.disabled).length > 0 && (
        <Card className="p-3 bg-gray-50 border-gray-200">
          <div className="text-sm text-gray-600">
            <div className="font-medium mb-1">Unavailable options:</div>
            {options
              .filter(option => option.disabled)
              .map(option => (
                <div key={option.value} className="flex items-center gap-2 text-gray-500">
                  <span>{option.label}</span>
                  <span className="text-xs">
                    {option.value === 'auto' ? '(requires file or connection)' :
                     option.value === 'data_analysis_service' || option.value === 'csv_to_sql_converter' ? '(requires CSV file)' :
                     '(requires database connection)'}
                  </span>
                </div>
              ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default DataSourceSelector;
