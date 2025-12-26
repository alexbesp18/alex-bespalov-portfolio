/**
 * Welcome Modal Component
 * Shows welcome message on first visit
 */

import React from 'react';
import PropTypes from 'prop-types';
import { STORAGE_KEYS } from '../utils/constants';

const WelcomeModal = ({ show, onClose }) => {
  if (!show) return null;

  const handleGetStarted = () => {
    localStorage.setItem(STORAGE_KEYS.HAS_VISITED, 'true');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 max-w-md shadow-2xl">
        <h2 className="text-2xl font-bold mb-4">Welcome to Bitcoin Mining Calculator!</h2>
        <ul className="space-y-2 mb-6 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-1">✓</span>
            <span>Compare 20+ popular Bitcoin miners</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-1">✓</span>
            <span>Adjust electricity rates for your location</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-1">✓</span>
            <span>See 2-year projections with tax calculations</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-1">✓</span>
            <span>Save and compare different scenarios</span>
          </li>
        </ul>
        <button 
          onClick={handleGetStarted}
          className="w-full bg-orange-600 text-white py-3 rounded-lg hover:bg-orange-700 transition-colors font-semibold"
        >
          Get Started
        </button>
      </div>
    </div>
  );
};

WelcomeModal.propTypes = {
  show: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired
};

export default WelcomeModal;
