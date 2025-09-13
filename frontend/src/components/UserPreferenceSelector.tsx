import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Info } from 'lucide-react';

interface UserPreferenceSelectorProps {
  value?: 'sql' | 'python';
  onChange: (value: 'sql' | 'python' | undefined) => void;
  disabled?: boolean;
}

const UserPreferenceSelector: React.FC<UserPreferenceSelectorProps> = ({
  value,
  onChange,
  disabled = false
}) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">
          Preference (Optional)
        </label>
        <Info className="h-4 w-4 text-gray-400" />
      </div>
      
      <Card className="p-3 bg-blue-50 border-blue-200">
        <CardContent className="p-0">
          <div className="text-xs text-blue-700 mb-2">
            Help AI choose the best service for your query style
          </div>
          <div className="flex gap-2">
            <Button
              variant={value === 'sql' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onChange(value === 'sql' ? undefined : 'sql')}
              disabled={disabled}
              className="flex-1"
            >
              <span className="mr-1">🗃️</span>
              SQL
            </Button>
            <Button
              variant={value === 'python' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onChange(value === 'python' ? undefined : 'python')}
              disabled={disabled}
              className="flex-1"
            >
              <span className="mr-1">📊</span>
              Python
            </Button>
          </div>
          <div className="text-xs text-gray-600 mt-2">
            {value === 'sql' && 'AI will prefer SQL-based analysis (csv_to_sql_converter)'}
            {value === 'python' && 'AI will prefer Python-based analysis (data_analysis_service)'}
            {!value && 'AI will choose based on query complexity and data size'}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserPreferenceSelector;
