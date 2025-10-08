# Testing Guide - Humanizer Agent Frontend

## Overview

The Humanizer Agent frontend uses a comprehensive testing strategy with three layers:

1. **Unit Tests** - Testing individual components and contexts in isolation
2. **Integration Tests** - Testing component interactions and workflows
3. **E2E Tests** - Testing complete user journeys in a browser

## Test Framework Stack

- **Vitest** - Fast unit/integration test runner (optimized for Vite)
- **React Testing Library** - Component testing utilities
- **Playwright** - End-to-end browser testing
- **jsdom** - DOM simulation for unit tests

## Running Tests

### Unit & Integration Tests

```bash
# Run all unit/integration tests
npm test

# Run tests in watch mode (during development)
npm run test

# Run with UI (visual test runner)
npm run test:ui

# Run with coverage report
npm run test:coverage
```

### E2E Tests

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI (visual test runner)
npm run test:e2e:ui
```

## Test Organization

```
frontend/
├── src/
│   ├── __tests__/
│   │   ├── contexts/          # Context/state management tests
│   │   │   └── WorkspaceContext.test.jsx
│   │   ├── layout/            # Layout component tests
│   │   │   ├── LayoutManager.test.jsx
│   │   │   └── InterestList.test.jsx
│   │   └── integration/       # Integration tests
│   │       ├── book-builder.test.jsx
│   │       └── navigation-interest.test.jsx
│   └── test/
│       ├── setup.js           # Global test setup
│       └── utils.jsx          # Test utilities and helpers
├── e2e/
│   ├── user-journeys.spec.js  # User flow E2E tests
│   └── pane-persistence.spec.js # Persistence E2E tests
├── vitest.config.js           # Vitest configuration
└── playwright.config.js       # Playwright configuration
```

## Test Coverage Summary

### Unit Tests (60 tests)

**WorkspaceContext** (23 tests)
- Provider initialization and error handling
- Tab management (add, close, switch, navigate)
- Interest list management
- Preferences persistence
- Complex workflows

**LayoutManager** (21 tests)
- Initialization and localStorage handling
- Pane visibility control
- Complex layout configurations
- Resize handle rendering
- Content rendering

**InterestList** (16 tests)
- Empty state handling
- Item rendering and icons
- Collapse/expand functionality
- User interactions (navigate, remove, clear)
- Event propagation handling

### Integration Tests (21 tests)

**Book Builder Workflow** (12 tests)
- Book creation and error handling
- Section management (create, update, delete)
- Content card management
- Full workflow testing
- Book navigation
- Error handling (network, 404, validation)

**Navigation + Interest List** (9 tests)
- Interest list navigation flow
- Tab/interest list coordination
- Complex navigation scenarios
- Circular navigation
- Order preservation

### E2E Tests (Playwright)

**User Journeys**
- Application loading
- Navigation between views
- Interest list workflows
- Book builder workflows
- Image browser workflows
- Conversation browser workflows

**Pane Persistence**
- Layout persistence across reloads
- Preferences persistence
- Pane size persistence
- Corrupted localStorage handling
- Tab persistence
- Responsive layout testing

## Writing Tests

### Unit Test Example

```jsx
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { WorkspaceProvider, useWorkspace } from '../../contexts/WorkspaceContext';

describe('MyComponent', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should do something', () => {
    const { result } = renderHook(() => useWorkspace(), {
      wrapper: WorkspaceProvider,
    });

    act(() => {
      result.current.addTab('conversation', 'Test', { id: 1 });
    });

    expect(result.current.tabs).toHaveLength(1);
  });
});
```

### Component Test Example

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { WorkspaceProvider } from '../../contexts/WorkspaceContext';
import MyComponent from '../../components/MyComponent';

it('should render and interact', () => {
  render(
    <WorkspaceProvider>
      <MyComponent />
    </WorkspaceProvider>
  );

  const button = screen.getByRole('button', { name: 'Click me' });
  fireEvent.click(button);

  expect(screen.getByText('Clicked!')).toBeInTheDocument();
});
```

### Integration Test Example

```jsx
import { renderHook, act } from '@testing-library/react';
import { WorkspaceProvider, useWorkspace } from '../../contexts/WorkspaceContext';

it('should support full workflow', () => {
  const { result } = renderHook(() => useWorkspace(), {
    wrapper: WorkspaceProvider,
  });

  // 1. Add item to interest list
  act(() => {
    result.current.addToInterest({ type: 'image', id: 1, title: 'Image' });
  });

  // 2. Navigate to item
  act(() => {
    result.current.navigateToInterest(result.current.interestList[0]);
  });

  // 3. Verify state
  expect(result.current.tabs).toHaveLength(1);
  expect(result.current.currentTab?.type).toBe('image');
});
```

### E2E Test Example

```js
import { test, expect } from '@playwright/test';

test('should complete user journey', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Navigate to feature
  await page.getByText('Books').click();

  // Interact with UI
  await page.getByRole('button', { name: 'New Book' }).click();
  await page.fill('input[name="title"]', 'My Book');
  await page.click('button[type="submit"]');

  // Verify result
  await expect(page.getByText('My Book')).toBeVisible();
});
```

## Testing Best Practices

### 1. Test Isolation

- Clear localStorage before each test
- Use `beforeEach` for setup
- Don't rely on test execution order
- Mock external dependencies (axios, etc.)

### 2. Test What Users See

- Use `screen.getByRole`, `screen.getByText` instead of implementation details
- Test user interactions, not implementation
- Focus on behavior, not internal state

### 3. Arrange-Act-Assert Pattern

```js
it('should do something', () => {
  // Arrange - set up test data
  const { result } = renderHook(() => useWorkspace(), { wrapper: WorkspaceProvider });

  // Act - perform action
  act(() => {
    result.current.addTab('conversation', 'Test', { id: 1 });
  });

  // Assert - verify result
  expect(result.current.tabs).toHaveLength(1);
});
```

### 4. Descriptive Test Names

```js
// ✅ Good
it('should navigate to next tab when navigateToNextTab is called')

// ❌ Bad
it('test navigation')
```

### 5. Test Edge Cases

- Empty states
- Error conditions
- Boundary values
- Race conditions
- Null/undefined values

### 6. Use Test Utilities

The project provides helpful utilities in `src/test/utils.jsx`:

```jsx
import { renderWithWorkspace, mockData, createMockAxios } from '../test/utils';

// Render with workspace context
renderWithWorkspace(<MyComponent />);

// Generate mock data
const book = mockData.book({ title: 'Custom Title' });
const section = mockData.section({ book_id: book.id });

// Mock axios
const mockAxios = createMockAxios();
mockAxios.get.mockResolvedValue({ data: [] });
```

## Mocking

### Mocking Modules

```js
import { vi } from 'vitest';

vi.mock('axios');
vi.mock('react-resizable-panels', () => ({
  Panel: ({ children }) => <div>{children}</div>,
  PanelGroup: ({ children }) => <div>{children}</div>,
  PanelResizeHandle: () => <div />,
}));
```

### Mocking Functions

```js
const mockFn = vi.fn();
mockFn.mockReturnValue('value');
mockFn.mockResolvedValue({ data: [] });
mockFn.mockRejectedValue(new Error('Failed'));
```

### Mocking localStorage

```js
import { createMockLocalStorage } from '../test/utils';

const mockStorage = createMockLocalStorage();
global.localStorage = mockStorage;
```

## Debugging Tests

### Run Single Test File

```bash
npm test -- WorkspaceContext.test.jsx
```

### Run Single Test

```bash
npm test -- -t "should add a new tab"
```

### Use Vitest UI

```bash
npm run test:ui
```

### Use Playwright UI

```bash
npm run test:e2e:ui
```

### Debug with console.log

```js
import { screen } from '@testing-library/react';

// Print DOM structure
screen.debug();

// Print specific element
screen.debug(screen.getByRole('button'));
```

## Continuous Integration

Tests run automatically on:
- Pre-commit hooks (unit tests only)
- Pull requests (all tests)
- Main branch commits (all tests + coverage)

## Coverage Goals

Current coverage: **81 tests across all layers**

Goals:
- Unit test coverage: >80%
- Integration test coverage: >70%
- E2E coverage: Critical user paths

## Common Issues

### Issue: Test fails with "localStorage is not defined"

**Solution:** Clear localStorage in `beforeEach`:

```js
beforeEach(() => {
  localStorage.clear();
});
```

### Issue: React state update warnings

**Solution:** Wrap state updates in `act()`:

```js
import { act } from '@testing-library/react';

act(() => {
  result.current.someFunction();
});
```

### Issue: Async tests timing out

**Solution:** Use `waitFor` or increase timeout:

```js
import { waitFor } from '@testing-library/react';

await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
}, { timeout: 5000 });
```

### Issue: E2E tests can't find backend

**Solution:** Ensure backend is running on port 8000 before E2E tests:

```bash
# Terminal 1
cd backend && python main.py

# Terminal 2
npm run test:e2e
```

## Future Improvements

- [ ] Add visual regression testing (Percy/Chromatic)
- [ ] Add accessibility testing (axe-core)
- [ ] Add performance testing (Lighthouse CI)
- [ ] Increase coverage to 90%+
- [ ] Add mutation testing
- [ ] Add API contract testing

## Resources

- [Vitest Documentation](https://vitest.dev)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

**Last Updated:** October 6, 2025
**Test Count:** 81 tests (60 unit, 21 integration, E2E comprehensive)
**Status:** ✅ All tests passing
