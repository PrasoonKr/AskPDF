import { Box, CircularProgress, Typography, Button, IconButton, Tooltip } from '@mui/material';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DeleteIcon from '@mui/icons-material/Delete';
import LayersClearIcon from '@mui/icons-material/LayersClear';
import Swal from 'sweetalert2';
import { useGetDocumentsQuery, useClearDocumentsMutation, useDeleteDocumentMutation } from '../api/apiSlice';

const Toast = Swal.mixin({
  toast: true,
  position: 'bottom-end',
  showConfirmButton: false,
  timer: 3500,
  timerProgressBar: true,
  background: '#0f172a',
  color: '#f8fafc',
  customClass: {
    popup: 'glass-panel',
  },
});

export default function DocumentList() {
  const { data: docsData, isLoading: isLoadingDocs } = useGetDocumentsQuery();
  const [clearDocuments, { isLoading: isClearing }] = useClearDocumentsMutation();
  const [deleteDocument, { isLoading: isDeleting }] = useDeleteDocumentMutation();

  const handleClear = () => {
    Swal.fire({
      title: 'Clear Knowledge Base?',
      text: 'This will remove all indexed PDFs and reset your FAISS vector index.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6366f1',
      confirmButtonText: 'Yes, clear all',
      background: '#0f172a',
      color: '#f8fafc',
      customClass: {
        container: 'swal2-container',
      },
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await clearDocuments().unwrap();
          Toast.fire({ icon: 'success', title: 'Knowledge base cleared.' });
        } catch (err) {
          Toast.fire({ icon: 'error', title: 'Failed to clear knowledge base.' });
        }
      }
    });
  };

  const handleDelete = (filename: string) => {
    Swal.fire({
      title: 'Delete Document?',
      text: `Remove "${filename}" and its vector embeddings?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#6366f1',
      confirmButtonText: 'Delete',
      background: '#0f172a',
      color: '#f8fafc',
      customClass: {
        container: 'swal2-container',
      },
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await deleteDocument(filename).unwrap();
          Toast.fire({ icon: 'success', title: `Removed ${filename}` });
        } catch (err) {
          Toast.fire({ icon: 'error', title: 'Failed to remove document.' });
        }
      }
    });
  };

  if (isLoadingDocs) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
        <CircularProgress size={24} sx={{ color: '#6366f1' }} />
      </Box>
    );
  }

  const documents = docsData?.documents || [];

  return (
    <Box sx={{ width: '100%' }}>
      {documents.length > 0 ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {documents.map((doc, idx) => (
            <Box
              key={idx}
              sx={{
                p: 1.2,
                borderRadius: '12px',
                bgcolor: 'rgba(255, 255, 255, 0.025)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 1,
                transition: 'all 0.2s',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.045)',
                  borderColor: 'rgba(99, 102, 241, 0.25)',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, minWidth: 0 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '8px',
                    bgcolor: 'rgba(236, 72, 153, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <PictureAsPdfIcon sx={{ fontSize: 18, color: '#f472b6' }} />
                </Box>
                <Tooltip title={doc}>
                  <Typography
                    variant="caption"
                    noWrap
                    sx={{
                      fontWeight: 600,
                      color: '#e2e8f0',
                      fontSize: '0.78rem',
                      maxWidth: '170px',
                    }}
                  >
                    {doc}
                  </Typography>
                </Tooltip>
              </Box>

              <IconButton
                size="small"
                onClick={() => handleDelete(doc)}
                disabled={isDeleting}
                sx={{
                  color: 'rgba(255,255,255,0.4)',
                  p: 0.5,
                  '&:hover': {
                    color: '#ef4444',
                    bgcolor: 'rgba(239, 68, 68, 0.12)',
                  },
                }}
              >
                <DeleteIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Box>
          ))}

          <Button
            variant="text"
            fullWidth
            onClick={handleClear}
            disabled={isClearing}
            startIcon={<LayersClearIcon sx={{ fontSize: 16 }} />}
            sx={{
              mt: 1.5,
              color: 'rgba(239, 68, 68, 0.8)',
              fontSize: '0.75rem',
              py: 0.8,
              borderRadius: '10px',
              border: '1px solid rgba(239, 68, 68, 0.15)',
              '&:hover': {
                bgcolor: 'rgba(239, 68, 68, 0.08)',
                borderColor: 'rgba(239, 68, 68, 0.3)',
              },
            }}
          >
            {isClearing ? 'Clearing Index...' : 'Clear All Documents'}
          </Button>
        </Box>
      ) : (
        <Box sx={{ py: 3, textAlign: 'center' }}>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>
            No documents uploaded yet.
          </Typography>
        </Box>
      )}
    </Box>
  );
}
