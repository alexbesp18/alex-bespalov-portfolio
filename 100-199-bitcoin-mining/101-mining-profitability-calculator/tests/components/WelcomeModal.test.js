/**
 * Tests for WelcomeModal component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import WelcomeModal from '../../src/components/WelcomeModal';

describe('WelcomeModal', () => {
  it('should not render when show is false', () => {
    render(<WelcomeModal show={false} onClose={jest.fn()} />);
    expect(screen.queryByText('Welcome to Bitcoin Mining Calculator!')).not.toBeInTheDocument();
  });

  it('should render when show is true', () => {
    render(<WelcomeModal show={true} onClose={jest.fn()} />);
    expect(screen.getByText('Welcome to Bitcoin Mining Calculator!')).toBeInTheDocument();
  });

  it('should call onClose when Get Started is clicked', () => {
    const onClose = jest.fn();
    render(<WelcomeModal show={true} onClose={onClose} />);
    
    const button = screen.getByText('Get Started');
    fireEvent.click(button);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('should display all feature points', () => {
    render(<WelcomeModal show={true} onClose={jest.fn()} />);
    
    expect(screen.getByText(/Compare 20\+ popular Bitcoin miners/)).toBeInTheDocument();
    expect(screen.getByText(/Adjust electricity rates for your location/)).toBeInTheDocument();
    expect(screen.getByText(/See 2-year projections with tax calculations/)).toBeInTheDocument();
    expect(screen.getByText(/Save and compare different scenarios/)).toBeInTheDocument();
  });
});
