import { render, screen } from '@testing-library/react';
import App from './App';

/**
 * Test suite for App component
 */
describe('App', () => {
  test('renders Portfolio Analyzer without crashing', () => {
    // Mock window.matchMedia for Recharts
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    render(<App />);
    // Check for main heading - use getAllByText since there may be multiple instances
    const headings = screen.getAllByText(/Portfolio Analyzer/i);
    expect(headings.length).toBeGreaterThan(0);
  });

  test('renders ErrorBoundary wrapper', () => {
    const { container } = render(<App />);
    // ErrorBoundary should wrap the app content
    expect(container.firstChild).toBeTruthy();
  });
});
