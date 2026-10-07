import { useState, useEffect, useRef } from 'react';
import {
  Box,
  IconButton,
  Paper,
  Typography,
  Chip,
  InputBase,
  Tooltip,
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import DescriptionIcon from '@mui/icons-material/Description';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';

import { useCreateSessionMutation, useLazyGetSessionMessagesQuery } from '../api/apiSlice';

interface Message {
  id: number;
  type: 'user' | 'assistant';
  content: string;
  sources?: any[];
  trace?: string;
}



export default function ChatInterface() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [isFocused, setIsFocused] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const [createSession] = useCreateSessionMutation();
  const isLoading = isStreaming;
  const messagesEndRef = useRef<HTMLDivElement>(null);



  useEffect(() => {
    const handleNewChat = async () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      setMessages([]);
      setInput('');
      setSessionId(null);
    };
    window.addEventListener('new-chat', handleNewChat);
    return () => window.removeEventListener('new-chat', handleNewChat);
  }, []);

  // Load a past session from the sidebar
  const [fetchMessages] = useLazyGetSessionMessagesQuery();
  useEffect(() => {
    const handleLoadSession = async (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (!detail?.sessionId) return;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      setSessionId(detail.sessionId);
      setInput('');
      setIsStreaming(false);
      try {
        const res = await fetchMessages(detail.sessionId).unwrap();
        const loadedMessages: Message[] = (res.messages || []).map((m: any, i: number) => ({
          id: Date.now() + i,
          type: m.role as 'user' | 'assistant',
          content: m.content,
          sources: m.sources || undefined,
          trace: m.trace || undefined,
        }));
        setMessages(loadedMessages);
      } catch (err) {
        console.error('Failed to load session messages', err);
        setMessages([]);
      }
    };
    window.addEventListener('load-session', handleLoadSession);
    return () => window.removeEventListener('load-session', handleLoadSession);
  }, [fetchMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendQuery = async (queryText: string) => {
    const trimmed = queryText.trim();
    if (!trimmed || isLoading) return;

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      try {
        const res = await createSession().unwrap();
        currentSessionId = res.session_id;
        setSessionId(currentSessionId);
      } catch (err) {
        console.error('Failed to create session', err);
        return;
      }
    }

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: trimmed,
    };

    const assistantMsgId = Date.now() + 1;
    const initialAssistantMsg: Message = {
      id: assistantMsgId,
      type: 'assistant',
      content: '',
      sources: [],
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMsg]);
    setInput('');
    setIsStreaming(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const token = localStorage.getItem('token');
      const apiBase = import.meta.env.VITE_API_BASE_URL || '/api';
      const response = await fetch(`${apiBase}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          question: trimmed,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        let errMessage = `Server error ${response.status}`;
        try {
          const errData = await response.json();
          errMessage = errData.detail || errMessage;
        } catch (_) {}
        throw new Error(errMessage);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          if (!block.trim()) continue;
          const blockLines = block.split('\n');
          let eventType = '';
          let dataStr = '';

          for (const line of blockLines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.slice(6).trim();
            }
          }

          if (!dataStr) continue;

          try {
            const parsed = JSON.parse(dataStr);
            if (eventType === 'sources' && Array.isArray(parsed)) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, sources: parsed } : msg
                )
              );
            } else if (eventType === 'token' && parsed.token) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: msg.content + parsed.token }
                    : msg
                )
              );
            } else if (eventType === 'done' && parsed.answer) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, content: parsed.answer } : msg
                )
              );
            } else if (eventType === 'error') {
              const errMsg = parsed.error || 'An error occurred during response generation.';
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, content: `⚠️ ${errMsg}` } : msg
                )
              );
              break;
            }
          } catch (e: any) {
            if (e.message && e.message !== 'Unexpected end of JSON input') {
              console.warn('SSE Parse error:', e);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, content: msg.content ? msg.content + '\n\n_Generation stopped by user._' : '_Generation stopped by user._' }
              : msg
          )
        );
      } else {
        console.error(err);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: `⚠️ Error generating response: ${err.message || 'Please ensure Ollama is running.'}`,
                }
              : msg
          )
        );
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleCopy = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };


  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '980px', width: '100%', mx: 'auto', px: { xs: 2, sm: 3 } }}>
      {/* Message Feed */}
      <Box
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          py: 3,
          display: 'flex',
          flexDirection: 'column',
          gap: 3,
          '&::-webkit-scrollbar': { width: '6px' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '6px' },
        }}
      >
        {messages.length === 0 && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '70vh',
              textAlign: 'center',
              px: 2,
            }}
          >
            {/* Glowing Brand Hero */}
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '20px',
                background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 2.5,
                boxShadow: '0 8px 32px rgba(99, 102, 241, 0.45)',
                animation: 'pulse-glow 6s infinite ease-in-out',
              }}
            >
              <AutoAwesomeIcon sx={{ color: '#fff', fontSize: 32 }} />
            </Box>

            <Typography
              variant="h4"
              sx={{
                fontWeight: 800,
                background: 'linear-gradient(135deg, #ffffff 30%, #a5b4fc 70%, #f472b6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
              }}
            >
              What would you like to explore?
            </Typography>

            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 540, mb: 4.5, fontSize: '0.95rem' }}>
              Upload any PDF document to research with grounded citations, hybrid search, and cross-encoder re-ranking.
            </Typography>


          </Box>
        )}

        {messages.map((msg) => (
          <Box
            key={msg.id}
            sx={{
              alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: msg.type === 'user' ? { xs: '90%', sm: '80%' } : '100%',
              width: msg.type === 'user' ? 'auto' : '100%',
            }}
          >
            {msg.type === 'user' ? (
              /* User Bubble */
              <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1.5 }}>
                <Paper
                  sx={{
                    p: '14px 20px',
                    background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                    color: '#ffffff',
                    borderRadius: '20px 20px 4px 20px',
                    boxShadow: '0 4px 16px rgba(79, 70, 229, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontWeight: 500 }}>
                    {msg.content}
                  </Typography>
                </Paper>
              </Box>
            ) : (
              /* Assistant Bubble */
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2.5, sm: 3 },
                  pr: { xs: 6, sm: 7 },
                  bgcolor: 'rgba(15, 23, 42, 0.55)',
                  backdropFilter: 'blur(16px)',
                  borderRadius: '20px',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* Copy Button */}
                <Box sx={{ position: 'absolute', top: 12, right: 12, zIndex: 2 }}>
                  <Tooltip title={copiedId === msg.id ? 'Copied!' : 'Copy response'}>
                    <IconButton
                      size="small"
                      onClick={() => handleCopy(msg.content, msg.id)}
                      sx={{
                        color: 'text.secondary',
                        bgcolor: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        borderRadius: '8px',
                        p: 0.8,
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          color: '#f8fafc',
                          bgcolor: 'rgba(255, 255, 255, 0.1)',
                          borderColor: 'rgba(255, 255, 255, 0.15)',
                        },
                      }}
                    >
                      {copiedId === msg.id ? (
                        <CheckIcon sx={{ fontSize: 16, color: '#10b981' }} />
                      ) : (
                        <ContentCopyIcon sx={{ fontSize: 16 }} />
                      )}
                    </IconButton>
                  </Tooltip>
                </Box>

                {/* Markdown Formatted Answer or Typing Indicator */}
                {!msg.content ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1.5 }}>
                    <span className="dot-typing"></span>
                    <Typography variant="body2" sx={{ color: 'text.secondary', ml: 2.5, fontSize: '0.85rem' }}>
                      Retrieving context & streaming answer...
                    </Typography>
                  </Box>
                ) : (
                  <Box
                    sx={{
                      color: '#e2e8f0',
                      fontSize: '0.95rem',
                      '& p': { m: 0, mb: 1.8, lineHeight: 1.7 },
                      '& p:last-child': { mb: 0 },
                      '& strong': { color: '#ffffff', fontWeight: 700 },
                      '& a': { color: '#818cf8', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } },
                      '& code': { bgcolor: 'rgba(0, 0, 0, 0.35)', px: 1, py: 0.3, borderRadius: '6px', fontFamily: '"JetBrains Mono", monospace', fontSize: '0.85em', color: '#f472b6' },
                      '& pre': { bgcolor: '#070a13', p: 2, borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)', overflowX: 'auto', my: 2, '& code': { bgcolor: 'transparent', p: 0, color: '#e2e8f0' } },
                      '& ul, & ol': { m: 0, mb: 1.8, pl: 3 },
                      '& li': { mb: 0.8 },
                      '& h1, & h2, & h3, & h4': { mt: 2.5, mb: 1.2, fontWeight: 700, color: '#ffffff' },
                      wordBreak: 'break-word',
                    }}
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </Box>
                )}

                {/* Grounded Citation Chips */}
                {msg.sources && msg.sources.length > 0 && (
                  <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', fontWeight: 700, mb: 1.2, letterSpacing: 0.5, textTransform: 'uppercase', fontSize: '0.7rem' }}>
                      Attributed Sources ({msg.sources.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {msg.sources.map((src, i) => {
                        const pct = Math.round(src.score * 100);
                        return (
                          <Chip
                            key={i}
                            icon={<DescriptionIcon sx={{ fontSize: '14px !important', color: '#f472b6 !important' }} />}
                            label={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8 }}>
                                <span>{src.source} (Page {src.page})</span>
                                {src.score !== undefined && (
                                  <Box component="span" sx={{ px: 0.6, py: 0.1, borderRadius: '4px', bgcolor: 'rgba(236, 72, 153, 0.18)', color: '#f472b6', fontSize: '0.65rem', fontWeight: 700 }}>
                                    {pct}% match
                                  </Box>
                                )}
                              </Box>
                            }
                            size="small"
                            sx={{
                              fontSize: '0.75rem',
                              bgcolor: 'rgba(255, 255, 255, 0.03)',
                              border: '1px solid rgba(236, 72, 153, 0.25)',
                              color: '#f8fafc',
                              py: 1.8,
                              '&:hover': { bgcolor: 'rgba(236, 72, 153, 0.08)' },
                            }}
                          />
                        );
                      })}
                    </Box>
                  </Box>
                )}
              </Paper>
            )}
          </Box>
        ))}

        <div ref={messagesEndRef} />
      </Box>

      {/* Floating Input Capsule */}
      <Box sx={{ py: 2.5, bgcolor: 'transparent', mt: 'auto' }}>
        <Paper
          elevation={0}
          sx={{
            display: 'flex',
            alignItems: 'center',
            p: '8px 12px 8px 20px',
            borderRadius: '20px',
            border: isFocused ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.1)',
            bgcolor: 'rgba(15, 23, 42, 0.75)',
            backdropFilter: 'blur(20px)',
            boxShadow: isFocused ? '0 0 24px rgba(99, 102, 241, 0.3)' : '0 8px 32px rgba(0, 0, 0, 0.25)',
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <InputBase
            fullWidth
            placeholder="Ask a question about your uploaded documents..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendQuery(input);
              }
            }}
            multiline
            maxRows={4}
            sx={{
              flex: 1,
              color: '#f8fafc',
              fontSize: '0.95rem',
              '& input::placeholder': { color: 'text.secondary', opacity: 0.8 },
            }}
            disabled={isLoading}
          />

          {isLoading ? (
            <IconButton
              onClick={() => abortControllerRef.current?.abort()}
              sx={{
                width: 40,
                height: 40,
                color: '#ef4444',
                bgcolor: 'rgba(239, 68, 68, 0.12)',
                '&:hover': { bgcolor: 'rgba(239, 68, 68, 0.2)' },
              }}
            >
              <StopCircleIcon />
            </IconButton>

          ) : (
            <IconButton
              onClick={() => handleSendQuery(input)}
              disabled={!input.trim()}
              sx={{
                width: 40,
                height: 40,
                background: input.trim() ? 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)' : 'rgba(255,255,255,0.05)',
                color: input.trim() ? '#ffffff' : 'rgba(255,255,255,0.3)',
                boxShadow: input.trim() ? '0 4px 14px rgba(99, 102, 241, 0.4)' : 'none',
                transition: 'all 0.2s',
                '&:hover': {
                  background: input.trim() ? 'linear-gradient(135deg, #4f46e5 0%, #db2777 100%)' : 'rgba(255,255,255,0.05)',
                  transform: input.trim() ? 'scale(1.05)' : 'none',
                },
              }}
            >
              <ArrowUpwardIcon fontSize="small" />
            </IconButton>
          )}
        </Paper>
        <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mt: 1, color: 'rgba(255, 255, 255, 0.35)', fontSize: '0.72rem' }}>
          AskPDF grounds answers in your documents • Press <strong style={{ color: '#94a3b8' }}>Enter ↵</strong> to send, <strong style={{ color: '#94a3b8' }}>Shift + Enter</strong> for a new line
        </Typography>
      </Box>
    </Box>
  );
}
