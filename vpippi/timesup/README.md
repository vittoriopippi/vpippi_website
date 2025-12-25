# Times Up! - Django Game App

A complete implementation of the Times Up! party game for Django, designed to be played on a single shared device.

## Overview

Times Up! is a guessing game where players try to identify famous people (real or fictional) over three rounds using the same deck of cards. Each round has different rules that make the game progressively more challenging and hilarious.

## Game Features

### Three Distinct Rounds

1. **Round 1: Open Description**
   - Speak freely using sentences
   - Cannot say any part of the name
   - No spelling, rhyming, or translating
   - 30 seconds per turn
   - Unlimited guesses
   - Cannot pass cards

2. **Round 2: One Word**
   - Only ONE word allowed per card
   - Can repeat the same word
   - Gestures allowed after saying the word
   - 30 seconds per turn
   - Only ONE guess allowed
   - Can pass cards

3. **Round 3: The Mime**
   - No speaking allowed
   - Pantomime and gestures only
   - Sound effects permitted
   - 30 seconds per turn
   - Only ONE guess allowed
   - Can pass cards

### Game Flow

1. **Setup**: Create teams (2+ teams, 2+ players each) and add 40 cards with famous people
2. **Lobby**: Review teams and select which round to start
3. **Play**: Teams take turns, with the active team trying to guess as many cards as possible in 30 seconds
4. **Scoring**: 1 point per correctly guessed card
5. **Round Complete**: View scores after each round
6. **Final Scores**: See winner after Round 3

## Installation

The app is already set up in your Django project. To access it:

1. Navigate to `/timesup/` in your browser
2. Create a new game or join an existing one using a game code

## URLs

- `/timesup/` - Home page
- `/timesup/create/` - Create new game
- `/timesup/join/` - Join existing game
- `/timesup/<code>/setup/` - Setup teams and cards
- `/timesup/<code>/lobby/` - Game lobby
- `/timesup/<code>/play/` - Main gameplay
- `/timesup/<code>/round-complete/` - Round completion screen
- `/timesup/<code>/final-scores/` - Final scores

## Models

- **Game**: Main game instance with unique 6-character code
- **Team**: Teams competing in the game
- **Player**: Individual players on teams
- **Card**: Famous people cards used in the game
- **GameRound**: Records of which cards were guessed by which team

## Admin Interface

All models are registered in the Django admin for easy management:
- View all games and their status
- Manage teams, players, and cards
- Track scoring history

## How to Play (Single Device)

1. One player creates a game and shares the 6-character game code
2. All players gather around the device
3. Set up teams and add 40 famous people to the deck
4. Start with Round 1
5. Pass the device to the active team for their 30-second turn
6. After time runs out, pass to the next team
7. Continue until all cards are guessed
8. Move to the next round and repeat with the SAME cards
9. After Round 3, view final scores and declare the winner!

## Tips

- The same deck is used for all three rounds, so players memorize the cards
- Round 1 helps everyone learn the cards
- Round 2 becomes about remembering associations from Round 1
- Round 3 is pure memory and quick thinking

## Technical Details

- Built with Django 4.2+
- Uses session-based game state
- Real-time timer using JavaScript
- Responsive design for mobile and desktop
- No external dependencies beyond Django

## Future Enhancements

Possible improvements:
- Multiplayer support with WebSockets
- Custom card packs
- Game statistics and history
- Sound effects and animations
- Mobile app version
