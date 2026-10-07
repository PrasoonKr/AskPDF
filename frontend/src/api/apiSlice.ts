import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query/react';

const baseQuery = fetchBaseQuery({ 
  baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  prepareHeaders: (headers) => {
    const token = localStorage.getItem('token');
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (args, api, extraOptions) => {
  let result = await baseQuery(args, api, extraOptions);
  
  if (result.error && result.error.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }
  
  return result;
};

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Documents', 'Sessions'],
  endpoints: (builder) => ({
    createSession: builder.mutation<{ session_id: string }, void>({
      query: () => ({
        url: '/sessions',
        method: 'POST',
      }),
      invalidatesTags: ['Sessions'],
    }),
    listSessions: builder.query<{ sessions: { id: string; title: string; created_at: string; updated_at: string }[] }, void>({
      query: () => '/sessions',
      providesTags: ['Sessions'],
    }),
    getSessionMessages: builder.query<{ messages: { id: string; role: string; content: string; sources?: any[]; trace?: any; created_at: string }[] }, string>({
      query: (sessionId) => `/sessions/${sessionId}/messages`,
    }),
    renameSession: builder.mutation<any, { sessionId: string; title: string }>({
      query: ({ sessionId, title }) => ({
        url: `/sessions/${sessionId}`,
        method: 'PATCH',
        body: { title },
      }),
      invalidatesTags: ['Sessions'],
    }),
    deleteSession: builder.mutation<any, string>({
      query: (sessionId) => ({
        url: `/sessions/${sessionId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Sessions'],
    }),
    askQuestion: builder.mutation<{ answer: string, sources: any[], trace?: string }, { session_id: string, question: string }>({
      query: (body) => ({
        url: '/chat',
        method: 'POST',
        body,
      }),
    }),
    getDocuments: builder.query<{ documents: string[] }, void>({
      query: () => '/documents',
      providesTags: ['Documents'],
    }),
    uploadDocument: builder.mutation<{ documents: number, chunks: number }, FormData>({
      query: (formData) => ({
        url: '/documents',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: ['Documents'],
    }),
    loginWithGoogle: builder.mutation<{ token: string; user: any }, { credential: string }>({
      query: (body) => ({
        url: '/auth/google',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Documents'],
    }),
    devLogin: builder.mutation<{ token: string; user: any }, void>({
      query: () => ({
        url: '/auth/dev-login',
        method: 'POST',
      }),
      invalidatesTags: ['Documents'],
    }),
    clearDocuments: builder.mutation<void, void>({
      query: () => ({
        url: '/documents',
        method: 'DELETE',
      }),
      invalidatesTags: ['Documents'],
    }),
    deleteDocument: builder.mutation<void, string>({
      query: (filename) => ({
        url: `/documents/${filename}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Documents'],
    }),
  }),
});

export const {
  useCreateSessionMutation,
  useListSessionsQuery,
  useGetSessionMessagesQuery,
  useLazyGetSessionMessagesQuery,
  useRenameSessionMutation,
  useDeleteSessionMutation,
  useAskQuestionMutation,
  useGetDocumentsQuery,
  useUploadDocumentMutation,
  useClearDocumentsMutation,
  useDeleteDocumentMutation,
  useLoginWithGoogleMutation,
  useDevLoginMutation,
} = apiSlice;

