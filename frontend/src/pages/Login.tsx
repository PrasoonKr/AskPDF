import { Box, Typography, Paper, Button, Divider, Chip } from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import LockIcon from '@mui/icons-material/Lock';
import BoltIcon from '@mui/icons-material/Bolt';
import StorageIcon from '@mui/icons-material/Storage';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useLoginWithGoogleMutation, useDevLoginMutation } from '../api/apiSlice';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';

export default function Login() {
  const [loginWithGoogle] = useLoginWithGoogleMutation();
  const [devLogin, { isLoading: isDevLoading }] = useDevLoginMutation();
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse: any) => {
    try {
      const res = await loginWithGoogle({ credential: credentialResponse.credential }).unwrap();
      localStorage.setItem('token', res.token);
      localStorage.setItem('user', JSON.stringify(res.user));
      navigate('/');
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'Login failed',
        text: 'Could not authenticate with backend.',
        background: '#0f172a',
        color: '#f8fafc',
      });
    }
  };

  const handleDevLogin = async () => {
    try {
      const res = await devLogin().unwrap();
      localStorage.setItem('token', res.token);
      localStorage.setItem('user', JSON.stringify(res.user));
      navigate('/');
    } catch (err) {
      Swal.fire({
        icon: 'error',
        title: 'Dev Login Failed',
        text: 'Could not connect to backend server. Make sure the backend is running.',
        background: '#0f172a',
        color: '#f8fafc',
      });
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        px: 2,
      }}
    >
      {/* Ambient background orbs */}
      <Box
        sx={{
          position: 'absolute',
          top: '20%',
          left: '25%',
          width: '350px',
          height: '350px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.18) 0%, transparent 70%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: '20%',
          right: '25%',
          width: '350px',
          height: '350px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(236, 72, 153, 0.15) 0%, transparent 70%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />

      <Paper
        elevation={0}
        sx={{
          p: { xs: 3.5, sm: 5 },
          borderRadius: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          bgcolor: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.1)',
          maxWidth: 440,
          width: '100%',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* AskPDF Glowing Logo Badge */}
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '18px',
            background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 30px rgba(99, 102, 241, 0.45)',
            mb: 2,
          }}
        >
          <PictureAsPdfIcon sx={{ color: '#fff', fontSize: 34 }} />
        </Box>

        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            mb: 0.5,
            background: 'linear-gradient(135deg, #ffffff 40%, #a5b4fc 80%, #f472b6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '-0.02em',
          }}
        >
          AskPDF
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center', maxWidth: 320 }}>
          Local-first AI research assistant powered by two-stage hybrid search & re-ranking.
        </Typography>

        {/* Feature Badges */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center', mb: 3.5 }}>
          <Chip
            icon={<LockIcon sx={{ fontSize: '13px !important', color: '#10b981 !important' }} />}
            label="100% Private"
            size="small"
            sx={{ bgcolor: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', color: '#6ee7b7', fontSize: '0.72rem', fontWeight: 600 }}
          />
          <Chip
            icon={<BoltIcon sx={{ fontSize: '13px !important', color: '#818cf8 !important' }} />}
            label="FAISS + BM25"
            size="small"
            sx={{ bgcolor: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)', color: '#a5b4fc', fontSize: '0.72rem', fontWeight: 600 }}
          />
          <Chip
            icon={<StorageIcon sx={{ fontSize: '13px !important', color: '#f472b6 !important' }} />}
            label="Local Ollama"
            size="small"
            sx={{ bgcolor: 'rgba(236, 72, 153, 0.08)', border: '1px solid rgba(236, 72, 153, 0.2)', color: '#f472b6', fontSize: '0.72rem', fontWeight: 600 }}
          />
        </Box>

        {/* Primary Guest / Local Dev Login */}
        <Button
          variant="contained"
          fullWidth
          onClick={handleDevLogin}
          disabled={isDevLoading}
          endIcon={<ArrowForwardIcon />}
          sx={{
            py: 1.4,
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '0.95rem',
            boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)',
            transition: 'all 0.25s',
            '&:hover': {
              background: 'linear-gradient(135deg, #4f46e5 0%, #db2777 100%)',
              boxShadow: '0 8px 30px rgba(99, 102, 241, 0.6)',
              transform: 'translateY(-1px)',
            },
          }}
        >
          {isDevLoading ? 'Opening Session...' : 'Continue as Guest / Local Dev'}
        </Button>

        <Divider sx={{ my: 2.8, width: '100%', borderColor: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.4)', fontSize: '0.75rem', fontWeight: 600 }}>
          OR WITH GOOGLE
        </Divider>

        <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => {
              Swal.fire({ icon: 'error', title: 'Google Login Failed', background: '#0f172a', color: '#f8fafc' });
            }}
            theme="filled_black"
            shape="pill"
            text="signin_with"
          />
        </Box>
      </Paper>
    </Box>
  );
}
