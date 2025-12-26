import { render } from '@testing-library/react';
import App from './App';

test('renders Miner Price Tracker without crashing', () => {
  render(<App />);
  // App renders successfully
});
