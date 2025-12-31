import { render } from '@testing-library/react';
import App from './App';

test('renders Crypto Calculators Landing without crashing', () => {
  render(<App />);
  // App renders successfully
});
