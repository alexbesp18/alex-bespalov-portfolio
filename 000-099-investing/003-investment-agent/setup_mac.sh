#!/bin/bash

echo "🚀 Setting up Investment Analysis Agent for Mac..."
echo ""

# Create folders
echo "📁 Creating folders..."
mkdir -p input
mkdir -p output

echo "✅ Folders created:"
echo "   - input/  (place your transcript files here)"
echo "   - output/ (analysis results will be saved here)"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Please copy .env.example to .env and add your API keys:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your API keys"
    echo ""
else
    echo "✅ .env file found"
    echo ""
fi

# Create example transcript
echo "📝 Creating example transcript..."
cat > input/example_transcript.txt << 'EOF'
Investment Podcast Transcript - AI Infrastructure Boom
Episode Date: January 10, 2025

[00:02:15] Host: Welcome back. Today we're diving deep into the AI infrastructure boom. What are you seeing in the data center space?

[00:02:45] Guest: The growth is unprecedented. NVIDIA just reported Q4 earnings, and their data center revenue was up 217% year-over-year to $18.4 billion. They mentioned having a multi-quarter backlog worth over $11 billion for their new Blackwell chips. Jensen said on the call that "demand is exceeding supply by a significant margin."

[00:04:12] Host: That's incredible. What about the supporting infrastructure?

[00:04:30] Guest: That's where it gets really interesting. Vertiv Technologies just reported earnings, and they're seeing similar explosive growth. Their Americas revenue grew 28% YoY, and they raised full-year guidance citing strong AI-driven demand for thermal management and power distribution. The CEO specifically mentioned "AI workloads requiring 10x the power density of traditional servers."

[00:06:50] Host: Are you seeing this flow through to the cloud providers?

[00:07:15] Guest: Absolutely. Microsoft's Azure revenue grew 30% in their latest quarter, with the CEO saying "AI services are now contributing meaningfully to revenue" and that they're "capacity constrained on AI inference." They're planning to spend $50 billion on AI infrastructure this year.

[00:09:20] Guest: But here's what people are missing - the networking layer. Arista Networks just crushed earnings with 20% revenue growth to $1.81 billion. They're the picks and shovels for AI data centers, and they called out "AI-driven demand exceeding our most optimistic scenarios."

[00:11:45] Host: What about the semiconductor equipment manufacturers?

[00:12:10] Guest: Applied Materials reported strong numbers - their revenue was up 5% with semiconductor systems revenue growing 8%. But more importantly, they guided higher for next quarter, specifically calling out "AI-driven demand for advanced logic and memory."

[00:14:30] Host: Any opportunities in the power infrastructure space?

[00:14:55] Guest: Eaton Corporation is fascinating. They just reported 9% organic revenue growth, but their electrical Americas segment grew 17%. The CFO specifically mentioned "AI data center power distribution driving unprecedented demand" and they raised their full-year EPS guidance by 10%.

[00:16:40] Host: Let's talk about cybersecurity for a moment. With all this AI deployment...

[00:17:05] Guest: CrowdStrike had a phenomenal quarter. ARR grew 31% to $3.86 billion, and subscription revenue was up 34%. They mentioned "AI workload protection modules seeing 300% growth" and added more net new ARR than any quarter in their history.

[00:19:20] Guest: The theme I'm seeing across all these companies is the same - demand is outpacing supply, margins are expanding, and guidance keeps getting raised. This AI infrastructure build-out is a multi-year cycle.

[00:20:45] Host: Any final thoughts on positioning?

[00:21:00] Guest: Focus on companies with: 1) Recent earnings beats, 2) Raised guidance specifically mentioning AI, 3) Supply constraints indicating pricing power, and 4) Expanding margins. This isn't hype - the capex is real and flowing through to revenue.

[End of relevant excerpt]
EOF

echo "✅ Example transcript created: input/example_transcript.txt"
echo ""

echo "🎯 Next steps:"
echo "1. Copy .env.example to .env: cp .env.example .env"
echo "2. Edit .env and add your API keys"
echo "3. Install dependencies: pip install -r requirements.txt"
echo "   (or use: make install)"
echo "4. Run the agent: python -m src.main"
echo "   (or use: make run)"
echo ""
echo "📚 See README.md for detailed instructions"
