import { useState, useRef } from "react";
import { Upload, FileText, X, CheckCircle, Clock, AlertCircle, HardDrive, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { useFileUpload } from "@/contexts/FileUploadContext";


export default function Uploads() {
  // Use shared file upload context
  const { uploadedFiles, isLoading, addUploadedFile, removeUploadedFile } = useFileUpload();
  
  // State for delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<string | null>(null);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setSelectedFiles(prev => [...prev, ...files]);
    // Don't add to shared context yet - wait for submit
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    setSelectedFiles(prev => [...prev, ...files]);
    // Don't add to shared context yet - wait for submit
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const removeSelectedFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearSelectedFiles = () => {
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };


  const submitFiles = async () => {
    // Now add files to shared context and start upload
    try {
      await Promise.all(selectedFiles.map(file => addUploadedFile(file)));
      clearSelectedFiles();
    } catch (error) {
      console.error('Some files failed to upload:', error);
      // Clear selected files even if some uploads failed
      clearSelectedFiles();
    }
  };

  const handleDeleteClick = (fileId: string) => {
    setFileToDelete(fileId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (fileToDelete) {
      try {
        await removeUploadedFile(fileToDelete);
        setFileToDelete(null);
      } catch (error) {
        console.error('Failed to delete file:', error);
        // Still close dialog even if deletion fails
      }
    }
    setDeleteDialogOpen(false);
  };

  const cancelDelete = () => {
    setFileToDelete(null);
    setDeleteDialogOpen(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'progress':
        return <Clock className="w-4 h-4 text-orange-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'progress':
        return 'Progress';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Upload Data</h1>
        <p className="text-muted-foreground mt-1">
          Upload and manage your data files
        </p>
      </div>

      {/* Upload Area */}
      <Card className="p-6">
        <div className="flex gap-6">
          {/* Drag & Drop Area */}
          <div className="flex-1">
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragOver 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                  <Upload className="w-6 h-6 text-muted-foreground" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">
                    Drag & Drop your file(s) here or Browse Files
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={triggerFileUpload}
                  className="mt-2"
                >
                  Browse Files
                </Button>
              </div>
            </div>
          </div>

          {/* Selected Files Preview */}
          <div className="w-80 space-y-3">
            <h3 className="text-sm font-medium text-foreground">Selected Files</h3>
            {selectedFiles.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No files selected</p>
              </div>
            ) : (
              <div className="space-y-2">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeSelectedFile(index)}
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
                <Button 
                  onClick={submitFiles}
                  className="w-full bg-primary hover:bg-primary-hover"
                  disabled={selectedFiles.length === 0}
                >
                  Submit
                </Button>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Uploaded Files Table */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Uploaded Files</h2>
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading uploaded files...</p>
              </div>
            </div>
          ) : uploadedFiles.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No files uploaded yet</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">FILE NAME</th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">FILE SIZE</th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">STATUS</th>
                  <th className="text-center py-3 px-4 font-medium text-muted-foreground">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {uploadedFiles.map((file) => (
                  <tr key={file.id} className="border-b border-border hover:bg-muted/20">
                    <td className="py-3 px-4 text-sm font-medium">{file.name}</td>
                    <td className="py-3 px-4 text-sm">
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-muted-foreground" />
                        {formatFileSize(file.size)}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(file.status)}
                        <span className={file.status === 'completed' ? 'text-green-600' : 
                                       file.status === 'progress' ? 'text-orange-600' : 
                                       'text-red-600'}>
                          {getStatusText(file.status)}
                        </span>
                        {file.status === 'progress' && file.progress !== undefined && (
                          <div className="w-20">
                            <Progress value={file.progress} className="h-2" />
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteClick(file.id)}
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-full"
                        title="Delete file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-red-500" />
              Delete File
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this file? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <p className="text-sm text-muted-foreground">
              The file will be permanently removed from your uploads.
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={cancelDelete}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={confirmDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete File
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
