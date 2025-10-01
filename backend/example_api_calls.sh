#!/bin/bash

# Example API calls for Manifestation Protocol Agent
# Make sure the backend is running on port 8000

echo "=========================================="
echo "Manifestation Protocol API Examples"
echo "=========================================="
echo ""

# 1. Generate a career manifestation protocol
echo "1. Generating career manifestation protocol..."
curl -X POST http://localhost:8000/api/protocols/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-001",
    "goal": "Land a $150k+ software engineering role at a FAANG company within 90 days",
    "timeframe": "90_days",
    "commitment_level": "intensive"
  }' | jq '.' > career_protocol_response.json

echo "Saved to: career_protocol_response.json"
echo ""

# Extract protocol ID for next calls
PROTOCOL_ID=$(cat career_protocol_response.json | jq -r '.id')
echo "Protocol ID: $PROTOCOL_ID"
echo ""

# 2. Generate a relationship protocol
echo "2. Generating relationship manifestation protocol..."
curl -X POST http://localhost:8000/api/protocols/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-002",
    "goal": "Attract a loving, committed relationship with someone who shares my values and supports my growth",
    "timeframe": "30_days",
    "commitment_level": "moderate"
  }' | jq '.'
echo ""

# 3. Generate a financial freedom protocol
echo "3. Generating financial freedom protocol..."
curl -X POST http://localhost:8000/api/protocols/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-003",
    "goal": "Build a passive income stream generating $5,000/month through online business",
    "timeframe": "90_days",
    "commitment_level": "intensive"
  }' | jq '.'
echo ""

# 4. Get protocol by ID
echo "4. Retrieving protocol by ID..."
curl -X GET http://localhost:8000/api/protocols/$PROTOCOL_ID | jq '.'
echo ""

# 5. Get all protocols for a user
echo "5. Getting all protocols for user demo-user-001..."
curl -X GET http://localhost:8000/api/protocols/user/demo-user-001 | jq '.'
echo ""

# 6. Log a checkpoint completion
echo "6. Logging Day 3 checkpoint completion..."
curl -X POST http://localhost:8000/api/protocols/$PROTOCOL_ID/checkpoint \
  -H "Content-Type: application/json" \
  -d '{
    "day": 3,
    "completed": true,
    "notes": "Feeling great momentum! Completed all daily practices and noticed increased clarity about my goals.",
    "reflections": [
      "I am more confident in my ability to achieve this goal",
      "The morning visualization is becoming easier and more vivid",
      "I caught myself naturally using affirmations throughout the day"
    ],
    "challenges": [
      "Hard to maintain evening routine when tired"
    ],
    "wins": [
      "Did all practices for 3 days straight",
      "Had a synchronicity - met someone who works at target company"
    ]
  }' | jq '.'
echo ""

echo "=========================================="
echo "Examples complete!"
echo "=========================================="
