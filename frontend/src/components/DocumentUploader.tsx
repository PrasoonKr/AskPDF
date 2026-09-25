import { useRef, useState } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import Swal from 'sweetalert2';
import { useUploadDocumentMutation } from '../api/apiSlice';

const Toast = Swal.mixin({
  toast: true,
  position: 'bottom-end',
  showConfirmButton: false,
  timer: 4500,
  timerProgressBar: true,
  background: '#0f172a',
  color: '#f8fafc',
  customClass: {
    popup: 'glass-panel'
  }
});

export default function DocumentUploader() {
  const [uploadDocument, { isLoading }] = useUploadDocumentMutation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const processFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const res = await uploadDocument(formData).unwrap();
      Toast.fire({
        icon: 'success',
        title: `Indexed ${res.chunks} chunks from ${res.documents} PDF document(s).`,
      });
    } catch (err: any) {
      Toast.fire({
        icon: 'error',
        title: err?.data?.detail || 'Document indexing failed',
      });
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <input
        type="file"
        multiple
        accept=".pdf"
        hidden
        ref={fileInputRef}
        onChange={handleFileChange}
      />
      <Box
        onClick={() => !isLoading && fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        sx={{
          border: isDragging ? '2px dashed #6366f1' : '1px dashed rgba(255, 255, 255, 0.15)',
          borderRadius: '14px',
          p: 2,
          textAlign: 'center',
          cursor: isLoading ? 'default' : 'pointer',
          bgcolor: isDragging ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1,
          '&:hover': {
            borderColor: '#6366f1',
            bgcolor: 'rgba(99, 102, 241, 0.05)',
            transform: 'translateY(-1px)',
          },
        }}
      >
        {isLoading ? (
          <Box sx={{ py: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.2 }}>
            <CircularProgress size={28} sx={{ color: '#ec4899' }} />
            <Typography variant="caption" sx={{ color: '#a5b4fc', fontWeight: 600 }}>
              Parsing & Embedding Chunks...
            </Typography>
          </Box>
        ) : (
          <>
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: '10px',
                bgcolor: 'rgba(99, 102, 241, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#818cf8',
              }}
            >
              <CloudUploadIcon fontSize="small" />
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.85rem' }}>
                Upload PDF Documents
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.72rem' }}>
                Drag & drop or click to browse
              </Typography>
            </Box>
          </>
        )}
      </Box>
    </Box>
  );
}
