/**
 * RetirementInflationCalculator component tests
 */

import { render, screen, fireEvent } from '@testing-library/react';
import RetirementInflationCalculator from '../RetirementInflationCalculator';

describe('RetirementInflationCalculator', () => {
  it('renders without crashing', () => {
    render(<RetirementInflationCalculator />);
    expect(screen.getByText(/retirement inflation calculator/i)).toBeInTheDocument();
  });

  it('displays initial investment value', () => {
    render(<RetirementInflationCalculator />);
    
    const initialInvestmentInput = screen.getByLabelText(/initial investment amount/i);
    expect(initialInvestmentInput).toHaveValue(50000);
  });

  it('displays expected return input with S&P 500 reference', () => {
    render(<RetirementInflationCalculator />);
    
    const expectedReturnInput = screen.getByLabelText(/expected annual return percentage/i);
    expect(expectedReturnInput).toHaveValue(9.6);
    expect(screen.getByText(/s&p 500 historical average/i)).toBeInTheDocument();
  });

  it('shows base case inflation by default', () => {
    render(<RetirementInflationCalculator />);
    
    const scenarioSelect = screen.getByLabelText(/select inflation scenario/i);
    expect(scenarioSelect).toHaveValue('base');
  });

  it('displays projected value for user inputs', () => {
    render(<RetirementInflationCalculator />);
    
    // Should show "Your Projected Outcome" section
    expect(screen.getByText(/your projected outcome/i)).toBeInTheDocument();
    // Multiple instances of "Projected Value" exist (in card and table header)
    expect(screen.getAllByText(/projected value/i).length).toBeGreaterThan(0);
  });

  it('displays key findings section', () => {
    render(<RetirementInflationCalculator />);
    
    expect(screen.getByText(/key findings/i)).toBeInTheDocument();
    expect(screen.getByText(/income needed at 50/i)).toBeInTheDocument();
    expect(screen.getByText(/total retirement funding/i)).toBeInTheDocument();
  });

  it('shows planning recommendations', () => {
    render(<RetirementInflationCalculator />);
    
    expect(screen.getByText(/planning recommendations/i)).toBeInTheDocument();
    expect(screen.getByText(/projected outcomes section/i)).toBeInTheDocument();
  });

  describe('Inflation Scenario Selection', () => {
    it('shows custom inflation input when custom scenario selected', () => {
      render(<RetirementInflationCalculator />);
      
      const scenarioSelect = screen.getByLabelText(/select inflation scenario/i);
      fireEvent.change(scenarioSelect, { target: { value: 'custom' } });
      
      expect(screen.getByLabelText(/custom inflation rate/i)).toBeInTheDocument();
    });

    it('hides custom inflation input for non-custom scenarios', () => {
      render(<RetirementInflationCalculator />);
      
      // By default, base case is selected
      expect(screen.queryByLabelText(/custom inflation rate/i)).not.toBeInTheDocument();
    });
  });

  describe('Input Validation', () => {
    it('allows changing current age', () => {
      render(<RetirementInflationCalculator />);
      
      const ageInput = screen.getByLabelText(/current age/i);
      fireEvent.change(ageInput, { target: { value: '35' } });
      
      expect(ageInput).toHaveValue(35);
    });

    it('allows changing annual contribution', () => {
      render(<RetirementInflationCalculator />);
      
      const contributionInput = screen.getByLabelText(/annual contribution until retirement/i);
      fireEvent.change(contributionInput, { target: { value: '10000' } });
      
      expect(contributionInput).toHaveValue(10000);
    });
  });

  describe('Tables', () => {
    it('renders future income requirements table', () => {
      render(<RetirementInflationCalculator />);
      
      expect(screen.getByText(/future income requirements/i)).toBeInTheDocument();
      // Use getAllByText since "best case" and "worst case" appear in multiple places
      expect(screen.getAllByText(/best case/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/worst case/i).length).toBeGreaterThan(0);
    });

    it('renders required returns table', () => {
      render(<RetirementInflationCalculator />);
      
      expect(screen.getByText(/required annual returns/i)).toBeInTheDocument();
      expect(screen.getAllByText(/lump sum only/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/with contributions/i).length).toBeGreaterThan(0);
    });

    it('renders projected outcomes table', () => {
      render(<RetirementInflationCalculator />);
      
      expect(screen.getByText(/projected outcomes analysis/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<RetirementInflationCalculator />);
      
      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toHaveTextContent(/retirement inflation calculator/i);
      
      const h2s = screen.getAllByRole('heading', { level: 2 });
      expect(h2s.length).toBeGreaterThan(0);
    });

    it('has labeled form inputs', () => {
      render(<RetirementInflationCalculator />);
      
      // All inputs should have associated labels
      expect(screen.getByLabelText(/current age/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/retirement age/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/life expectancy/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/desired annual income/i)).toBeInTheDocument();
    });
  });
});
