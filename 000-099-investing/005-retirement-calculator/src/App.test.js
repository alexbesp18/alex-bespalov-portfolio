/**
 * App component tests
 */

import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the retirement calculator', () => {
    render(<App />);
    
    // Check that the main heading is present
    const headingElement = screen.getByRole('heading', { 
      name: /retirement inflation calculator/i 
    });
    expect(headingElement).toBeInTheDocument();
  });

  it('renders all main sections', () => {
    render(<App />);
    
    // Check for key sections
    expect(screen.getByText(/your information/i)).toBeInTheDocument();
    expect(screen.getByText(/projected outcomes analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/key findings/i)).toBeInTheDocument();
    expect(screen.getByText(/future income requirements/i)).toBeInTheDocument();
    expect(screen.getByText(/required annual returns/i)).toBeInTheDocument();
    expect(screen.getByText(/planning recommendations/i)).toBeInTheDocument();
  });

  it('renders input fields with default values', () => {
    render(<App />);
    
    // Check for current age input
    const currentAgeInput = screen.getByLabelText(/current age/i);
    expect(currentAgeInput).toBeInTheDocument();
    expect(currentAgeInput).toHaveValue(29);
    
    // Check for retirement age input
    const retirementAgeInput = screen.getByLabelText(/retirement age/i);
    expect(retirementAgeInput).toBeInTheDocument();
    expect(retirementAgeInput).toHaveValue(50);
  });

  it('renders inflation scenario dropdown', () => {
    render(<App />);
    
    const scenarioSelect = screen.getByLabelText(/select inflation scenario/i);
    expect(scenarioSelect).toBeInTheDocument();
  });
});
