/**
 * Hashrate Widget Component
 * Displays network difficulty trend information
 */

import React from 'react';
import PropTypes from 'prop-types';
import { Zap } from 'lucide-react';
import { calculateMonthlyGrowth, getCalculatedEndValues } from '../utils/calculations';
import { ParamsShape } from '../types';

const HashrateWidget = ({ params }) => {
  const { networkHashrateEnd } = getCalculatedEndValues(params);
  const monthlyGrowth = calculateMonthlyGrowth(params.networkHashrateStart, networkHashrateEnd);
  
  return (
    <div className="bg-yellow-50 rounded-lg p-4 mb-6">
      <h3 className="font-semibold mb-2 flex items-center gap-2">
        <Zap className="w-4 h-4" />
        Network Difficulty Trend
      </h3>
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-600">Current:</span>
          <span className="font-bold block">{params.networkHashrateStart} EH/s</span>
        </div>
        <div>
          <span className="text-gray-600">Monthly Growth:</span>
          <span className="font-bold block">{monthlyGrowth.toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-gray-600">Year End Est:</span>
          <span className="font-bold block">{networkHashrateEnd.toFixed(0)} EH/s</span>
        </div>
      </div>
    </div>
  );
};

HashrateWidget.propTypes = {
  params: ParamsShape.isRequired
};

export default HashrateWidget;
