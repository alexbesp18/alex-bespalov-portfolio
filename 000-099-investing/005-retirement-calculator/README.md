# Retirement Inflation Calculator

A sophisticated React application that helps you plan for retirement by modeling how inflation erodes purchasing power over time, calculating required investment returns, and showing whether your savings strategy will meet your goals.

## Key Features

- **Multi-Scenario Inflation Modeling** - Compare best case (1.8%), base case (2.7%), and worst case (4.5%) inflation scenarios side-by-side
- **Required Return Calculator** - Uses Newton's method to calculate the exact annual return needed to meet retirement goals
- **Contribution Impact Analysis** - See how annual contributions reduce required returns and close funding gaps
- **Dynamic Projections** - Real-time updates as you adjust age, income needs, investment amounts, and expected returns
- **Gap Analysis** - Identifies shortfalls and calculates additional annual savings needed to reach targets

## Quick Start

### Prerequisites

- Node.js 18.0 or higher
- npm 9.0 or higher

### Installation

```bash
git clone https://github.com/alexbesp18/retirement-calculator.git
cd retirement-calculator
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the calculator.

### Production Build

```bash
npm run build
```

## How It Works

### Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Current Age | Your age today | 29 |
| Retirement Age | When you plan to retire | 50 |
| Life Expectancy | Planning horizon end | 90 |
| Desired Annual Income | Income needed in today's dollars | $100,000 |
| Initial Investment | Lump sum available now | $50,000 |
| Annual Contribution | Yearly savings until retirement | $0 |
| Expected Return | Anticipated annual investment return | 9.6% (S&P 500 avg) |

### Calculations

The calculator performs several sophisticated financial calculations:

1. **Future Value with Inflation**
   ```
   FV = PV × (1 + inflation_rate)^years
   ```

2. **Total Retirement Funding**
   - Sums inflation-adjusted income needs for each year of retirement

3. **Required Return (Newton's Method)**
   - For lump sum + contributions scenarios, uses iterative Newton-Raphson method to solve for the internal rate of return

4. **Additional Contribution Needed**
   - Calculates the gap between projected portfolio value and target, then determines required additional annual savings

## Project Structure

```
retirement-calculator/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   └── RetirementInflationCalculator.js  # Main calculator component
│   ├── config/
│   │   └── constants.js    # Configuration and defaults
│   ├── utils/
│   │   ├── calculations.js # Financial calculation functions
│   │   └── formatters.js   # Currency/percentage formatting
│   ├── App.js              # Root component
│   ├── App.css             # Global styles
│   └── index.js            # Entry point
├── package.json
└── README.md
```

## Technical Notes

### Newton's Method Implementation

For scenarios with annual contributions, there's no closed-form solution for the required return rate. The calculator uses Newton-Raphson iteration:

```javascript
// Find rate r where:
// FV = P(1+r)^n + C[(1+r)^n - 1]/r = Target
// Iterate: r_new = r - f(r)/f'(r)
```

The algorithm converges within 100 iterations with 0.0001 tolerance.

### Performance Considerations

- All calculations run client-side with no API calls
- React's useEffect recalculates on input changes
- Tables are rendered dynamically based on user's initial investment amount

### Inflation Rate Sources

| Scenario | Rate | Basis |
|----------|------|-------|
| Best Case | 1.8% | Historical low periods |
| Base Case | 2.7% | 20-year average |
| Worst Case | 4.5% | High inflation periods |

## Testing

```bash
npm test
```

## Tech Stack

- **React 19** - UI framework with hooks
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library
- **Create React App** - Build tooling

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built for retirement planning and financial education purposes. Not financial advice.
