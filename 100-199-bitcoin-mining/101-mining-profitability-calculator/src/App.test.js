import { render } from '@testing-library/react';
import App from './App';

test('renders Bitcoin Mining Calculator without crashing', () => {
  render(<App />);
  // App renders successfully
});
