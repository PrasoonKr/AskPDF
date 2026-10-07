import { useState } from 'react';
import { Box, Drawer, Typography, Divider, Avatar, IconButton, Button, useTheme, useMediaQuery, Badge } from '@mui/material';
import { Outlet, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { apiSlice, useGetDocumentsQuery } from '../api/apiSlice';
import DocumentUploader from './DocumentUploader';
import DocumentList from './DocumentList';
import AddIcon from '@mui/icons-material/Add';
import LogoutIcon from '@mui/icons-material/Logout';
import FolderIcon from '@mui/icons-material/Folder';
import MenuIcon from '@mui/icons-material/Menu';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';

const drawerWidth = 290;

export default function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [isLeftDrawerOpen, setIsLeftDrawerOpen] = useState(false);
  const [isRightDrawerOpen, setIsRightDrawerOpen] = useState(false);
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { data: docsData } = useGetDocumentsQuery();
  const docCount = docsData?.documents?.length || 0;

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    dispatch(apiSlice.util.resetApiState());
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'transparent' }}>
      {/* Left Sidebar */}
      <Drawer
        sx={{
          width: isMobile ? 0 : drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            backgroundColor: 'rgba(10, 14, 26, 0.85)',
            backdropFilter: 'blur(20px)',
            borderRight: '1px solid rgba(255, 255, 255, 0.07)',
          },
        }}
        variant={isMobile ? "temporary" : "permanent"}
        open={isMobile ? isLeftDrawerOpen : true}
        onClose={() => setIsLeftDrawerOpen(false)}
        anchor="left"
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Logo & Header */}
          <Box sx={{ p: 2.5, pb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
              <Box
                sx={{
                  width: 42,
                  height: 42,
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4)',
                }}
              >
                <PictureAsPdfIcon sx={{ color: '#fff', fontSize: 24 }} />
              </Box>
              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 800,
                    background: 'linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    lineHeight: 1.2,
                  }}
                >
                  AskPDF
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.45)', fontWeight: 500, fontSize: '0.72rem' }}>
                  Get Your Answers Instantly
                </Typography>
              </Box>
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)' }} />

          {/* Action Buttons */}
          <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Button
              fullWidth
              variant="contained"
              onClick={() => window.dispatchEvent(new Event('new-chat'))}
              startIcon={<AddIcon />}
              sx={{
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#fff',
                py: 1.1,
                borderRadius: '12px',
                boxShadow: '0 4px 14px rgba(99, 102, 241, 0.35)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                  boxShadow: '0 6px 20px rgba(99, 102, 241, 0.5)',
                  transform: 'translateY(-1px)',
                }
              }}
            >
              New Chat
            </Button>

            <DocumentUploader />
          </Box>

          {/* Quick Knowledge Base Preview */}
          <Box sx={{ px: 2.5, py: 1.5, flexGrow: 1, overflowY: 'auto' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: 0.8, textTransform: 'uppercase', fontSize: '0.7rem' }}>
                Active Documents ({docCount})
              </Typography>
            </Box>
            <DocumentList />
          </Box>

          {/* User Profile / Footer */}
          <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,0.06)', mt: 'auto', bgcolor: 'rgba(0,0,0,0.15)' }}>
            {user && (
              <Box sx={{ p: 1.2, display: 'flex', alignItems: 'center', gap: 1.2, mb: 1.5, bgcolor: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <Avatar
                  src={user.picture || undefined}
                  sx={{ width: 34, height: 34, bgcolor: 'primary.main', fontSize: '0.9rem', fontWeight: 700 }}
                  slotProps={{ img: { referrerPolicy: "no-referrer" as const } }}
                >
                  {!user.picture && user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </Avatar>
                <Box sx={{ overflow: 'hidden', flexGrow: 1 }}>
                  <Typography variant="body2" noWrap sx={{ fontWeight: 600, color: 'text.primary', fontSize: '0.825rem' }}>
                    {user.name}
                  </Typography>
                  <Typography variant="caption" noWrap color="text.secondary" sx={{ display: 'block', fontSize: '0.72rem' }}>
                    {user.email}
                  </Typography>
                </Box>
                <IconButton onClick={handleLogout} size="small" sx={{ color: 'text.secondary', '&:hover': { color: '#ef4444', bgcolor: 'rgba(239, 68, 68, 0.12)' } }}>
                  <LogoutIcon fontSize="small" />
                </IconButton>
              </Box>
            )}
          </Box>
        </Box>
      </Drawer>

      {/* Main Content Area */}
      <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', position: 'relative' }}>
        {/* Top Header Bar */}
        <Box
          sx={{
            px: { xs: 2, sm: 3 },
            py: 1.5,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            bgcolor: 'rgba(10, 14, 26, 0.5)',
            backdropFilter: 'blur(16px)',
            minHeight: '60px',
            zIndex: 10,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            {isMobile && (
              <IconButton onClick={() => setIsLeftDrawerOpen(true)} sx={{ color: 'text.secondary' }}>
                <MenuIcon />
              </IconButton>
            )}
          </Box>

          <Button
            variant="outlined"
            onClick={() => setIsRightDrawerOpen(true)}
            startIcon={
              <Badge badgeContent={docCount} color="primary" sx={{ '& .MuiBadge-badge': { fontSize: '0.65rem', height: 16, minWidth: 16 } }}>
                <FolderIcon fontSize="small" />
              </Badge>
            }
            sx={{
              color: '#e2e8f0',
              borderColor: 'rgba(255,255,255,0.12)',
              bgcolor: 'rgba(255,255,255,0.02)',
              borderRadius: '10px',
              fontSize: '0.8rem',
              py: 0.6,
              '&:hover': {
                bgcolor: 'rgba(99, 102, 241, 0.1)',
                borderColor: '#6366f1',
              }
            }}
          >
            Library ({docCount})
          </Button>
        </Box>

        {/* Chat Interface Outlet */}
        <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
          <Outlet />
        </Box>
      </Box>

      {/* Right Drawer: Knowledge Base Details */}
      <Drawer
        anchor="right"
        open={isRightDrawerOpen}
        onClose={() => setIsRightDrawerOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', sm: 380 },
            boxSizing: 'border-box',
            backgroundColor: 'rgba(10, 14, 26, 0.95)',
            backdropFilter: 'blur(20px)',
            borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
            p: 3,
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#f8fafc' }}>
            Document Library
          </Typography>
          <Box sx={{ px: 1, py: 0.3, borderRadius: 1, bgcolor: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontSize: '0.75rem', fontWeight: 600 }}>
            {docCount} Files
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5, fontSize: '0.825rem' }}>
          All uploaded files are parsed, chunked, and embedded into your isolated FAISS index.
        </Typography>
        <DocumentUploader />
        <Box sx={{ mt: 3 }}>
          <DocumentList />
        </Box>
      </Drawer>
    </Box>
  );
}

