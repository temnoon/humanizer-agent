import { render } from '@testing-library/react';
import { WorkspaceProvider } from '../contexts/WorkspaceContext';

/**
 * Custom render function that wraps components with necessary providers
 * @param {React.ReactElement} ui - Component to render
 * @param {Object} options - Render options
 * @param {Object} options.workspaceValue - Initial workspace context value
 * @returns {Object} Render result from @testing-library/react
 */
export function renderWithWorkspace(ui, { workspaceValue, ...renderOptions } = {}) {
  function Wrapper({ children }) {
    return <WorkspaceProvider>{children}</WorkspaceProvider>;
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

/**
 * Create mock localStorage for testing
 */
export function createMockLocalStorage() {
  let store = {};

  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => {
      store[key] = value.toString();
    },
    removeItem: (key) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    },
  };
}

/**
 * Wait for async updates to complete
 */
export const waitForAsync = () => new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Mock axios responses for testing
 */
export function createMockAxios() {
  return {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    patch: vi.fn(() => Promise.resolve({ data: {} })),
  };
}

/**
 * Sample data generators for tests
 */
export const mockData = {
  book: (overrides = {}) => ({
    id: 1,
    title: 'Test Book',
    description: 'A test book',
    created_at: '2025-10-06T00:00:00Z',
    updated_at: '2025-10-06T00:00:00Z',
    user_id: 1,
    ...overrides,
  }),

  section: (overrides = {}) => ({
    id: 1,
    book_id: 1,
    title: 'Test Section',
    content: '# Test Content',
    order_index: 0,
    parent_section_id: null,
    ...overrides,
  }),

  conversation: (overrides = {}) => ({
    id: 1,
    title: 'Test Conversation',
    source: 'chatgpt',
    created_at: '2025-10-06T00:00:00Z',
    message_count: 10,
    ...overrides,
  }),

  message: (overrides = {}) => ({
    id: 1,
    conversation_id: 1,
    role: 'user',
    content: 'Test message',
    created_at: '2025-10-06T00:00:00Z',
    ...overrides,
  }),

  image: (overrides = {}) => ({
    id: 1,
    conversation_id: 1,
    message_id: 1,
    filename: 'test.png',
    file_path: '/path/to/test.png',
    created_at: '2025-10-06T00:00:00Z',
    ...overrides,
  }),
};
